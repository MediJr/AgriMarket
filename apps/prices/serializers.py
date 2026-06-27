from rest_framework import serializers

from .models import Market, PriceRecord


class MarketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Market
        fields = ["id", "name", "city", "province", "latitude", "longitude"]


class PriceRecordSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    market_name = serializers.CharField(source="market.name", read_only=True)

    class Meta:
        model = PriceRecord
        fields = [
            "id",
            "product",
            "product_name",
            "market",
            "market_name",
            "price",
            "currency",
            "unit",
            "recorded_at",
            "source",
            "collector",
            "is_validated",
            "created_at",
        ]
        read_only_fields = ["id", "collector", "is_validated", "created_at"]
