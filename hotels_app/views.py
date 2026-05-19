from django.shortcuts import render
from django.db.models import Count, Avg
from .models import Hotel, UserQuery, Booking


def index(request):
    """Главная страница с статистикой"""
    stats = {
        'total_hotels': Hotel.objects.count(),
        'total_queries': UserQuery.objects.count(),
        'total_bookings': Booking.objects.count(),
        'cities': Hotel.objects.values_list('city', flat=True).distinct(),
    }
    recent_queries = UserQuery.objects.order_by('-created_at')[:10]
    hotels = Hotel.objects.filter(is_available=True)[:6]

    return render(request, 'hotels_app/index.html', {
        'stats': stats,
        'recent_queries': recent_queries,
        'hotels': hotels,
    })
