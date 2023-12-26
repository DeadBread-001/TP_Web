"""
URL configuration for askme_makarov project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from askme_app import views
from django.conf import settings
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('hot', views.hot, name='hot'),
    path('settings/', views.settings, name='settings'),
    path('tag/<str:tag_name>', views.tag, name='tag'),
    path('question/<int:question_id>', views.question, name='question'),
    path('ask/', views.ask, name='ask'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.log_in, name='login'),
    path('logout/', views.log_out, name='logout'),
    path('like/', views.like, name='like'),
    path('toggle_correct/', views.toggle_correct, name='toggle_correct'),
    path('check_author/', views.check_author, name='check_author')
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)