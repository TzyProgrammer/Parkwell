from django.contrib import admin
from .models import CustomUser, Car, Spot, Reservation

# Register your models here.
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'role')
    search_fields = ('username', 'email')

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'brand', 'model', 'color')
    search_fields = ('license_plate', 'brand', 'model', 'color')

@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = ('spot_number', 'status')
    search_fields = ('spot_number',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'spot', 'start_time', 'end_time')
    list_filter = ('start_time', 'end_time','spot')
    search_fields = ('user__username', 'spot__spot_number')