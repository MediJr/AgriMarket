from django.contrib import admin

from .models import Market, PriceRecord


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "province")
    search_fields = ("name", "city", "province")


@admin.register(PriceRecord)
class PriceRecordAdmin(admin.ModelAdmin):
    list_display = ("product", "market", "price", "currency", "unit", "recorded_at", "is_validated")
    list_filter = ("is_validated", "recorded_at", "market__province")
    search_fields = ("product__name", "market__name", "source")
