from django.contrib import admin
from .models import Hotel, UserQuery, Booking


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'stars_display', 'price_per_night', 'has_wifi', 'has_parking', 'has_pool', 'is_available')
    list_filter = ('city', 'stars', 'is_available', 'has_wifi', 'has_parking', 'has_pool')
    search_fields = ('name', 'city', 'address')
    list_editable = ('is_available',)

    def stars_display(self, obj):
        return '⭐' * obj.stars
    stars_display.short_description = 'Звёзды'


@admin.register(UserQuery)
class UserQueryAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'telegram_username', 'telegram_user_id', 'query_type', 'short_query', 'created_at')
    list_filter = ('query_type', 'created_at')
    search_fields = ('telegram_username', 'first_name', 'query_text')
    readonly_fields = ('telegram_user_id', 'telegram_username', 'first_name', 'query_type', 'query_text', 'response_text', 'created_at')

    def short_query(self, obj):
        return obj.query_text[:60] + '...' if len(obj.query_text) > 60 else obj.query_text
    short_query.short_description = 'Запрос'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('guest_name', 'hotel', 'check_in', 'check_out', 'guests_count', 'status', 'total_nights', 'total_price')
    list_filter = ('status', 'hotel__city', 'check_in')
    search_fields = ('guest_name', 'hotel__name')
    list_editable = ('status',)

    def total_nights(self, obj):
        return obj.total_nights()
    total_nights.short_description = 'Ночей'

    def total_price(self, obj):
        return f"{obj.total_price():,.0f} тг"
    total_price.short_description = 'Сумма'


admin.site.site_header = '🏨 Управление отелями'
admin.site.site_title = 'Hotel Bot Admin'
admin.site.index_title = 'Панель администратора'
