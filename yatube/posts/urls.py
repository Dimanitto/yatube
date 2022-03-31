# posts/urls.py
from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    # Главная страница
    path('', views.index, name='index'),
    # Страница группы
    path('group/<slug:slug>/', views.group_posts, name='group_posts'),
    # Профайл пользователя
    path('profile/<str:username>/', views.profile, name='profile'),
    # Просмотр записи
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    # Страница для публикации постов
    path('create/', views.post_create, name='post_create'),
    # Страница для редактирования постов
    path('posts/<int:post_id>/edit/', views.post_edit, name='post_edit'),
    # Добавление комментария
    path(
        'posts/<int:post_id>/comment/',
        views.add_comment,
        name='add_comment'),
    # Вывод постов автора на которого подписан юзер
    path('follow/', views.follow_index, name='follow_index'),
    # Подписаться на автора
    path(
        'profile/<str:username>/follow/',
        views.profile_follow,
        name='profile_follow'
    ),
    # Отписаться от автора
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    ),
]
