"""
Telegram-бот для поиска и бронирования отелей
Тема 29: Чат-бот отелей — поиск и фильтрация
Финальный этап (100%): Безопасность, валидация, расширенный функционал
"""

import os
import sys
import django
import logging
import telebot
from telebot import types
from datetime import datetime, date

# ======== НАСТРОЙКА ЛОГИРОВАНИЯ ========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ======== DJANGO SETUP ========
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_project.settings')
django.setup()

from hotels_app.models import Hotel, UserQuery, Booking

# ======== TOKEN  ========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8299940958:AAGRSIirA1ukmlzKV8J0TQiV8zCmk0E3rBw')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан! Установите переменную окружения BOT_TOKEN.")

bot = telebot.TeleBot(BOT_TOKEN)

# user data
user_states = {}
booking_data = {}


# ======== AUXILIARY FUNCTIONS ========

def safe_save_query(message, query_type, response_text=''):
    """Saves users in DB with error handling"""
    try:
        UserQuery.objects.create(
            telegram_user_id=message.from_user.id,
            telegram_username=message.from_user.username or '',
            first_name=message.from_user.first_name or '',
            query_type=query_type,
            query_text=(message.text or '')[:500],
            response_text=response_text[:500],
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения запроса: {e}")


def safe_save_query_raw(user_id, username, first_name, query_type, query_text, response_text=''):
    """The message objects signature is saved (for the callback)"""
    try:
        UserQuery.objects.create(
            telegram_user_id=user_id,
            telegram_username=username or '',
            first_name=first_name or '',
            query_type=query_type,
            query_text=query_text[:500],
            response_text=response_text[:500],
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения запроса: {e}")


def validate_name(name: str) -> bool:
    """Checks that the name contains only letters and spaces, minimum 2 characters"""
    name = name.strip()
    if len(name) < 2:
        return False
    if not all(c.isalpha() or c.isspace() or c in '-.' for c in name):
        return False
    return True


def validate_date_format(date_str: str):
    """Parses a date, returning a date object or None.
Supports the following formats: 06/25/2025 and 06/25/25"""
    date_str = date_str.strip()
    # Let's try a full year (2025)
    try:
        return datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError:
        pass
    # Trying a short year (25 → 2025)
    try:
        d = datetime.strptime(date_str, '%d.%m.%y').date()
        return d
    except ValueError:
        pass
    return None


def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        types.KeyboardButton('🔍 Поиск отелей'),
        types.KeyboardButton('🏙️ Выбрать город'),
        types.KeyboardButton('⭐ Фильтр по звёздам'),
        types.KeyboardButton('💰 Фильтр по цене'),
        types.KeyboardButton('🛎️ Фильтр по удобствам'),
        types.KeyboardButton('📋 Все отели'),
        types.KeyboardButton('📅 Мои бронирования'),
        types.KeyboardButton('🏆 Топ отелей'),
        types.KeyboardButton('💡 Случайный отель'),
        types.KeyboardButton('❓ Помощь'),
    )
    return keyboard


def get_cities_keyboard():
    try:
        cities = Hotel.objects.values_list('city', flat=True).distinct().order_by('city')
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        for city in cities:
            keyboard.add(types.KeyboardButton(f'🏙️ {city}'))
        keyboard.add(types.KeyboardButton('🔙 Назад'))
        return keyboard
    except Exception as e:
        logger.error(f"Ошибка получения городов: {e}")
        return get_main_keyboard()


def format_hotel_detail(hotel):
    """Детальная карточка отеля"""
    amenities = []
    if hotel.has_wifi:
        amenities.append('🌐 WiFi')
    if hotel.has_parking:
        amenities.append('🅿️ Парковка')
    if hotel.has_pool:
        amenities.append('🏊 Бассейн')

    text = (
        f"🏨 *{hotel.name}*\n"
        f"📍 {hotel.city}\n"
        f"{'⭐' * hotel.stars} ({hotel.stars} звезд)\n"
        f"💰 {hotel.price_per_night:,.0f} тг/ночь\n"
    )
    if hotel.address:
        text += f"🗺️ {hotel.address}\n"
    if hotel.phone:
        text += f"📞 {hotel.phone}\n"
    if amenities:
        text += f"✅ {' | '.join(amenities)}\n"
    if hotel.description:
        text += f"\n_{hotel.description}_"
    return text


def format_hotels_list(hotels, title="🏨 Найденные отели:"):
    if not hotels:
        return (
            "😔 *Отели по вашему запросу не найдены.*\n\n"
            "💡 Попробуйте:\n"
            "• Изменить название города\n"
            "• Увеличить бюджет\n"
            "• Уменьшить количество звёзд"
        )

    text = f"{title}\n\n"
    for i, hotel in enumerate(hotels, 1):
        text += f"{i}. *{hotel.name}* — {'⭐' * hotel.stars}\n"
        text += f"   📍 {hotel.city} | 💰 {hotel.price_per_night:,.0f} тг/ночь\n"
        amenities = []
        if hotel.has_wifi:
            amenities.append('WiFi')
        if hotel.has_parking:
            amenities.append('Парковка')
        if hotel.has_pool:
            amenities.append('Бассейн')
        if amenities:
            text += f"   ✅ {', '.join(amenities)}\n"
        text += "\n"

    text += f"_Всего найдено: {len(hotels)} отелей_"
    return text


def show_hotels_with_booking(message, hotels, title):
    """Показывает отели с кнопкой бронирования"""
    if not hotels:
        bot.send_message(
            message.chat.id,
            format_hotels_list([], title),
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return

    text = format_hotels_list(hotels, title)
    safe_save_query(message, 'search', text)

    keyboard = types.InlineKeyboardMarkup()
    for hotel in hotels:
        keyboard.add(types.InlineKeyboardButton(
            f"📅 Забронировать: {hotel.name}",
            callback_data=f"book_{hotel.id}"
        ))

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=get_main_keyboard())
    bot.send_message(message.chat.id, "Хотите забронировать отель?", reply_markup=keyboard)


# ======== КОМАНДЫ ========

@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name or "Гость"
    text = (
        f"👋 Привет, *{user_name}*!\n\n"
        f"🏨 Добро пожаловать в *Hotel Bot*!\n\n"
        f"Я помогу вам:\n"
        f"🔍 Найти отель по городу или названию\n"
        f"⭐ Отфильтровать по звёздности\n"
        f"💰 Выбрать по цене\n"
        f"🛎️ Фильтровать по удобствам (WiFi, бассейн, парковка)\n"
        f"📅 Забронировать и управлять бронированиями\n"
        f"📖 Посмотреть историю запросов\n\n"
        f"Используйте кнопки ниже или команды:\n"
        f"/help — справка\n"
        f"/mybookings — мои бронирования\n"
        f"/history — история запросов\n"
        f"/about — о боте"
    )
    safe_save_query(message, 'start', text)
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=get_main_keyboard())


@bot.message_handler(commands=['help'])
def help_command(message):
    text = (
        "📖 *Справка по боту:*\n\n"
        "🔍 *Поиск отелей* — поиск по городу или названию\n"
        "🏙️ *Выбрать город* — выбор из списка\n"
        "⭐ *Фильтр по звёздам* — от 1 до 5 звёзд\n"
        "💰 *Фильтр по цене* — по бюджету\n"
        "🛎️ *Фильтр по удобствам* — WiFi, бассейн, парковка\n"
        "📋 *Все отели* — полный список\n"
        "📅 *Мои бронирования* — просмотр и отмена броней\n\n"
        "*Команды:*\n"
        "/start — начать сначала\n"
        "/help — эта справка\n"
        "/mybookings — мои бронирования\n"
        "/history — история моих запросов\n"
        "/about — информация о боте\n\n"
        "💡 *Подсказка:* Вы можете написать название города прямо в чат!"
    )
    safe_save_query(message, 'help', text)
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=get_main_keyboard())


@bot.message_handler(commands=['about'])
def about_command(message):
    text = (
        "🏨 *Hotel Bot — бот для поиска и бронирования отелей*\n\n"
        "📌 *Версия:* 2.0 (Финальный этап)\n"
        "🛠️ *Технологии:*\n"
        "  • Python 3.x\n"
        "  • pyTelegramBotAPI (telebot)\n"
        "  • Django ORM\n"
        "  • SQLite / PostgreSQL\n\n"
        "📊 *Возможности:*\n"
        "  • Поиск отелей по городу и названию\n"
        "  • Фильтрация по звёздам, цене, удобствам\n"
        "  • Онлайн-бронирование\n"
        "  • История запросов\n"
        "  • Отмена бронирований\n\n"
        "👨‍💻 Проект разработан в рамках курса Python"
    )
    safe_save_query(message, 'about', text)
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=get_main_keyboard())


@bot.message_handler(commands=['mybookings'])
def my_bookings_command(message):
    show_my_bookings(message)


@bot.message_handler(commands=['history'])
def history_command(message):
    show_history(message)


def show_history(message):
    """Показывает историю запросов пользователя"""
    try:
        queries = UserQuery.objects.filter(
            telegram_user_id=message.from_user.id
        ).order_by('-created_at')[:10]

        if not queries:
            bot.send_message(
                message.chat.id,
                "📖 История запросов пуста.",
                reply_markup=get_main_keyboard()
            )
            return

        text = "📖 *Ваши последние 10 запросов:*\n\n"
        type_emoji = {
            'start': '🚀', 'help': '❓', 'search': '🔍',
            'filter': '🔧', 'booking': '📅', 'about': 'ℹ️'
        }
        for q in queries:
            emoji = type_emoji.get(q.query_type, '📌')
            created = q.created_at.strftime('%d.%m %H:%M')
            text += f"{emoji} `{created}` — {q.query_text[:40]}\n"

        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Ошибка показа истории: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка загрузки истории. Попробуйте позже.", reply_markup=get_main_keyboard())


# ======== КНОПКИ ГЛАВНОГО МЕНЮ ========

@bot.message_handler(func=lambda m: m.text == '📋 Все отели')
def handle_all_hotels(message):
    try:
        hotels = list(Hotel.objects.filter(is_available=True))
        show_hotels_with_booking(message, hotels, "📋 Все доступные отели:")
    except Exception as e:
        logger.error(f"Ошибка получения отелей: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка загрузки отелей. Попробуйте позже.", reply_markup=get_main_keyboard())


@bot.message_handler(func=lambda m: m.text == '🏙️ Выбрать город')
def handle_choose_city(message):
    bot.send_message(message.chat.id, "🏙️ Выберите город из списка:", reply_markup=get_cities_keyboard())


@bot.message_handler(func=lambda m: m.text == '🔙 Назад')
def handle_back(message):
    user_states.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "🏠 Главное меню", reply_markup=get_main_keyboard())


@bot.message_handler(func=lambda m: m.text == '❓ Помощь')
def handle_help(message):
    help_command(message)


@bot.message_handler(func=lambda m: m.text == '📅 Мои бронирования')
def handle_my_bookings(message):
    show_my_bookings(message)


@bot.message_handler(func=lambda m: m.text == '📖 История запросов')
def handle_history(message):
    show_history(message)


def show_my_bookings(message):
    """Показывает бронирования с возможностью отмены"""
    try:
        bookings = Booking.objects.filter(
            telegram_user_id=message.from_user.id
        ).order_by('-created_at')

        if not bookings:
            bot.send_message(
                message.chat.id,
                "📅 У вас пока нет бронирований.\n\nНайдите отель и нажмите «Забронировать»!",
                reply_markup=get_main_keyboard()
            )
            return

        text = "📅 *Ваши бронирования:*\n\n"
        keyboard = types.InlineKeyboardMarkup()

        for b in bookings:
            nights = (b.check_out - b.check_in).days
            total = nights * b.hotel.price_per_night
            status_emoji = {'pending': '⏳', 'confirmed': '✅', 'cancelled': '❌'}.get(b.status, '⏳')
            text += (
                f"{status_emoji} *{b.hotel.name}*\n"
                f"📍 {b.hotel.city}\n"
                f"👤 {b.guest_name} | 👥 {b.guests_count} гостей\n"
                f"📆 {b.check_in.strftime('%d.%m.%Y')} → {b.check_out.strftime('%d.%m.%Y')} ({nights} ночей)\n"
                f"💰 Итого: {total:,.0f} тг\n"
                f"Статус: {b.get_status_display()}\n\n"
            )
            # Кнопка отмены только для активных броней
            if b.status in ('pending', 'confirmed'):
                keyboard.add(types.InlineKeyboardButton(
                    f"❌ Отменить: {b.hotel.name} ({b.check_in.strftime('%d.%m')})",
                    callback_data=f"cancel_b_{b.id}"
                ))

        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=get_main_keyboard())
        if keyboard.keyboard:
            bot.send_message(message.chat.id, "Управление бронированиями:", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка показа бронирований: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка загрузки бронирований.", reply_markup=get_main_keyboard())


# ======== ФИЛЬТРЫ ========

@bot.message_handler(func=lambda m: m.text == '⭐ Фильтр по звёздам')
def handle_filter_stars(message):
    keyboard = types.InlineKeyboardMarkup(row_width=5)
    buttons = [types.InlineKeyboardButton(f"{'⭐' * i}", callback_data=f"stars_{i}") for i in range(1, 6)]
    keyboard.add(*buttons)
    keyboard.add(types.InlineKeyboardButton("✅ Все отели", callback_data="stars_0"))
    safe_save_query(message, 'filter', 'Фильтр по звёздам')
    bot.send_message(message.chat.id, "⭐ Выберите минимальное количество звёзд:", reply_markup=keyboard)


@bot.message_handler(func=lambda m: m.text == '💰 Фильтр по цене')
def handle_filter_price(message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("До 15 000 тг", callback_data="price_15000"),
        types.InlineKeyboardButton("До 30 000 тг", callback_data="price_30000"),
        types.InlineKeyboardButton("До 50 000 тг", callback_data="price_50000"),
        types.InlineKeyboardButton("До 100 000 тг", callback_data="price_100000"),
        types.InlineKeyboardButton("Все варианты", callback_data="price_999999"),
    )
    safe_save_query(message, 'filter', 'Фильтр по цене')
    bot.send_message(message.chat.id, "💰 Выберите максимальную цену за ночь:", reply_markup=keyboard)


@bot.message_handler(func=lambda m: m.text == '🛎️ Фильтр по удобствам')
def handle_filter_amenities(message):
    """Новый фильтр по удобствам"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("🌐 Только с WiFi", callback_data="amenity_wifi"),
        types.InlineKeyboardButton("🏊 Только с бассейном", callback_data="amenity_pool"),
        types.InlineKeyboardButton("🅿️ Только с парковкой", callback_data="amenity_parking"),
        types.InlineKeyboardButton("🌐🏊 WiFi + Бассейн", callback_data="amenity_wifi_pool"),
        types.InlineKeyboardButton("🌐🅿️ WiFi + Парковка", callback_data="amenity_wifi_parking"),
        types.InlineKeyboardButton("✅ Все удобства", callback_data="amenity_all"),
    )
    safe_save_query(message, 'filter', 'Фильтр по удобствам')
    bot.send_message(message.chat.id, "🛎️ Выберите удобства:", reply_markup=keyboard)


@bot.message_handler(func=lambda m: m.text == '🏆 Топ отелей')
def handle_top_hotels(message):
    """Показывает топ-5 отелей по звёздам"""
    try:
        hotels = list(Hotel.objects.filter(is_available=True).order_by('-stars', 'price_per_night')[:5])
        show_hotels_with_booking(message, hotels, "🏆 Топ-5 лучших отелей:")
        safe_save_query(message, 'search', 'Топ отелей')
    except Exception as e:
        logger.error(f"Ошибка топ отелей: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка загрузки.", reply_markup=get_main_keyboard())


@bot.message_handler(func=lambda m: m.text == '💡 Случайный отель')
def handle_random_hotel(message):
    """Показывает случайный отель"""
    try:
        hotels = list(Hotel.objects.filter(is_available=True).order_by('?')[:1])
        if hotels:
            show_hotels_with_booking(message, hotels, "💡 Случайный отель для вас:")
        else:
            bot.send_message(message.chat.id, "😔 Нет доступных отелей.", reply_markup=get_main_keyboard())
        safe_save_query(message, 'search', 'Случайный отель')
    except Exception as e:
        logger.error(f"Ошибка случайного отеля: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка загрузки.", reply_markup=get_main_keyboard())


@bot.message_handler(func=lambda m: m.text == '🔍 Поиск отелей')
def handle_search(message):
    user_states[message.from_user.id] = 'waiting_search'
    safe_save_query(message, 'search', 'Поиск отелей')
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('🔙 Назад'))
    bot.send_message(
        message.chat.id,
        "🔍 Введите название *города* или *отеля*:\n\n_Например: Алматы или Grand Hotel_",
        parse_mode='Markdown',
        reply_markup=keyboard
    )


@bot.message_handler(func=lambda m: m.text and m.text.startswith('🏙️ ') and m.text != '🏙️ Выбрать город')
def handle_city_button(message):
    city = message.text.replace('🏙️ ', '').strip()
    try:
        hotels = list(Hotel.objects.filter(city__icontains=city, is_available=True))
        show_hotels_with_booking(message, hotels, f"🏙️ Отели в городе *{city}*:")
    except Exception as e:
        logger.error(f"Ошибка поиска по городу: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка поиска.", reply_markup=get_main_keyboard())


# ======== CALLBACK ОБРАБОТЧИКИ ========

@bot.callback_query_handler(func=lambda call: call.data.startswith('book_'))
def callback_book_hotel(call):
    try:
        hotel_id = int(call.data.split('_')[1])
        hotel = Hotel.objects.get(id=hotel_id)
    except (Hotel.DoesNotExist, ValueError, IndexError):
        bot.answer_callback_query(call.id, "❌ Отель не найден!")
        return
    except Exception as e:
        logger.error(f"Ошибка бронирования: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка. Попробуйте позже.")
        return

    booking_data[call.from_user.id] = {'hotel_id': hotel_id, 'hotel_name': hotel.name}
    user_states[call.from_user.id] = 'booking_name'

    bot.answer_callback_query(call.id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('🔙 Отмена'))

    text = (
        f"📅 *Бронирование отеля:*\n"
        f"🏨 {hotel.name}\n"
        f"📍 {hotel.city}\n"
        f"💰 {hotel.price_per_night:,.0f} тг/ночь\n\n"
        f"*Шаг 1/4:* Введите ваше имя и фамилию:\n"
        f"_Например: Иван Иванов_"
    )
    bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('stars_'))
def callback_stars(call):
    try:
        stars = int(call.data.split('_')[1])
        if stars == 0:
            hotels = list(Hotel.objects.filter(is_available=True))
            title = "🏨 Все отели:"
        else:
            hotels = list(Hotel.objects.filter(stars__gte=stars, is_available=True))
            title = f"⭐ Отели от {'⭐' * stars}:"

        text = format_hotels_list(hotels, title)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown')

        keyboard = types.InlineKeyboardMarkup()
        for hotel in hotels:
            keyboard.add(types.InlineKeyboardButton(
                f"📅 Забронировать: {hotel.name}",
                callback_data=f"book_{hotel.id}"
            ))
        if hotels:
            bot.send_message(call.message.chat.id, "Хотите забронировать?", reply_markup=keyboard)

        safe_save_query_raw(
            call.from_user.id, call.from_user.username, call.from_user.first_name,
            'filter', f"Фильтр по звёздам: {stars}+", text
        )
    except Exception as e:
        logger.error(f"Ошибка фильтра по звёздам: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка фильтра.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('price_'))
def callback_price(call):
    try:
        max_price = int(call.data.split('_')[1])
        hotels = list(Hotel.objects.filter(price_per_night__lte=max_price, is_available=True))
        title = f"💰 Отели до {max_price:,} тг/ночь:"
        text = format_hotels_list(hotels, title)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown')

        keyboard = types.InlineKeyboardMarkup()
        for hotel in hotels:
            keyboard.add(types.InlineKeyboardButton(
                f"📅 Забронировать: {hotel.name}",
                callback_data=f"book_{hotel.id}"
            ))
        if hotels:
            bot.send_message(call.message.chat.id, "Хотите забронировать?", reply_markup=keyboard)

        safe_save_query_raw(
            call.from_user.id, call.from_user.username, call.from_user.first_name,
            'filter', f"Фильтр по цене: до {max_price} тг", text
        )
    except Exception as e:
        logger.error(f"Ошибка фильтра по цене: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка фильтра.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('amenity_'))
def callback_amenity(call):
    """Обработчик фильтра по удобствам"""
    try:
        amenity = call.data.replace('amenity_', '')
        hotels_qs = Hotel.objects.filter(is_available=True)

        if amenity == 'wifi':
            hotels = list(hotels_qs.filter(has_wifi=True))
            title = "🌐 Отели с WiFi:"
        elif amenity == 'pool':
            hotels = list(hotels_qs.filter(has_pool=True))
            title = "🏊 Отели с бассейном:"
        elif amenity == 'parking':
            hotels = list(hotels_qs.filter(has_parking=True))
            title = "🅿️ Отели с парковкой:"
        elif amenity == 'wifi_pool':
            hotels = list(hotels_qs.filter(has_wifi=True, has_pool=True))
            title = "🌐🏊 Отели с WiFi и бассейном:"
        elif amenity == 'wifi_parking':
            hotels = list(hotels_qs.filter(has_wifi=True, has_parking=True))
            title = "🌐🅿️ Отели с WiFi и парковкой:"
        else:
            hotels = list(hotels_qs)
            title = "✅ Все отели:"

        text = format_hotels_list(hotels, title)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown')

        keyboard = types.InlineKeyboardMarkup()
        for hotel in hotels:
            keyboard.add(types.InlineKeyboardButton(
                f"📅 Забронировать: {hotel.name}",
                callback_data=f"book_{hotel.id}"
            ))
        if hotels:
            bot.send_message(call.message.chat.id, "Хотите забронировать?", reply_markup=keyboard)

        safe_save_query_raw(
            call.from_user.id, call.from_user.username, call.from_user.first_name,
            'filter', f"Фильтр по удобствам: {amenity}", text
        )
    except Exception as e:
        logger.error(f"Ошибка фильтра по удобствам: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка фильтра.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_b_'))
def callback_cancel_user_booking(call):
    """Отмена конкретного бронирования пользователем"""
    try:
        booking_id = int(call.data.split('_')[2])
        booking = Booking.objects.get(id=booking_id, telegram_user_id=call.from_user.id)

        if booking.status == 'cancelled':
            bot.answer_callback_query(call.id, "Это бронирование уже отменено.")
            return

        booking.status = 'cancelled'
        booking.save()

        bot.answer_callback_query(call.id, "✅ Бронирование отменено")
        bot.edit_message_text(
            f"❌ Бронирование *{booking.hotel.name}* отменено.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        logger.info(f"Пользователь {call.from_user.id} отменил бронирование {booking_id}")

    except Booking.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Бронирование не найдено.")
    except Exception as e:
        logger.error(f"Ошибка отмены бронирования: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка. Попробуйте позже.")


# ======== ОБРАБОТКА СОСТОЯНИЙ БРОНИРОВАНИЯ ========

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    # Проверка на пустой ввод
    if not message.text or not message.text.strip():
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, введите текст.", reply_markup=get_main_keyboard())
        return

    user_id = message.from_user.id
    state = user_states.get(user_id)

    # Отмена бронирования
    if message.text in ('🔙 Отмена', '🔙 Назад'):
        user_states.pop(user_id, None)
        booking_data.pop(user_id, None)
        if message.text == '🔙 Отмена':
            bot.send_message(message.chat.id, "❌ Бронирование отменено.", reply_markup=get_main_keyboard())
        else:
            bot.send_message(message.chat.id, "🏠 Главное меню", reply_markup=get_main_keyboard())
        return

    # Шаг 1: Ввод имени с валидацией
    if state == 'booking_name':
        name = message.text.strip()
        if not validate_name(name):
            bot.send_message(
                message.chat.id,
                "❌ *Некорректное имя!*\n\nИмя должно:\n• Содержать минимум 2 символа\n• Состоять только из букв\n\n_Пример: Иван Петров_",
                parse_mode='Markdown'
            )
            return
        booking_data[user_id]['guest_name'] = name
        user_states[user_id] = 'booking_checkin'
        bot.send_message(
            message.chat.id,
            f"✅ Имя: *{name}*\n\n*Шаг 2/4:* Введите дату заезда:\n📅 Формат: `ДД.ММ.ГГГГ`\n_Например: 25.06.2025_",
            parse_mode='Markdown'
        )
        return

    # Шаг 2: Дата заезда
    if state == 'booking_checkin':
        check_in = validate_date_format(message.text)
        if not check_in:
            bot.send_message(
                message.chat.id,
                "❌ *Неверный формат даты!*\n\nВведите дату в формате `ДД.ММ.ГГГГ`\n_Например: 25.06.2025_",
                parse_mode='Markdown'
            )
            return
        if check_in < date.today():
            bot.send_message(
                message.chat.id,
                "❌ Дата заезда не может быть в прошлом!\n\nВведите актуальную дату:",
                parse_mode='Markdown'
            )
            return
        booking_data[user_id]['check_in'] = check_in
        user_states[user_id] = 'booking_checkout'
        bot.send_message(
            message.chat.id,
            f"✅ Дата заезда: *{check_in.strftime('%d.%m.%Y')}*\n\n*Шаг 3/4:* Введите дату выезда:\n📅 Формат: `ДД.ММ.ГГГГ`",
            parse_mode='Markdown'
        )
        return

    # Шаг 3: Дата выезда
    if state == 'booking_checkout':
        check_out = validate_date_format(message.text)
        if not check_out:
            bot.send_message(
                message.chat.id,
                "❌ *Неверный формат даты!*\n\nВведите дату в формате `ДД.ММ.ГГГГ`",
                parse_mode='Markdown'
            )
            return
        check_in = booking_data[user_id]['check_in']
        if check_out <= check_in:
            bot.send_message(
                message.chat.id,
                "❌ Дата выезда должна быть *позже* даты заезда!\n\nВведите корректную дату выезда:",
                parse_mode='Markdown'
            )
            return
        nights = (check_out - check_in).days
        if nights > 365:
            bot.send_message(message.chat.id, "❌ Максимальный срок бронирования — 365 дней. Введите другую дату:")
            return

        booking_data[user_id]['check_out'] = check_out
        user_states[user_id] = 'booking_guests'
        bot.send_message(
            message.chat.id,
            f"✅ Дата выезда: *{check_out.strftime('%d.%m.%Y')}* ({nights} ночей)\n\n*Шаг 4/4:* Сколько гостей?\n_Введите число от 1 до 10_",
            parse_mode='Markdown'
        )
        return

    # Шаг 4: Количество гостей
    if state == 'booking_guests':
        if not message.text.strip().isdigit():
            bot.send_message(message.chat.id, "❌ Введите число, например: `2`", parse_mode='Markdown')
            return
        guests = int(message.text.strip())
        if guests < 1 or guests > 10:
            bot.send_message(message.chat.id, "❌ Введите число от *1* до *10*:", parse_mode='Markdown')
            return

        try:
            data = booking_data[user_id]
            hotel = Hotel.objects.get(id=data['hotel_id'])
        except (Hotel.DoesNotExist, KeyError):
            bot.send_message(message.chat.id, "❌ Ошибка: отель не найден. Начните заново.", reply_markup=get_main_keyboard())
            user_states.pop(user_id, None)
            booking_data.pop(user_id, None)
            return

        check_in = data['check_in']
        check_out = data['check_out']
        nights = (check_out - check_in).days
        total = nights * hotel.price_per_night

        user_states[user_id] = 'booking_confirm'
        booking_data[user_id]['guests'] = guests

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_booking"),
            types.InlineKeyboardButton("❌ Отменить", callback_data="cancel_booking"),
        )

        text = (
            f"📋 *Подтверждение бронирования:*\n\n"
            f"🏨 {hotel.name}\n"
            f"📍 {hotel.city}\n"
            f"👤 Гость: {data['guest_name']}\n"
            f"👥 Гостей: {guests}\n"
            f"📆 Заезд: {check_in.strftime('%d.%m.%Y')}\n"
            f"📆 Выезд: {check_out.strftime('%d.%m.%Y')}\n"
            f"🌙 Ночей: {nights}\n"
            f"💰 Цена за ночь: {hotel.price_per_night:,.0f} тг\n"
            f"💳 *Итого: {total:,.0f} тг*\n\n"
            f"Подтвердить бронирование?"
        )
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=keyboard)
        return

    # Поиск по городу или названию отеля
    if state == 'waiting_search':
        query = message.text.strip()
        if len(query) < 2:
            bot.send_message(message.chat.id, "❌ Введите минимум 2 символа для поиска.")
            return
        try:
            hotels = list(Hotel.objects.filter(
                city__icontains=query, is_available=True
            ) | Hotel.objects.filter(
                name__icontains=query, is_available=True
            ))
            show_hotels_with_booking(message, hotels, f"🔍 Результаты поиска *\"{query}\"*:")
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            bot.send_message(message.chat.id, "❌ Ошибка поиска.", reply_markup=get_main_keyboard())
        user_states.pop(user_id, None)
        return

    # ======== ПРОСТЫЕ ДИАЛОГОВЫЕ ОТВЕТЫ ========
    text_lower = message.text.strip().lower()

    # Приветствия
    greetings = ('привет', 'хай', 'здравствуй', 'здравствуйте', 'салам', 'сәлем',
                 'добрый день', 'добрый вечер', 'доброе утро', 'hello', 'hi')
    if text_lower in greetings:
        user_name = message.from_user.first_name or "Гость"
        bot.send_message(
            message.chat.id,
            f"👋 Привет, {user_name}! Чем могу помочь?\n\nИспользуйте кнопки меню или нажмите ❓ Помощь.",
            reply_markup=get_main_keyboard()
        )
        return

    # Благодарность
    thanks = ('спасибо', 'спс', 'благодарю', 'благодарен', 'рахмет', 'thanks', 'thank you')
    if text_lower in thanks:
        bot.send_message(
            message.chat.id,
            "😊 Пожалуйста! Если нужна помощь — жмите ❓ Помощь.",
            reply_markup=get_main_keyboard()
        )
        return

    # Пока / До свидания
    goodbyes = ('пока', 'до свидания', 'досвидания', 'до встречи', 'прощай', 'bye', 'goodbye')
    if text_lower in goodbyes:
        bot.send_message(
            message.chat.id,
            "👋 До свидания! Возвращайтесь, когда нужно найти отель. 🏨",
            reply_markup=get_main_keyboard()
        )
        return

    # Как дела / Как ты
    howru = ('как дела', 'как дела?', 'как ты', 'как ты?', 'как поживаешь', 'всё хорошо?')
    if text_lower in howru:
        bot.send_message(
            message.chat.id,
            "🤖 Я бот, у меня всё отлично! Готов помочь найти отель. 🏨",
            reply_markup=get_main_keyboard()
        )
        return

    # Кто ты / Что умеешь
    whoru = ('кто ты', 'кто ты?', 'что ты', 'что умеешь', 'что ты умеешь', 'что ты делаешь')
    if text_lower in whoru:
        bot.send_message(
            message.chat.id,
            "🏨 Я Hotel Bot — помогаю искать и бронировать отели!\n\nНажмите ❓ Помощь чтобы узнать подробнее.",
            reply_markup=get_main_keyboard()
        )
        return

    # Да / Ок
    yes_words = ('да', 'ок', 'окей', 'хорошо', 'ладно', 'понял', 'понятно', 'ok', 'okay')
    if text_lower in yes_words:
        bot.send_message(
            message.chat.id,
            "👍 Отлично! Используйте кнопки меню для поиска отелей.",
            reply_markup=get_main_keyboard()
        )
        return

    # Неизвестная команда — оставлено как было
    bot.send_message(
        message.chat.id,
        "🤔 Не понимаю эту команду.\n\nИспользуйте кнопки меню или /help для справки.",
        reply_markup=get_main_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data == 'confirm_booking')
def callback_confirm_booking(call):
    user_id = call.from_user.id
    data = booking_data.get(user_id)

    if not data:
        bot.answer_callback_query(call.id, "❌ Данные бронирования не найдены! Начните заново.")
        return

    try:
        hotel = Hotel.objects.get(id=data['hotel_id'])
        Booking.objects.create(
            hotel=hotel,
            telegram_user_id=user_id,
            guest_name=data['guest_name'],
            check_in=data['check_in'],
            check_out=data['check_out'],
            guests_count=data['guests'],
            status='pending',
        )

        user_states.pop(user_id, None)
        booking_data.pop(user_id, None)

        nights = (data['check_out'] - data['check_in']).days
        total = nights * hotel.price_per_night

        bot.edit_message_text(
            f"🎉 *Бронирование успешно оформлено!*\n\n"
            f"🏨 {hotel.name}\n"
            f"📍 {hotel.city}\n"
            f"👤 {data['guest_name']} | 👥 {data['guests']} гостей\n"
            f"📆 {data['check_in'].strftime('%d.%m.%Y')} → {data['check_out'].strftime('%d.%m.%Y')}\n"
            f"🌙 {nights} ночей\n"
            f"💳 Итого: *{total:,.0f} тг*\n\n"
            f"Статус: ⏳ Ожидает подтверждения\n\n"
            f"Администратор свяжется с вами в ближайшее время.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.send_message(
            call.message.chat.id,
            "📅 Посмотреть все бронирования: «Мои бронирования» или /mybookings",
            reply_markup=get_main_keyboard()
        )
        logger.info(f"Новое бронирование: пользователь {user_id}, отель {hotel.name}")

    except Hotel.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Отель не найден!")
    except Exception as e:
        logger.error(f"Ошибка создания бронирования: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при бронировании. Попробуйте позже.")


@bot.callback_query_handler(func=lambda call: call.data == 'cancel_booking')
def callback_cancel_booking(call):
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    booking_data.pop(user_id, None)
    bot.edit_message_text("❌ Бронирование отменено.", call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "🏠 Главное меню:", reply_markup=get_main_keyboard())


# ======== ЗАПУСК ========

if __name__ == '__main__':
    logger.info("🏨 Hotel Bot запускается...")
    print("🏨 Hotel Bot запущен!")
    print("Логи сохраняются в bot.log")
    print("Нажмите Ctrl+C для остановки")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем.")
        print("\n👋 Бот остановлен.")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        raise