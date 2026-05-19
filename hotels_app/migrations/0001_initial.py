from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Hotel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('city', models.CharField(max_length=100, verbose_name='Город')),
                ('stars', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], verbose_name='Звёзды')),
                ('price_per_night', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена за ночь (тенге)')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('address', models.CharField(blank=True, max_length=300, verbose_name='Адрес')),
                ('phone', models.CharField(blank=True, max_length=50, verbose_name='Телефон')),
                ('has_wifi', models.BooleanField(default=True, verbose_name='WiFi')),
                ('has_parking', models.BooleanField(default=False, verbose_name='Парковка')),
                ('has_pool', models.BooleanField(default=False, verbose_name='Бассейн')),
                ('is_available', models.BooleanField(default=True, verbose_name='Доступен для бронирования')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Отель', 'verbose_name_plural': 'Отели', 'ordering': ['city', 'stars']},
        ),
        migrations.CreateModel(
            name='UserQuery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_user_id', models.BigIntegerField(verbose_name='ID пользователя Telegram')),
                ('telegram_username', models.CharField(blank=True, max_length=100, verbose_name='Юзернейм')),
                ('first_name', models.CharField(blank=True, max_length=100, verbose_name='Имя')),
                ('query_type', models.CharField(choices=[('search', 'Поиск отелей'), ('filter', 'Фильтрация'), ('info', 'Информация об отеле'), ('start', 'Старт бота'), ('help', 'Помощь')], max_length=20, verbose_name='Тип запроса')),
                ('query_text', models.TextField(verbose_name='Текст запроса')),
                ('response_text', models.TextField(blank=True, verbose_name='Ответ бота')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата и время')),
            ],
            options={'verbose_name': 'Запрос пользователя', 'verbose_name_plural': 'Запросы пользователей', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hotel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hotels_app.hotel', verbose_name='Отель')),
                ('telegram_user_id', models.BigIntegerField(verbose_name='ID пользователя')),
                ('guest_name', models.CharField(max_length=200, verbose_name='Имя гостя')),
                ('check_in', models.DateField(verbose_name='Дата заезда')),
                ('check_out', models.DateField(verbose_name='Дата выезда')),
                ('guests_count', models.IntegerField(default=1, verbose_name='Количество гостей')),
                ('status', models.CharField(choices=[('pending', 'Ожидает подтверждения'), ('confirmed', 'Подтверждено'), ('cancelled', 'Отменено')], default='pending', max_length=20, verbose_name='Статус')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
            ],
            options={'verbose_name': 'Бронирование', 'verbose_name_plural': 'Бронирования', 'ordering': ['-created_at']},
        ),
    ]
