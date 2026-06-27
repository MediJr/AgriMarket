from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        PRODUCER = "producer", "Producteur"
        SUPPLIER = "supplier", "Fournisseur"
        BUYER = "buyer", "Acheteur"
        TRANSPORTER = "transporter", "Transporteur"
        COLLECTOR = "collector", "Collecteur de prix"
        ADMIN = "admin", "Administrateur"

    role = models.CharField(
        max_length=24,
        choices=Role.choices,
        default=Role.BUYER
    )

    phone = models.CharField(
        max_length=32,
        blank=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.username


class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    organization = models.CharField(
        max_length=160,
        blank=True
    )

    company_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Restaurant, Hôtel, Grossiste, Coopérative, Supermarché..."
    )

    city = models.CharField(
        max_length=120,
        blank=True
    )

    province = models.CharField(
        max_length=120,
        blank=True
    )

    address = models.CharField(
        max_length=255,
        blank=True
    )

    bio = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Profil {self.user.username}"