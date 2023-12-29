function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();

            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function handleLike(item, type) {
    const [counter, button] = item.children;

    button.addEventListener('click', () => {
        const formData = new FormData();
        formData.append(`${type}_id`, button.dataset.id);

        const request = new Request('/like/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        fetch(request)
            .then((response) => response.json())
            .then((data) => {
                counter.innerHTML = data.count;
                if (data.count > 0) {
                    counter.classList.add('text-success');
                    counter.classList.remove('text-danger');
                } else {
                    counter.classList.remove('text-success', 'text-danger');
                }
            });
    });
}

const question_items = document.getElementsByClassName('question-like-section');
for (let item of question_items) {
    handleLike(item, 'question');
}

const comment_items = document.getElementsByClassName('comment-like-section');
for (let item of comment_items) {
    handleLike(item, 'comment');
}

const comment_checkboxes = document.getElementsByClassName('checkbox-section');
for (let i = 0; i < comment_checkboxes.length; i++) {
    const [checkbox] = comment_checkboxes[i].children;
    const formData = new FormData();
    formData.append('comment_id', checkbox.dataset.id);

    const request = new Request('/check_author/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    });

    fetch(request)
        .then((response) => response.json())
        .then((data) => {
            checkbox.disabled = data.author !== data.user;
        })

    checkbox.addEventListener('click', (event) => {
        const formData = new FormData();
        formData.append(`comment_id`, checkbox.dataset.id);

        const request = new Request('/toggle_correct/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        fetch(request)
            .then((response) => response.json())
            .then((data) => {
                const comment = document.getElementsByClassName('comment');
                if (data.is_correct) {
                    comment[i].classList.add('bold');
                } else {
                    comment[i].classList.remove('bold');
                }
            });
    });
}


$(document).ready(function () {
    $('#comments-section').on('click', '.comment-like-btn', function () {
        var commentId = $(this).data('id');
        var $comment = $(this).closest('.comment');

        $.ajax({
            type: 'POST',
            url: '/like/',
            data: {
                comment_id: commentId,
                csrfmiddlewaretoken: getCookie('csrftoken')
            },
            success: function (response) {
                var likeCount = response.count;
                $comment.find('.comment-like-section .mx-1').text(likeCount);
            },
            error: function (error) {
                console.log('Like error:', error);
            }
        });
    });

    $('#comments-section').on('change', '.comment-correct-checkbox', function () {
        var commentId = $(this).data('id');
        var $comment = $(this).closest('.comment');

        $.ajax({
            type: 'POST',
            url: '/toggle_correct/',
            data: {
                comment_id: commentId,
                csrfmiddlewaretoken: getCookie('csrftoken')
            },
            success: function (response) {
                var isCorrect = response.is_correct;
                if (isCorrect) {
                    $comment.addClass('bold');
                } else {
                    $comment.removeClass('bold');
                }
            },
            error: function (error) {
                console.log('Toggle correct error:', error);
            }
        });
    });


    $('#comment-form').submit(function (event) {
        event.preventDefault();

        var url = $(this).data('url');

        $.ajax({
            type: 'POST',
            url: url,
            data: $(this).serialize() + '&csrfmiddlewaretoken=' + getCookie('csrftoken'),
            success: function (response) {
                $('#comments-section').append(response.html);
                $('#comment-form')[0].reset();
            },
            error: function (error) {
                console.log(error);
            }
        });
    });
});