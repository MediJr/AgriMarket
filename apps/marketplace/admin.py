from django.contrib import admin

from .models import Offer, Order, PurchaseRequest


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "product",
        "producer",
        "quantity",
        "unit_price",
        "currency",
        "status",
        "city",
        "province",
    )

    list_filter = (
        "status",
        "province",
        "product",
    )

    search_fields = (
        "title",
        "description",
        "product__name",
        "producer__username",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "buyer",
        "offer",
        "quantity",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "buyer__username",
        "offer__title",
    )


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "buyer",
        "quantity",
        "unit",
        "target_price",
        "currency",
        "city",
        "province",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "province",
        "product",
    )

    search_fields = (
        "product__name",
        "buyer__username",
        "city",
        "province",
        "description",
    )