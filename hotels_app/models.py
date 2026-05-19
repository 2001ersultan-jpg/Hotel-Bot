from django.db import models


class Hotel(models.Model):
    """Модель отеля"""
    name = models.CharField(max_length=200, verbose_name='Название')
    city = models.CharField(max_length=100, verbose_name='Город')
    stars = models.IntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name='Звёзды')
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за ночь (тенге)')
    description = models.TextField(verbose_name='Описание', blank=True)
    address = models.CharField(max_length=300, verbose_name='Адрес', blank=True)
    phone = models.CharField(max_length=50, verbose_name='Телефон', blank=True)
    has_wifi = models.BooleanField(default=True, verbose_name='WiFi')
    has_parking = models.BooleanField(default=False, verbose_name='Парковка')
    has_pool = models.BooleanField(default=False, verbose_name='Бассейн')
    is_available = models.BooleanField(default=True, verbose_name='Доступен для бронирования')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отель'
        verbose_name_plural = 'Отели'
        ordering = ['city', 'stars']

    def __str__(self):
        return f"{self.name} ({self.city}, {'⭐' * self.stars})"

    def stars_display(self):
        return '⭐' * self.stars


class UserQuery(models.Model):
    """Модель для хранения запросов пользователей из Telegram"""
    QUERY_TYPES = [
        ('search', 'Поиск отелей'),
        ('filter', 'Фильтрация'),
        ('info', 'Информация об отеле'),
        ('start', 'Старт бота'),
        ('help', 'Помощь'),
    ]

    telegram_user_id = models.BigIntegerField(verbose_name='ID пользователя Telegram')
    telegram_username = models.CharField(max_length=100, verbose_name='Юзернейм', blank=True)
    first_name = models.CharField(max_length=100, verbose_name='Имя', blank=True)
    query_type = models.CharField(max_length=20, choices=QUERY_TYPES, verbose_name='Тип запроса')
    query_text = models.TextField(verbose_name='Текст запроса')
    response_text = models.TextField(verbose_name='Ответ бота', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время')

    class Meta:
        verbose_name = 'Запрос пользователя'
        verbose_name_plural = 'Запросы пользователей'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name or self.telegram_username} | {self.query_type} | {self.created_at.strftime('%d.%m.%Y %H:%M')}"


class Booking(models.Model):
    """Модель бронирования"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, verbose_name='Отель')
    telegram_user_id = models.BigIntegerField(verbose_name='ID пользователя')
    guest_name = models.CharField(max_length=200, verbose_name='Имя гостя')
    check_in = models.DateField(verbose_name='Дата заезда')
    check_out = models.DateField(verbose_name='Дата выезда')
    guests_count = models.IntegerField(default=1, verbose_name='Количество гостей')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.guest_name} → {self.hotel.name} ({self.check_in} – {self.check_out})"

    def total_nights(self):
        return (self.check_out - self.check_in).days

    def total_price(self):
        return self.total_nights() * self.hotel.price_per_night
