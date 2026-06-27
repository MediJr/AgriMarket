"""
Service de notifications pour AgriMarket.

Centralise la création de notifications en réutilisant l'application notifications.
"""

from apps.notifications.models import Notification


class NotificationService:
    @staticmethod
    def create_notification(user, title, body, channel=Notification.Channel.IN_APP):
        Notification.objects.create(
            user=user,
            title=title,
            body=body,
            channel=channel,
        )

    @staticmethod
    def notify_match_for_offer(offer, purchase_request, score):
        """Notifie l'acheteur qu'une offre correspond à sa demande."""
        NotificationService.create_notification(
            user=purchase_request.buyer,
            title="Nouvelle offre compatible avec votre demande",
            body=(
                f"L'offre « {offer.title} » de {offer.producer.username} "
                f"correspond à votre demande pour {purchase_request.product.name} "
                f"(score {score}/100)."
            ),
        )

    @staticmethod
    def notify_match_for_request(offer, purchase_request, score):
        """Notifie le vendeur qu'une demande correspond à son offre."""
        NotificationService.create_notification(
            user=offer.producer,
            title="Nouvelle demande compatible avec votre offre",
            body=(
                f"La demande de {purchase_request.buyer.username} pour "
                f"{purchase_request.product.name} correspond à votre offre "
                f"« {offer.title} » (score {score}/100)."
            ),
        )

    @staticmethod
    def notify_matches_for_offer(offer, limit=5, min_score=None):
        from apps.marketplace.services.matching import MatchingService

        threshold = min_score or MatchingService.MIN_MATCH_SCORE
        for purchase_request, score in MatchingService.get_top_matches_for_offer(
            offer, limit=limit
        ):
            if score >= threshold:
                NotificationService.notify_match_for_offer(
                    offer, purchase_request, score
                )

    @staticmethod
    def notify_matches_for_request(purchase_request, limit=5, min_score=None):
        from apps.marketplace.services.matching import MatchingService

        threshold = min_score or MatchingService.MIN_MATCH_SCORE
        for offer, score in MatchingService.get_top_matches_for_request(
            purchase_request, limit=limit
        ):
            if score >= threshold:
                NotificationService.notify_match_for_request(
                    offer, purchase_request, score
                )

    @staticmethod
    def notify_new_order(order):
        NotificationService.create_notification(
            user=order.offer.producer,
            title="Nouvelle commande reçue",
            body=(
                f"Commande #{order.pk} de {order.buyer.username} pour "
                f"{order.offer.product.name} "
                f"({order.quantity} {order.offer.unit})."
            ),
        )
        NotificationService.create_notification(
            user=order.buyer,
            title="Commande enregistrée",
            body=(
                f"Votre commande #{order.pk} pour {order.offer.product.name} "
                f"est en attente de validation par le vendeur."
            ),
        )

    @staticmethod
    def notify_order_accepted(order):
        NotificationService.create_notification(
            user=order.buyer,
            title="Commande acceptée",
            body=(
                f"Votre commande #{order.pk} pour {order.offer.product.name} "
                f"a été acceptée par {order.offer.producer.username}."
            ),
        )

    @staticmethod
    def notify_order_rejected(order):
        NotificationService.create_notification(
            user=order.buyer,
            title="Commande refusée",
            body=(
                f"Votre commande #{order.pk} pour {order.offer.product.name} "
                f"a été refusée par {order.offer.producer.username}."
            ),
        )

    @staticmethod
    def notify_order_completed(order):
        NotificationService.create_notification(
            user=order.buyer,
            title="Commande terminée",
            body=(
                f"Votre commande #{order.pk} pour {order.offer.product.name} "
                f"est terminée."
            ),
        )
        NotificationService.create_notification(
            user=order.offer.producer,
            title="Commande clôturée",
            body=(
                f"La commande #{order.pk} pour {order.offer.product.name} "
                f"est terminée."
            ),
        )
