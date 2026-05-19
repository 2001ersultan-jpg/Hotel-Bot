"""
Скрипт для загрузки тестовых данных отелей в базу данных.
Запускать: python load_sample_data.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_project.settings')
django.setup()

from hotels_app.models import Hotel

Hotel.objects.all().delete()

hotels_data = [
    # Алматы
    {
        'name': 'Rixos Almaty',
        'city': 'Алматы',
        'stars': 5,
        'price_per_night': 85000,
        'description': 'Роскошный пятизвёздочный отель в центре Алматы с видом на горы.',
        'address': 'ул. Кабанбай батыра, 50',
        'phone': '+7 727 250 00 00',
        'has_wifi': True,
        'has_parking': True,
        'has_pool': True,
    },
    {
        'name': 'The Ritz-Carlton Almaty',
        'city': 'Алматы',
        'stars': 5,
        'price_per_night': 95000,
        'description': 'Изысканный отель в деловом центре города.',
        'address': 'ул. Желтоксан, 2/1',
        'phone': '+7 727 150 80 80',
        'has_wifi': True,
        'has_parking': True,
        'has_pool': True,
    },
    {
        'name': 'Hotel Kazakhstan',
        'city': 'Алматы',
        'stars': 4,
        'price_per_night': 35000,
        'description': 'Легендарный отель — символ Алматы с панорамным видом на город.',
        'address': 'пр. Достык, 52',
        'phone': '+7 727 291 91 01',
        'has_wifi': True,
        'has_parking': True,
        'has_pool': False,
    },
    {
        'name': 'ibis Almaty',
        'city': 'Алматы',
        'stars': 3,
        'price_per_night': 18000,
        'description': 'Удобный отель для деловых путешественников по доступным ценам.',
        'address': 'ул. Байзакова, 280',
        'phone': '+7 727 244 27 70',
        'has_wifi': True,
        'has_parking': False,
        'has_pool': False,
    },
    {
        'name': 'Nomad Inn',
        'city': 'Алматы',
        'stars': 2,
        'price_per_night': 9000,
        'description': 'Бюджетный хостел с дружелюбной атмосферой в центре города.',
        'address': 'ул. Панфилова, 115',
        'phone': '+7 727 291 18 11',
        'has_wifi': True,
        'has_parking': False,
        'has_pool': False,
    },
    # Астана
    {
        'name': 'Hilton Astana',
        'city': 'Астана',
        'stars': 5,
        'price_per_night': 75000,
        'description': 'Первоклассный отель в деловом центре столицы.',
        'address': 'пр. Туран, 28',
        'phone': '+7 7172 79 05 00',
        'has_wifi': True,
        'has_parking': True,
        'has_pool': True,
    },
    {
        'name': 'Ramada Plaza Astana',
        'city': 'Астана',
        'stars': 4,
        'price_per_night': 42000,
        'description': 'Современный отель с великолепным видом на Ак-Орду.',
        'address': 'ул. Бейбитшилик, 18',
        'phone': '+7 7172 59 73 00',
        'has_wifi': True,
        'has_parking': True,
        'has_pool': True,
    },
    {
        'name': 'Comfort Hotel Astana',
        'city': 'Астана',
        'stars': 3,
        'price_per_night': 22000,
        'description': 'Комфортабельный отель по разумным ценам в Астане.',
        'address': 'ул. Республики, 12',
        'phone': '+7 7172 31 44 44',
        'has_wifi': True,
        'has_parking': True,
        'has_pool': False,
    },
    # Шымкент
    {
        'name': 'Shymkent Hotel',
        'city': 'Шымкент',
        'stars': 4,
        'price_per_night': 28000,
        'description': 'Главный отель южной столицы Казахстана.',
        'address': 'пр. Республики, 15',
        'phone': '+7 7252 53 47 00',
        'has_wifi': True,
        'has_parking': True,
        'has_pool': False,
    },
    {
        'name': 'Asia Hotel Shymkent',
        'city': 'Шымкент',
        'stars': 3,
        'price_per_night': 14000,
        'description': 'Уютный отель с хорошим соотношением цены и качества.',
        'address': 'ул. Байтурсынова, 8',
        'phone': '+7 7252 21 00 21',
        'has_wifi': True,
        'has_parking': False,
        'has_pool': False,
    },
    # Актау
    {
        'name': 'Renaissance Aktau',
        'city': 'Актау',
        'stars': 5,
        'price_per_night': 68000,
        'description': 'Роскошный курортный отель на берегу Каспийского моря.',
        'address': '32-й микрорайон',
        'phone': '+7 7292 32 79 00',
        'has_wifi': True,
        'has_parking': True,
        'has_pool': True,
    },
    {
        'name': 'Caspian Hotel',
        'city': 'Актау',
        'stars': 3,
        'price_per_night': 19000,
        'description': 'Уютный отель с видом на Каспийское море.',
        'address': '9-й микрорайон, 12',
        'phone': '+7 7292 33 11 00',
        'has_wifi': True,
        'has_parking': True,
        'has_pool': False,
    },
]

for data in hotels_data:
    Hotel.objects.create(**data)

print(f"✅ Загружено {len(hotels_data)} отелей в базу данных!")
print("\nГорода:")
from hotels_app.models import Hotel
for city in Hotel.objects.values_list('city', flat=True).distinct():
    count = Hotel.objects.filter(city=city).count()
    print(f"  🏙️ {city}: {count} отелей")
