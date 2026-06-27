from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import Category, Product
from apps.marketplace.models import Offer, Order, PurchaseRequest
from apps.marketplace.services.matching import MatchingService
from apps.marketplace.services.orders import OrderService
from apps.notifications.models import Notification


class MVPFlowTests(TestCase):
    """Parcours bout-en-bout du MVP."""

    def setUp(self):
        category = Category.objects.create(name="Céréales", slug="cereales-flow")
        self.product = Product.objects.create(
            name="Maïs",
            slug="mais-flow",
            category=category,
        )
        self.producer = User.objects.create_user(
            username="flow_producer",
            password="testpass123",
            role=User.Role.PRODUCER,
        )
        self.buyer = User.objects.create_user(
            username="flow_buyer",
            password="testpass123",
            role=User.Role.BUYER,
        )
        self.client = APIClient()

    def test_full_mvp_flow(self):
        self.client.force_authenticate(user=self.producer)
        offer_response = self.client.post(
            "/api/offers/",
            {
                "product": self.product.pk,
                "title": "Maïs flow",
                "quantity": "100",
                "unit": "kg",
                "unit_price": "500",
                "currency": "CDF",
                "city": "Kinshasa",
                "province": "Kinshasa",
            },
            format="json",
        )
        self.assertEqual(offer_response.status_code, 201)
        offer_id = offer_response.data["id"]

        self.client.force_authenticate(user=self.buyer)
        request_response = self.client.post(
            "/api/purchase-requests/",
            {
                "product": self.product.pk,
                "quantity": "50",
                "unit": "kg",
                "target_price": "600",
                "currency": "CDF",
                "city": "Kinshasa",
                "province": "Kinshasa",
            },
            format="json",
        )
        self.assertEqual(request_response.status_code, 201)

        match_response = self.client.get(
            f"/api/offers/{offer_id}/matching-requests/"
        )
        self.assertEqual(match_response.status_code, 200)
        self.assertGreaterEqual(len(match_response.data), 1)

        order_response = self.client.post(
            "/api/orders/",
            {"offer": offer_id, "quantity": "10"},
            format="json",
        )
        self.assertEqual(order_response.status_code, 201)
        order_id = order_response.data["id"]

        self.client.force_authenticate(user=self.producer)
        accept_response = self.client.post(f"/api/orders/{order_id}/accept/")
        self.assertEqual(accept_response.status_code, 200)

        self.assertTrue(
            Notification.objects.filter(
                user=self.producer,
                title__icontains="commande",
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                user=self.buyer,
                title__icontains="acceptée",
            ).exists()
        )

        price_response = self.client.get(
            f"/api/products/{self.product.pk}/price-context/",
            {"province": "Kinshasa"},
        )
        self.assertEqual(price_response.status_code, 200)

        observatory = self.client.get(reverse("observatory"))
        self.assertEqual(observatory.status_code, 200)


class OrderSecurityTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Fruits", slug="fruits-sec")
        product = Product.objects.create(
            name="Banane",
            slug="banane-sec",
            category=category,
        )
        self.producer = User.objects.create_user(
            username="sec_producer",
            password="testpass123",
            role=User.Role.PRODUCER,
        )
        self.buyer = User.objects.create_user(
            username="sec_buyer",
            password="testpass123",
            role=User.Role.BUYER,
        )
        self.offer = Offer.objects.create(
            producer=self.producer,
            product=product,
            title="Bananes",
            quantity=Decimal("50"),
            unit="kg",
            unit_price=Decimal("400"),
            city="Goma",
            province="Nord-Kivu",
        )
        self.order = Order.objects.create(
            buyer=self.buyer,
            offer=self.offer,
            quantity=Decimal("5"),
        )
        self.client = APIClient()

    def test_buyer_cannot_accept_order(self):
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(f"/api/orders/{self.order.pk}/accept/")
        self.assertEqual(response.status_code, 403)

    def test_self_order_forbidden(self):
        with self.assertRaises(ValidationError):
            OrderService.validate_create(
                offer=self.offer,
                quantity=Decimal("1"),
                buyer=self.producer,
            )

    def test_weak_match_excluded(self):
        category = Category.objects.create(name="Tubercules", slug="tubercules")
        product = Product.objects.create(
            name="Manioc",
            slug="manioc",
            category=category,
        )
        offer = Offer.objects.create(
            producer=self.producer,
            product=product,
            title="Manioc",
            quantity=Decimal("100"),
            unit="kg",
            unit_price=Decimal("200"),
            city="Kinshasa",
            province="Kinshasa",
        )
        request = PurchaseRequest.objects.create(
            buyer=self.buyer,
            product=product,
            quantity=Decimal("200"),
            unit="kg",
            target_price=Decimal("100"),
            city="Lubumbashi",
            province="Haut-Katanga",
        )
        score = MatchingService.calculate_match_score(offer, request)
        self.assertEqual(score, 40)
        self.assertEqual(MatchingService.find_matching_requests(offer), [])


class WebNotificationsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notif_user",
            password="testpass123",
            role=User.Role.BUYER,
        )
        Notification.objects.create(
            user=self.user,
            title="Test",
            body="Message test",
        )

    def test_notifications_page_requires_login(self):
        response = self.client.get(reverse("my-notifications"))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_sees_notifications(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("my-notifications"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test")


class RegisterRoleTests(TestCase):
    def test_api_register_rejects_admin_role(self):
        client = APIClient()
        response = client.post(
            "/api/auth/register/",
            {
                "username": "evil_admin",
                "email": "evil@example.com",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
                "role": "admin",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username="evil_admin").exists())
