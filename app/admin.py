from django.contrib import admin
from .models import UnlockSlot, UnlockBooking, Profile, Attendance


@admin.register(UnlockSlot)
class UnlockSlotAdmin(admin.ModelAdmin):
    list_display = ('date', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('date',)


@admin.register(UnlockBooking)
class UnlockBookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'slot', 'booked_at')
    search_fields = ('user__username', 'slot__date')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'slot', 'is_present', 'marked_by', 'marked_at')
    list_filter = ('is_present', 'slot__date')
    search_fields = ('user__username', 'slot__date')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'full_name', 'enrollment')
