"""
Transitions métier des commandes.

Centralise la logique partagée entre l'API et les vues web.
"""

from django.db.models import Sum
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.marketplace.models import Offer, Order


class OrderService:
    ALLOWED_TRANSITIONS = {
        Order.Status.PENDING: {Order.Status.ACCEPTED, Order.Status.CANCELLED},
        Order.Status.ACCEPTED: {Order.Status.COMPLETED, Order.Status.CANCELLED},
    }

    @staticmethod
    def validate_create(*, offer, quantity, buyer):
        if buyer.role != buyer.Role.BUYER and not buyer.is_staff:
            raise ValidationError("Seuls les acheteurs peuvent passer commande.")

        if offer.status != Offer.Status.ACTIVE:
            raise ValidationError("Cette offre n'est plus active.")

        if offer.producer == buyer:
            raise ValidationError("Vous ne pouvez pas commander votre propre offre.")

        if quantity <= 0:
            raise ValidationError("La quantité doit être supérieure à zéro.")

        reserved = (
            Order.objects.filter(
                offer=offer,
                status__in=[Order.Status.PENDING, Order.Status.ACCEPTED],
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )
        available = offer.quantity - reserved
        if quantity > available:
            raise ValidationError(
                "La quantité demandée dépasse la quantité disponible."
            )

    @staticmethod
    def _ensure_seller(order, user):
        if order.offer.producer != user and not user.is_staff:
            raise PermissionDenied("Seul le vendeur peut gérer cette commande.")

    @staticmethod
    def _transition(order, *, expected_status, new_status, user):
        OrderService._ensure_seller(order, user)

        if order.status != expected_status:
            raise ValidationError(
                f"Transition invalide : statut actuel « {order.status} »."
            )

        allowed = OrderService.ALLOWED_TRANSITIONS.get(expected_status, set())
        if new_status not in allowed:
            raise ValidationError("Transition de statut non autorisée.")

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        return order

    @staticmethod
    def accept(order, user):
        order = OrderService._transition(
            order,
            expected_status=Order.Status.PENDING,
            new_status=Order.Status.ACCEPTED,
            user=user,
        )
        offer = order.offer
        if offer.status == Offer.Status.ACTIVE:
            offer.status = Offer.Status.RESERVED
            offer.save(update_fields=["status", "updated_at"])
        return order

    @staticmethod
    def reject(order, user):
        return OrderService._transition(
            order,
            expected_status=Order.Status.PENDING,
            new_status=Order.Status.CANCELLED,
            user=user,
        )

    @staticmethod
    def complete(order, user):
        order = OrderService._transition(
            order,
            expected_status=Order.Status.ACCEPTED,
            new_status=Order.Status.COMPLETED,
            user=user,
        )
        offer = order.offer
        offer.status = Offer.Status.SOLD
        offer.save(update_fields=["status", "updated_at"])
        return order
