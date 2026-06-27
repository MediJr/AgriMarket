from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.catalog.models import Product


class Offer(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        ACTIVE = "active", "Active"
        RESERVED = "reserved", "Reservee"
        SOLD = "sold", "Vendue"
        WITHDRAWN = "withdrawn", "Retiree"

    producer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="offers"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="offers"
    )

    title = models.CharField(max_length=180)

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    unit = models.CharField(max_length=16)

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=8,
        default="CDF"
    )

    city = models.CharField(max_length=120)

    province = models.CharField(max_length=120)

    available_from = models.DateField(
        null=True,
        blank=True
    )

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["status", "province", "city"]),
            models.Index(fields=["product", "status"]),
            models.Index(fields=["unit_price"]),
        ]

    @property
    def total_price(self):
        return (
            (self.quantity or Decimal("0"))
            * (self.unit_price or Decimal("0"))
        )

    def __str__(self):
        return self.title


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        ACCEPTED = "accepted", "Acceptee"
        PAID = "paid", "Payee"
        SHIPPED = "shipped", "Expediee"
        COMPLETED = "completed", "Terminee"
        CANCELLED = "cancelled", "Annulee"

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    offer = models.ForeignKey(
        Offer,
        on_delete=models.PROTECT,
        related_name="orders"
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING
    )

    note = models.TextField(blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["buyer", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"Commande #{self.pk}"


class PurchaseRequest(models.Model):

    class Status(models.TextChoices):
        OPEN = "open", "Ouverte"
        MATCHED = "matched", "Correspondance trouvée"
        CLOSED = "closed", "Fermée"

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="purchase_requests"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="purchase_requests"
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    unit = models.CharField(
        max_length=16,
        default="kg"
    )

    target_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=8,
        default="CDF"
    )

    city = models.CharField(
        max_length=120
    )

    province = models.CharField(
        max_length=120
    )

    needed_before = models.DateField(
        null=True,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["product"]),
            models.Index(fields=["province", "city"]),
            models.Index(fields=["target_price"]),
        ]

    def __str__(self):
        return (
            f"{self.product.name} "
            f"({self.quantity} {self.unit})"
        )