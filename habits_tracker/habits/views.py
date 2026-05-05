from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models

from .models import User, Habit, HabitProgress, HabitCompletion
from .forms import UserRegistrationForm, HabitForm, HabitCompletionForm


def habit_list(request):
    """
    Главная страница со списком всех привычек
    """
    if request.user.is_authenticated:
        habits = Habit.objects.filter(
            models.Q(created_by=request.user) |  # свои привычки
            models.Q(created_by__role='admin')  # привычки админа
        ).order_by('-created_at')
    else:
        habits = Habit.objects.filter(created_by__role='admin').order_by('-created_at')

    context = {
        'habits': habits,
    }
    return render(request, 'habits/habit_list.html', context)


def register(request):
    """
    Регистрация нового пользователя
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Автоматически входим после регистрации
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('habits:habit_list')
    else:
        form = UserRegistrationForm()

    return render(request, 'habits/register.html', {'form': form})


def user_login(request):
    """
    Вход пользователя
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Добро пожаловать!')
            return redirect('habits:habit_list')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')

    return render(request, 'habits/login.html')


def user_logout(request):
    """
    Выход пользователя
    """
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('habits:habit_list')


@login_required
def profile(request):
    """
    Профиль пользователя с его прогрессом
    """
    # Получаем все привычки, которые пользователь осваивает
    active_progress = HabitProgress.objects.filter(
        user=request.user,
        status='in_progress'
    ).select_related('habit')

    # Получаем освоенные привычки
    completed_progress = HabitProgress.objects.filter(
        user=request.user,
        status='completed'
    ).select_related('habit')

    # Получаем забытые привычки
    abandoned_progress = HabitProgress.objects.filter(
        user=request.user,
        status='abandoned'
    ).select_related('habit')

    context = {
        'active_progress': active_progress,
        'completed_progress': completed_progress,
        'abandoned_progress': abandoned_progress,
    }
    return render(request, 'habits/profile.html', context)


@login_required
def reactivate_habit(request, progress_id):
    progress = get_object_or_404(HabitProgress, id=progress_id, user=request.user)

    if progress.status == 'completed':
        progress.status = 'in_progress'
        progress.completed_date = None
        progress.save()
        messages.success(request, f'Привычка "{progress.habit.name}" возвращена в процесс освоения')
    else:
        messages.warning(request, 'Эта привычка не была освоена')

    return redirect('habits:profile')


@login_required
def complete_habit(request, progress_id):
    progress = get_object_or_404(HabitProgress, id=progress_id, user=request.user)

    if progress.status == 'in_progress':
        progress.status = 'completed'
        progress.completed_date = timezone.now()
        progress.save()
        messages.success(request, f'Поздравляем! Вы освоили привычку "{progress.habit.name}"')
    else:
        messages.warning(request, 'Эта привычка уже освоена или забыта')

    return redirect('habits:profile')

@login_required
def habit_create(request):
    """
    Добавление новой привычки (доступно только администраторам)
    """
    if request.method == 'POST':
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.created_by = request.user
            habit.save()
            messages.success(request, 'Привычка успешно добавлена!')
            return redirect('habits:habit_detail', habit_id=habit.id)
    else:
        form = HabitForm()

    return render(request, 'habits/habit_form.html', {'form': form, 'title': 'Добавить привычку'})


def habit_detail(request, habit_id):
    """
    Детальная страница привычки
    """
    if request.user.is_authenticated:
        habit = get_object_or_404(
            Habit,
            models.Q(created_by=request.user) | models.Q(created_by__role='admin'),
            id=habit_id
        )
    else:
        habit = get_object_or_404(Habit, created_by__role='admin', id=habit_id)

    # Проверяем, начал ли текущий пользователь осваивать эту привычку
    user_progress = None
    if request.user.is_authenticated:
        user_progress = HabitProgress.objects.filter(
            user=request.user,
            habit=habit
        ).first()

    context = {
        'habit': habit,
        'user_progress': user_progress,
    }
    return render(request, 'habits/habit_detail.html', context)


@login_required
def start_habit(request, habit_id):
    """
    Начать освоение привычки
    """
    habit = get_object_or_404(Habit, id=habit_id)

    # Проверяем, не начал ли пользователь уже эту привычку
    existing_progress = HabitProgress.objects.filter(
        user=request.user,
        habit=habit
    ).first()

    if existing_progress:
        messages.warning(request, 'Вы уже начали осваивать эту привычку')
    else:
        progress = HabitProgress.objects.create(
            user=request.user,
            habit=habit,
            status='in_progress'
        )
        messages.success(request, f'Вы начали осваивать привычку "{habit.name}"')

    return redirect('habits:habit_detail', habit_id=habit.id)


@login_required
def mark_completion(request, progress_id):
    """
    Отметить выполнение привычки
    """
    from datetime import timedelta

    progress = get_object_or_404(HabitProgress, id=progress_id, user=request.user)

    if request.method == 'POST':
        form = HabitCompletionForm(request.POST)
        if form.is_valid():
            completion_date = form.cleaned_data['completion_date']
            status = form.cleaned_data['status']
            note = form.cleaned_data['note']

            # Проверка, разрешен ли день недели
            if not progress.habit.is_allowed_day(completion_date):
                messages.error(request,
                               f'Эта привычка выполняется только в определенные дни недели. {completion_date} не подходит.')
                return redirect('habits:profile')

            # Определяем текущий период
            if progress.habit.frequency == 'daily':
                period_start = completion_date
                period_end = completion_date
            elif progress.habit.frequency == 'weekly':
                period_start = completion_date - timedelta(days=completion_date.weekday())
                period_end = period_start + timedelta(days=6)
            else:  # monthly
                period_start = completion_date.replace(day=1)
                if period_start.month == 12:
                    next_month = period_start.replace(year=period_start.year + 1, month=1)
                else:
                    next_month = period_start.replace(month=period_start.month + 1)
                period_end = next_month - timedelta(days=1)

            # Проверяем, достигнут ли лимит за текущий период
            completed_count = HabitCompletion.objects.filter(
                habit_progress=progress,
                completion_date__range=[period_start, period_end],
                status=True
            ).count()

            if completed_count >= progress.habit.target_count:
                messages.warning(
                    request,
                    f'Вы уже выполнили лимит ({progress.habit.target_count} раз) за этот период. Следующий период начнется {period_end + timedelta(days=1)}.'
                )
                return redirect('habits:profile')

            # Создаём отметку
            completion = HabitCompletion.objects.create(
                habit_progress=progress,
                completion_date=completion_date,
                status=status,
                note=note
            )

            # Обновляем серию (по отметкам)
            progress.update_streak(status)

            # Проверяем предыдущий период и сбрасываем серию, если нужно
            progress.check_and_update_streak_for_previous_period(completion_date)

            # Проверяем, достигнут ли теперь лимит за текущий период
            new_completed_count = HabitCompletion.objects.filter(
                habit_progress=progress,
                completion_date__range=[period_start, period_end],
                status=True
            ).count()

            if new_completed_count >= progress.habit.target_count:
                # Лимит достигнут - обновляем периодическую серию
                progress.update_period_streak(completion_date)
                messages.success(request,
                                 f'Отлично! Вы выполнили норму ({progress.habit.target_count} раз) за этот период!')

            messages.success(request, f'Отметка за {completion_date} сохранена!')

            return redirect('habits:profile')
    else:
        # По умолчанию предлагаем сегодняшнюю дату
        form = HabitCompletionForm(initial={'completion_date': timezone.now().date()})

    return render(request, 'habits/mark_completion.html', {
        'progress': progress,
        'form': form,
    })