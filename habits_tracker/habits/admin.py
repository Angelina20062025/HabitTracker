from django.contrib import admin
# Register your models here.
from django.contrib import admin
from .models import User, Habit, HabitProgress, HabitCompletion


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'role', 'date_registered']
    list_filter = ['role', 'date_registered']
    search_fields = ['username', 'email', 'first_name', 'last_name']


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'frequency', 'weekdays', 'created_by', 'created_at']
    list_filter = ['frequency', 'category', 'created_at']
    search_fields = ['name', 'description', 'category', 'frequency', 'weekdays', 'created_by']


@admin.register(HabitProgress)
class HabitProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'habit', 'status', 'start_date', 'current_streak', 'max_streak']
    list_filter = ['status', 'start_date']
    search_fields = ['user__username', 'habit__name']


@admin.register(HabitCompletion)
class HabitCompletionAdmin(admin.ModelAdmin):
    list_display = ['habit_progress', 'completion_date', 'status']
    list_filter = ['status', 'completion_date']
    search_fields = ['habit_progress__user__username', 'habit_progress__habit__name']