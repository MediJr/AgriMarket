from django.conf import settings
from django.db import models

from apps.catalog.models import Product


class Market(models.Model):
    name = models.CharField(max_length=160)
    city = models.CharField(max_length=120)
    province = models.CharField(max_length=120)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ["province", "city", "name"]
        unique_together = ("name", "city", "province")
        indexes = [models.Index(fields=["province", "city"])]

    def __str__(self):
        return f"{self.name} - {self.city}"


class PriceRecord(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="price_records")
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="price_records")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="CDF")
    unit = models.CharField(max_length=16, default="kg")
    recorded_at = models.DateField()
    source = models.CharField(max_length=160, blank=True)
    collector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    is_validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at", "product__name"]
        indexes = [
            models.Index(fields=["product", "recorded_at"]),
            models.Index(fields=["market", "recorded_at"]),
            models.Index(fields=["is_validated", "recorded_at"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["product", "market", "unit", "recorded_at"], name="unique_daily_market_price")
        ]

    def __str__(self):
        return f"{self.product} {self.price} {self.currency}/{self.unit}"
