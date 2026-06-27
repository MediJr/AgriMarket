from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Profile, User
from apps.catalog.models import Category, Product
from apps.marketplace.models import Offer, Order, PurchaseRequest
from apps.prices.models import Market, PriceRecord


class Command(BaseCommand):
    help = "Charge des données de démonstration pour le MVP AgriMarket."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Chargement des données de démonstration...")

        cereals, _ = Category.objects.get_or_create(
            slug="cereales",
            defaults={"name": "Céréales", "description": "Maïs, riz, blé..."},
        )
        legumes, _ = Category.objects.get_or_create(
            slug="legumes",
            defaults={"name": "Légumes", "description": "Tomates, oignons..."},
        )

        mais, _ = Product.objects.get_or_create(
            slug="mais",
            defaults={
                "name": "Maïs",
                "category": cereals,
                "description": "Maïs jaune sec",
                "default_unit": "kg",
            },
        )
        tomate, _ = Product.objects.get_or_create(
            slug="tomate",
            defaults={
                "name": "Tomate",
                "category": legumes,
                "description": "Tomate fraîche",
                "default_unit": "kg",
            },
        )

        producer, created = User.objects.get_or_create(
            username="demo_producer",
            defaults={
                "email": "producer@agrimarket.local",
                "role": User.Role.PRODUCER,
                "first_name": "Jean",
                "last_name": "Producteur",
            },
        )
        if created:
            producer.set_password("demo1234")
            producer.save()
            Profile.objects.create(user=producer, city="Kinshasa", province="Kinshasa")

        supplier, created = User.objects.get_or_create(
            username="demo_supplier",
            defaults={
                "email": "supplier@agrimarket.local",
                "role": User.Role.SUPPLIER,
                "first_name": "Marie",
                "last_name": "Fournisseur",
            },
        )
        if created:
            supplier.set_password("demo1234")
            supplier.save()
            Profile.objects.create(user=supplier, city="Lubumbashi", province="Haut-Katanga")

        buyer, created = User.objects.get_or_create(
            username="demo_buyer",
            defaults={
                "email": "buyer@agrimarket.local",
                "role": User.Role.BUYER,
                "first_name": "Paul",
                "last_name": "Acheteur",
            },
        )
        if created:
            buyer.set_password("demo1234")
            buyer.save()
            Profile.objects.create(
                user=buyer,
                city="Kinshasa",
                province="Kinshasa",
                company_type="Restaurant",
            )

        market_kin, _ = Market.objects.get_or_create(
            name="Marché Central",
            city="Kinshasa",
            province="Kinshasa",
        )
        market_lshi, _ = Market.objects.get_or_create(
            name="Marché Mwange",
            city="Lubumbashi",
            province="Haut-Katanga",
        )

        PriceRecord.objects.get_or_create(
            product=mais,
            market=market_kin,
            unit="kg",
            recorded_at=date.today(),
            defaults={
                "price": Decimal("450"),
                "currency": "CDF",
                "is_validated": True,
                "source": "Collecte démo",
            },
        )
        PriceRecord.objects.get_or_create(
            product=tomate,
            market=market_lshi,
            unit="kg",
            recorded_at=date.today(),
            defaults={
                "price": Decimal("800"),
                "currency": "CDF",
                "is_validated": True,
                "source": "Collecte démo",
            },
        )

        offer, _ = Offer.objects.get_or_create(
            producer=producer,
            product=mais,
            title="Maïs premium Kinshasa",
            defaults={
                "quantity": Decimal("500"),
                "unit": "kg",
                "unit_price": Decimal("480"),
                "currency": "CDF",
                "city": "Kinshasa",
                "province": "Kinshasa",
                "description": "Maïs sec, qualité A",
            },
        )

        purchase_request, _ = PurchaseRequest.objects.get_or_create(
            buyer=buyer,
            product=mais,
            city="Kinshasa",
            province="Kinshasa",
            defaults={
                "quantity": Decimal("200"),
                "unit": "kg",
                "target_price": Decimal("500"),
                "currency": "CDF",
                "description": "Besoin pour restaurant",
            },
        )

        Order.objects.get_or_create(
            buyer=buyer,
            offer=offer,
            defaults={
                "quantity": Decimal("50"),
                "note": "Commande de démonstration",
            },
        )

        self.stdout.write(self.style.SUCCESS("Données de démonstration chargées."))
        self.stdout.write("Comptes : demo_producer / demo_supplier / demo_buyer")
        self.stdout.write("Mot de passe : demo1234")
