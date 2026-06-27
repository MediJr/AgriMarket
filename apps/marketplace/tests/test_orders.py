from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import Category, Product
from apps.marketplace.models import Offer, Order, PurchaseRequest
from apps.marketplace.services.orders import OrderService
from apps.notifications.models import Notification


class OrderServiceTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Légumes", slug="legumes")
        self.product = Product.objects.create(
            name="Tomate",
            slug="tomate",
            category=category,
        )
        self.producer = User.objects.create_user(
            username="seller",
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
            title="Tomates fraîches",
            quantity=Decimal("100"),
            unit="kg",
            unit_price=Decimal("300"),
            city="Lubumbashi",
            province="Haut-Katanga",
        )
        self.order = Order.objects.create(
            buyer=self.buyer,
            offer=self.offer,
            quantity=Decimal("20"),
        )

    def test_validate_create_rejects_excessive_quantity(self):
        with self.assertRaises(ValidationError):
            OrderService.validate_create(
                offer=self.offer,
                quantity=Decimal("500"),
                buyer=self.buyer,
            )

    def test_validate_create_accounts_for_pending_orders(self):
        Order.objects.create(
            buyer=self.buyer,
            offer=self.offer,
            quantity=Decimal("80"),
        )
        with self.assertRaises(ValidationError):
            OrderService.validate_create(
                offer=self.offer,
                quantity=Decimal("30"),
                buyer=self.buyer,
            )

    def test_accept_transition_updates_offer_status(self):
        OrderService.accept(self.order, self.producer)
        self.order.refresh_from_db()
        self.offer.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.ACCEPTED)
        self.assertEqual(self.offer.status, Offer.Status.RESERVED)

    def test_complete_transition_marks_offer_sold(self):
        OrderService.accept(self.order, self.producer)
        OrderService.complete(self.order, self.producer)
        self.order.refresh_from_db()
        self.offer.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.COMPLETED)
        self.assertEqual(self.offer.status, Offer.Status.SOLD)

    def test_invalid_transition_rejected(self):
        with self.assertRaises(ValidationError):
            OrderService.complete(self.order, self.producer)


class OrderAPITests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Fruits", slug="fruits")
        self.product = Product.objects.create(
            name="Banane",
            slug="banane",
            category=category,
        )
        self.producer = User.objects.create_user(
            username="seller2",
            password="testpass123",
            role=User.Role.PRODUCER,
        )
        self.buyer = User.objects.create_user(
            username="buyer2",
            password="testpass123",
            role=User.Role.BUYER,
        )
        self.offer = Offer.objects.create(
            producer=self.producer,
            product=self.product,
            title="Bananes",
            quantity=Decimal("50"),
            unit="kg",
            unit_price=Decimal("400"),
            city="Goma",
            province="Nord-Kivu",
        )
        self.client = APIClient()

    def test_buyer_can_create_order_and_notify_seller(self):
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(
            "/api/orders/",
            {"offer": self.offer.pk, "quantity": "10", "note": "Livraison rapide"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Notification.objects.filter(user=self.producer, title__icontains="commande").exists()
        )

    def test_seller_can_accept_order_via_api(self):
        order = Order.objects.create(
            buyer=self.buyer,
            offer=self.offer,
            quantity=Decimal("5"),
        )
        self.client.force_authenticate(user=self.producer)
        response = self.client.post(f"/api/orders/{order.pk}/accept/")
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.ACCEPTED)

    def test_matching_requests_endpoint(self):
        PurchaseRequest.objects.create(
            buyer=self.buyer,
            product=self.product,
            quantity=Decimal("10"),
            unit="kg",
            target_price=Decimal("500"),
            city="Goma",
            province="Nord-Kivu",
        )
        response = self.client.get(f"/api/offers/{self.offer.pk}/matching-requests/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_producer_cannot_create_order(self):
        self.client.force_authenticate(user=self.producer)
        response = self.client.post(
            "/api/orders/",
            {"offer": self.offer.pk, "quantity": "10"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
