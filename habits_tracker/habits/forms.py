from django import forms
from django.contrib.auth import get_user_model
from .models import Habit, HabitCompletion

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    """
    Форма регистрации пользователя
    """
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Подтверждение пароля')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        labels = {
            'username': 'Имя пользователя',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
        }

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        return password_confirm

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует')
        return email


class HabitForm(forms.ModelForm):
    """
    Форма добавления привычки (только для админов)
    """

    weekdays = forms.MultipleChoiceField(
        label='Дни выполнения',
        required=False,
        choices=[
            ('mon', 'Понедельник'),
            ('tue', 'Вторник'),
            ('wed', 'Среда'),
            ('thu', 'Четверг'),
            ('fri', 'Пятница'),
            ('sat', 'Суббота'),
            ('sun', 'Воскресенье'),
        ],
        widget=forms.CheckboxSelectMultiple,
        help_text='Если не выбрано конкретного дня, выполнение разрешено в любой день'
    )

    class Meta:
        model = Habit
        fields = ['name', 'description', 'category', 'frequency', 'weekdays']
        labels = {
            'name': 'Название',
            'description': 'Описание',
            'category': 'Категория',
            'frequency': 'Частота выполнения',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_weekdays(self):
        weekdays = self.cleaned_data.get('weekdays')
        if weekdays:
            return ','.join(weekdays)
        return ''

class HabitCompletionForm(forms.Form):
    """
    Форма отметки выполнения привычки
    """
    completion_date = forms.DateField(
        label='Дата выполнения',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    status = forms.BooleanField(
        label='Выполнено',
        required=False,
        initial=True
    )
    note = forms.CharField(
        label='Заметка',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3})
    )