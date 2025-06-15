from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateField, BooleanField
from wtforms.validators import DataRequired, Length, Optional

class LoginForm(FlaskForm):
    """Форма входа"""
    username = StringField('Логин', validators=[
        DataRequired(message='Введите логин'),
        Length(min=3, max=50)
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Введите пароль')
    ])

class ApplicationFilterForm(FlaskForm):
    """Форма фильтров для заявок"""
    date_from = DateField('От', validators=[Optional()])
    date_to = DateField('До', validators=[Optional()])
    country = StringField('Страна', validators=[Optional()])
    source = SelectField('Источник', coerce=int, validators=[Optional()])

class TextEditForm(FlaskForm):
    """Форма редактирования текста"""
    text = TextAreaField('Текст', validators=[
        DataRequired(message='Введите текст')
    ])
    
class TrafficSourceForm(FlaskForm):
    """Форма создания источника трафика"""
    name = StringField('Название', validators=[
        DataRequired(message='Введите название'),
        Length(min=3, max=100)
    ])
    platform = SelectField('Платформа', choices=[
        ('facebook', 'Facebook Ads'),
        ('google', 'Google Ads'),
        ('telegram_ads', 'Telegram Ads'),
        ('propellerads', 'PropellerAds'),
        ('evadav', 'Evadav'),
        ('richads', 'RichAds'),
        ('pushhouse', 'PushHouse'),
        ('onclick', 'OnClick')
    ])
    # Динамические поля будут добавляться в зависимости от платформы

class BroadcastForm(FlaskForm):
    """Форма рассылки"""
    message = TextAreaField('Сообщение', validators=[
        DataRequired(message='Введите сообщение'),
        Length(min=10, max=4096)
    ])
    target = SelectField('Целевая аудитория', choices=[
        ('all', 'Все пользователи'),
        ('no_application', 'Без заявки'),
        ('with_application', 'С заявкой')
    ])
    scheduled = BooleanField('Запланировать')
    scheduled_time = DateField('Время отправки', validators=[Optional()])
