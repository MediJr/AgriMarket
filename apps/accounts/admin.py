from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Profile, User


@admin.register(User)
class AgriMarketUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("AgriMarket", {"fields": ("role", "phone", "is_verified")}),)
    list_display = ("username", "email", "role", "is_verified", "is_staff")
    list_filter = ("role", "is_verified", "is_staff")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "city", "province", "updated_at")
    search_fields = ("user__username", "organization", "city", "province")
