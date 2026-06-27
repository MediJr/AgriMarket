from decimal import Decimal
from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product
from apps.prices.models import Market, PriceRecord
from apps.prices.services.price_context import PriceContextService


class PriceContextServiceTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Céréales", slug="cereales")
        self.product = Product.objects.create(
            name="Maïs",
            slug="mais",
            category=category,
        )
        market = Market.objects.create(
            name="Marché Central",
            city="Kinshasa",
            province="Kinshasa",
        )
        PriceRecord.objects.create(
            product=self.product,
            market=market,
            price=Decimal("400"),
            unit="kg",
            recorded_at=date.today(),
            is_validated=True,
        )
        market2 = Market.objects.create(
            name="Marché Secondaire",
            city="Kinshasa",
            province="Kinshasa",
        )
        PriceRecord.objects.create(
            product=self.product,
            market=market2,
            price=Decimal("600"),
            unit="kg",
            recorded_at=date.today(),
            is_validated=False,
        )

    def test_validated_records_only(self):
        context = PriceContextService.get_context(
            product_id=self.product.pk,
            province="Kinshasa",
        )
        self.assertEqual(context["record_count"], 1)
        self.assertEqual(context["avg_price"], Decimal("400"))

    def test_price_context_api(self):
        client = APIClient()
        response = client.get(
            f"/api/products/{self.product.pk}/price-context/",
            {"province": "Kinshasa"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["record_count"], 1)
        self.assertIn("avg_price", response.data)
        self.assertIn("last_recorded_at", response.data)
