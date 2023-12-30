import json

import jwt
import time
from cent import Client
from django.contrib import auth
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse, JsonResponse
from django.core.paginator import (Paginator, EmptyPage, PageNotAnInteger)
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.conf import settings as conf_settings

from askme_app.forms import LoginForm, RegisterForm, SettingsForm, AskForm, CommentForm
from askme_app.models import Question, Tag, Comment, Profile, QuestionLike, CommentLike

TOP_TAGS = Tag.manager.top_of_tags(10)
TOP_USERS = Profile.manager.get_top_users(10)

client = Client(conf_settings.CENTRIFUGO_API_URL, api_key=conf_settings.CENTRIFUGO_API_KEY, timeout=1)


def get_centrifugo_data(user_id, channel):
    return {
        'centrifugo': {
            'token': jwt.encode({"sub": str(user_id), "exp": int(time.time()) + 10 * 60},
                                conf_settings.CENTRIFUGO_TOKEN_HMAC_SECRET_KEY, algorithm="HS256"),
            'ws_url': conf_settings.CENTRIFUGO_WS_URL,
            "channel": channel
        }
    }


def paginate(objects, request, per_page=20):
    page = request.GET.get('page', 1)
    paginator = Paginator(objects, per_page)
    default_page = 1
    try:
        items_page = paginator.page(page)
    except PageNotAnInteger:
        items_page = paginator.page(default_page)
    except EmptyPage:
        items_page = paginator.page(paginator.num_pages)
    return items_page


def index(request):
    questions = Question.manager.get_new_questions()
    items_page = paginate(questions, request, 20)
    return render(request, 'index.html',
                  {'questions': items_page, 'pages': items_page, 'tags': TOP_TAGS, 'users': TOP_USERS})


def question(request, question_id):
    item = get_object_or_404(Question, pk=question_id)
    comments = Comment.manager.get_comments_ordered_by_likes(question_id)
    items_page = paginate(comments, request, 30)
    if request.method == 'GET':
        comment_form = CommentForm()
    if request.method == 'POST':
        content = request.POST.get('content')
        profile = Profile.manager.get_profile_by_id(request.user.id)
        question = Question.manager.get_question_by_id(question_id)
        comment_form = CommentForm(request.POST, question=question, author=profile, initial={'content': content})
        if comment_form.is_valid():
            new_comment = comment_form.save()
            if new_comment:
                return redirect('question', question_id=question_id)
    return render(request, 'question.html', {'question': item, 'comments': items_page,
                                             'pages': items_page, 'question_id': question_id, 'tags': TOP_TAGS,
                                             'users': TOP_USERS, 'comment_form': comment_form,
                                             **get_centrifugo_data(request.user.id, f'question.{question_id}')})


@login_required(login_url='/login/', redirect_field_name='continue')
def ask(request):
    if request.method == "GET":
        ask_form = AskForm()
    if request.method == "POST":
        title, content, tags = request.POST['title'], request.POST['content'], request.POST['tags']
        profile = Profile.manager.get_profile_by_id(request.user.id)
        ask_form = AskForm(request.POST, author=profile, initial={"title": title, "content": content, "tags": tags})
        if ask_form.is_valid():
            new_question = ask_form.save()
            if new_question:
                return redirect('question', question_id=new_question.id)
    return render(request, 'ask.html', {'tags': TOP_TAGS, 'users': TOP_USERS, 'ask_form': ask_form,
                                        'all_tags': Tag.manager.get_all_tag_names()})


def signup(request):
    if request.method == "GET":
        user_form = RegisterForm()
    if request.method == "POST":
        user_form = RegisterForm(request.POST, request.FILES)
        if user_form.is_valid():
            user = user_form.save()
            new_user = authenticate(request, username=user_form.cleaned_data['username'],
                                    password=user_form.cleaned_data['password'])
            if user:
                login(request, new_user)
                return redirect(reverse('index'))
            else:
                user_form.add_error(None, "User saving error!")
    return render(request, 'signup.html', {'tags': TOP_TAGS, 'users': TOP_USERS, 'user_form': user_form})


def log_in(request):
    if request.method == 'GET':
        login_form = LoginForm()
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user = authenticate(request, **login_form.cleaned_data)
            if user is not None:
                login(request, user)
                return redirect(request.GET.get('continue', 'index'))
    return render(request, 'login.html', {'tags': TOP_TAGS, 'users': TOP_USERS, 'login_form': login_form})


def log_out(request):
    auth.logout(request)
    return redirect(reverse('login'))


def hot(request):
    items_page = paginate(Question.manager.get_top_questions(), request)
    return render(request, 'hot.html',
                  {'questions': items_page, 'pages': items_page, 'tags': TOP_TAGS, 'users': TOP_USERS})


@login_required(login_url='/login/', redirect_field_name='continue')
def settings(request):
    if request.method == 'GET':
        settings_form = SettingsForm(initial=model_to_dict(request.user), request=request)
    elif request.method == 'POST':
        settings_form = SettingsForm(request.POST, request.FILES, instance=request.user, request=request)
        if settings_form.is_valid():
            settings_form.save()
    else:
        settings_form = SettingsForm(request=request)
    return render(request, 'settings.html', {'tags': TOP_TAGS, 'users': TOP_USERS, 'settings_form': settings_form})


def tag(request, tag_name):
    tag_item = Tag.manager.get_questions_by_tag(tag_name)
    items_page = paginate(tag_item.order_by('-create_date'), request)
    return render(request, 'tag.html',
                  {'tag': tag_name, 'questions': items_page, 'pages': items_page, 'tags': TOP_TAGS, 'users': TOP_USERS})


@login_required(login_url='/login/', redirect_field_name='continue')
@csrf_protect
def like(request):
    if request.POST.get('question_id') is not None:
        id = request.POST.get('question_id')
        question = get_object_or_404(Question, pk=id)
        QuestionLike.manager.toggle_like(user=request.user.profile, question=question)
        count = question.get_likes_count()
    if request.POST.get('comment_id') is not None:
        id = request.POST.get('comment_id')
        comment = get_object_or_404(Comment, pk=id)
        CommentLike.manager.toggle_like(user=request.user.profile, comment=comment)
        count = comment.get_likes_count()

    return JsonResponse({'count': count})


@login_required(login_url='/login/', redirect_field_name='continue')
@csrf_protect
def toggle_correct(request):
    id = request.POST.get('comment_id')
    comment = get_object_or_404(Comment, pk=id)
    comment.is_correct = not comment.is_correct
    correct = comment.is_correct
    comment.save()
    return JsonResponse({'is_correct': correct})


@csrf_protect
def check_author(request):
    id = request.POST.get('comment_id')
    comment = get_object_or_404(Comment, pk=id)
    if request.user.id is not None:
        return JsonResponse({'user': request.user.id, 'author': comment.get_question_author_id()})
    return JsonResponse({'user': -1, 'author': comment.get_question_author_id()})


@login_required(login_url='/login/', redirect_field_name='continue')
@csrf_protect
def create_comment(request, question_id):
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            profile = Profile.manager.get_profile_by_id(request.user.id)
            question = Question.manager.get_question_by_id(question_id)

            comment_form = CommentForm(
                data=request.POST,
                question=question,
                author=profile,
            )

            if comment_form.is_valid():
                new_comment = comment_form.save()
                comment_data = {'html': render_to_string('components/comment-item.html', {'comment': new_comment})}
                channel_name = f'question.{question_id}'
                client.publish(channel_name, json.dumps(comment_data))

                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': 'Invalid form data'})
        else:
            return JsonResponse({'error': 'Invalid form data'})
    else:
        return JsonResponse({'error': 'Invalid request method'})
