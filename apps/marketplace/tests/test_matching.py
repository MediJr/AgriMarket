from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.catalog.models import Category, Product
from apps.marketplace.models import Offer, PurchaseRequest
from apps.marketplace.services.matching import MatchingService


class MatchingServiceTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Céréales", slug="cereales")
        self.product = Product.objects.create(
            name="Maïs",
            slug="mais",
            category=category,
        )
        self.producer = User.objects.create_user(
            username="producer",
            password="testpass123",
            role=User.Role.PRODUCER,
        )
        self.buyer = User.objects.create_user(
            username="buyer",
            password="testpass123",
            role=User.Role.BUYER,
        )
        self.offer = Offer.objects.create(
            producer=self.producer,
            product=self.product,
            title="Maïs Kinshasa",
            quantity=Decimal("100"),
            unit="kg",
            unit_price=Decimal("500"),
            city="Kinshasa",
            province="Kinshasa",
        )
        self.request = PurchaseRequest.objects.create(
            buyer=self.buyer,
            product=self.product,
            quantity=Decimal("50"),
            unit="kg",
            target_price=Decimal("600"),
            city="Kinshasa",
            province="Kinshasa",
        )

    def test_perfect_match_score(self):
        score = MatchingService.calculate_match_score(self.offer, self.request)
        self.assertEqual(score, 100)

    def test_find_matching_requests_for_offer(self):
        matches = MatchingService.find_matching_requests(self.offer)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], self.request)
        self.assertEqual(matches[0][1], 100)

    def test_find_matching_offers_for_request(self):
        matches = MatchingService.find_matching_offers(self.request)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], self.offer)

    def test_inactive_offer_excluded(self):
        self.offer.status = Offer.Status.WITHDRAWN
        self.offer.save()
        matches = MatchingService.find_matching_requests(self.offer)
        self.assertEqual(matches, [])
