from django.urls import path
from . import views

app_name = 'habits'

urlpatterns = [
    #список привычек
    path('', views.habit_list, name='habit_list'),

    #Регистрация
    path('register/', views.register, name='register'),

    #Вход и выход
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    #Профиль пользователя
    path('profile/', views.profile, name='profile'),

    #Добавление привычки
    path('habit/create/', views.habit_create, name='habit_create'),

    #Детальная страница привычки
    path('habit/<int:habit_id>/', views.habit_detail, name='habit_detail'),

    #Начать освоение привычки
    path('habit/<int:habit_id>/start/', views.start_habit, name='start_habit'),

    #Отметить выполнение
    path('progress/<int:progress_id>/complete/', views.mark_completion, name='mark_completion'),
]