from django.db import models
# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    # Расширенная модель пользователя.
    # AbstractUser и недостающие поля
    ROLE_CHOICES = (
        ('admin', 'Администратор'),
        ('user', 'Пользователь'),
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name='Роль'
    )
    date_registered = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата регистрации'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"


class Habit(models.Model):
    # Модель привычки
    # Частота выполнения
    FREQUENCY_CHOICES = (
        ('daily', 'Ежедневно'),
        ('weekly', 'Еженедельно'),
        ('monthly', 'Ежемесячно'),
    )

    weekdays = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Дни выполнения',
        help_text='Укажите дни: mon,tue,wed,thu,fri,sat,sun (через запятую)'
    )

    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    category = models.CharField(max_length=100, blank=True, verbose_name='Категория')
    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default='daily',
        verbose_name='Частота выполнения'
    )

    # Связь с пользователем
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='habits',
        verbose_name='Создатель'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def is_allowed_day(self, date):
        #проверяет, разрешено ли выполнение привычки в указанную дату
        if not self.weekdays:  #если дни не указаны, разрешено в любой день
            return True

        weekdays_map = {
            0: 'mon',  # понедельник
            1: 'tue',  # вторник
            2: 'wed',  # среда
            3: 'thu',  # четверг
            4: 'fri',  # пятница
            5: 'sat',  # суббота
            6: 'sun',  # воскресенье
        }

        weekday_num = date.weekday()  #0=пн, 6=вс
        weekday_name = weekdays_map[weekday_num]

        allowed_days = [d.strip().lower() for d in self.weekdays.split(',')]
        return weekday_name in allowed_days


class HabitProgress(models.Model):
    # Модель этапа освоения привычки
    # Связывает пользователя с привычкой и отслеживает прогресс
    STATUS_CHOICES = (
        ('in_progress', 'В процессе'),
        ('completed', 'Освоена'),
        ('abandoned', 'Забыта/Брошена'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='habit_progress',
        verbose_name='Пользователь'
    )
    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name='Привычка'
    )

    start_date = models.DateTimeField(default=timezone.now, verbose_name='Дата начала')
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='in_progress',
        verbose_name='Статус освоения'
    )
    current_streak = models.PositiveIntegerField(default=0, verbose_name='Текущая серия')
    max_streak = models.PositiveIntegerField(default=0, verbose_name='Максимальная серия')

    # Дата завершения
    completed_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата завершения')

    class Meta:
        verbose_name = 'Этап освоения'
        verbose_name_plural = 'Этапы освоения'
        ordering = ['-start_date']
        # Один пользователь может иметь только один активный этап освоения для конкретной привычки
        unique_together = ['user', 'habit']

    def __str__(self):
        return f"{self.user.username} - {self.habit.name} ({self.get_status_display()})"

    def update_streak(self, completed):
        # Обновление серии выполнения
        if completed:
            self.current_streak += 1
            if self.current_streak > self.max_streak:
                self.max_streak = self.current_streak
        else:
            self.current_streak = 0
        self.save()


class HabitCompletion(models.Model):
    # Модель выполнения привычки
    habit_progress = models.ForeignKey(
        HabitProgress,
        on_delete=models.CASCADE,
        related_name='completions',
        verbose_name='Этап освоения'
    )
    completion_date = models.DateField(default=timezone.now, verbose_name='Дата выполнения')
    status = models.BooleanField(default=True, verbose_name='Выполнено')
    note = models.TextField(blank=True, verbose_name='Заметка')

    class Meta:
        verbose_name = 'Выполнение привычки'
        verbose_name_plural = 'Выполнения привычек'
        ordering = ['-completion_date']
        unique_together = ['habit_progress', 'completion_date']

    def __str__(self):
        return f"{self.habit_progress.habit.name} - {self.completion_date} - {'Выполнено' if self.status else 'Не выполнено'}"