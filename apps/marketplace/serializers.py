from rest_framework import serializers

from .models import (
    Offer,
    Order,
    PurchaseRequest,
)
from .services.orders import OrderService


class OfferSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    producer_name = serializers.CharField(
        source="producer.get_full_name",
        read_only=True
    )

    total_price = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Offer

        fields = [
            "id",
            "producer",
            "producer_name",
            "product",
            "product_name",
            "title",
            "quantity",
            "unit",
            "unit_price",
            "total_price",
            "currency",
            "city",
            "province",
            "available_from",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "producer",
            "created_at",
            "updated_at",
        ]


class OrderSerializer(serializers.ModelSerializer):
    offer_title = serializers.CharField(source="offer.title", read_only=True)
    product_name = serializers.CharField(source="offer.product.name", read_only=True)
    seller_name = serializers.CharField(
        source="offer.producer.username",
        read_only=True,
    )
    buyer_name = serializers.CharField(source="buyer.username", read_only=True)
    unit = serializers.CharField(source="offer.unit", read_only=True)
    unit_price = serializers.DecimalField(
        source="offer.unit_price",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    currency = serializers.CharField(source="offer.currency", read_only=True)

    class Meta:
        model = Order

        fields = [
            "id",
            "buyer",
            "buyer_name",
            "offer",
            "offer_title",
            "product_name",
            "seller_name",
            "quantity",
            "unit",
            "unit_price",
            "currency",
            "status",
            "note",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "buyer",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        offer = attrs.get("offer") or getattr(self.instance, "offer", None)
        quantity = attrs.get("quantity")
        request = self.context.get("request")

        if not offer or quantity is None or not request:
            return attrs

        OrderService.validate_create(
            offer=offer,
            quantity=quantity,
            buyer=request.user,
        )
        return attrs


class PurchaseRequestSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    buyer_name = serializers.CharField(
        source="buyer.username",
        read_only=True
    )

    class Meta:
        model = PurchaseRequest

        fields = [
            "id",
            "buyer",
            "buyer_name",
            "product",
            "product_name",
            "quantity",
            "unit",
            "target_price",
            "currency",
            "city",
            "province",
            "needed_before",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "buyer",
            "created_at",
            "updated_at",
        ]