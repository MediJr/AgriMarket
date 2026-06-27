"""
Service de matching pour AgriMarket.

Ce service est indépendant des vues et contient toute la logique métier
de mise en relation entre offres et demandes d'achat.

Le score de compatibilité est calculé selon les critères suivants :
- Même produit : 40 points
- Même province : 20 points
- Même ville : 10 points (bonus en plus de la province)
- Quantité compatible (offre >= demande) : 15 points
- Prix compatible (offre <= demande) : 15 points
- Statut compatible (offre active, demande ouverte) : requis

Score maximum : 100 points
"""

from apps.marketplace.models import Offer, PurchaseRequest


class MatchingService:
    """
    Service de matching entre offres et demandes d'achat.
    """

    SCORE_PRODUCT = 40
    SCORE_PROVINCE = 20
    SCORE_CITY = 10
    SCORE_QUANTITY = 15
    SCORE_PRICE = 15
    MIN_MATCH_SCORE = 55

    @staticmethod
    def calculate_match_score(offer: Offer, request: PurchaseRequest) -> int:
        """
        Calcule le score de compatibilité entre une offre et une demande.
        Retourne 0 si le produit ne correspond pas.
        """
        if offer.product_id != request.product_id:
            return 0

        if offer.status != Offer.Status.ACTIVE:
            return 0

        if request.status != PurchaseRequest.Status.OPEN:
            return 0

        score = MatchingService.SCORE_PRODUCT

        if offer.province.lower().strip() == request.province.lower().strip():
            score += MatchingService.SCORE_PROVINCE
            if offer.city.lower().strip() == request.city.lower().strip():
                score += MatchingService.SCORE_CITY

        if offer.quantity >= request.quantity:
            score += MatchingService.SCORE_QUANTITY

        if offer.unit_price <= request.target_price:
            score += MatchingService.SCORE_PRICE

        return score

    @staticmethod
    def find_matching_requests(offer: Offer) -> list:
        """
        Trouve les demandes d'achat compatibles avec une offre.

        Args:
            offer: L'offre pour laquelle chercher des demandes compatibles

        Returns:
            Liste de tuples (request, score) triés par score décroissant
        """
        if offer.status != Offer.Status.ACTIVE:
            return []

        matching_requests = []

        # Récupérer toutes les demandes ouvertes du même produit
        requests = PurchaseRequest.objects.filter(
            product=offer.product,
            status=PurchaseRequest.Status.OPEN
        ).select_related("buyer", "product")

        for request in requests:
            score = MatchingService.calculate_match_score(offer, request)
            if score >= MatchingService.MIN_MATCH_SCORE:
                matching_requests.append((request, score))

        matching_requests.sort(key=lambda x: x[1], reverse=True)
        return matching_requests

    @staticmethod
    def find_matching_offers(request: PurchaseRequest) -> list:
        """
        Trouve les offres compatibles avec une demande d'achat.

        Args:
            request: La demande d'achat pour laquelle chercher des offres compatibles

        Returns:
            Liste de tuples (offer, score) triés par score décroissant
        """
        if request.status != PurchaseRequest.Status.OPEN:
            return []

        matching_offers = []

        # Récupérer toutes les offres actives du même produit
        offers = Offer.objects.filter(
            product=request.product,
            status=Offer.Status.ACTIVE
        ).select_related("producer", "product")

        for offer in offers:
            score = MatchingService.calculate_match_score(offer, request)
            if score >= MatchingService.MIN_MATCH_SCORE:
                matching_offers.append((offer, score))

        matching_offers.sort(key=lambda x: x[1], reverse=True)
        return matching_offers

    @staticmethod
    def get_top_matches_for_offer(offer: Offer, limit: int = 10) -> list:
        """
        Retourne les N meilleures demandes compatibles avec une offre.

        Args:
            offer: L'offre pour laquelle chercher des demandes
            limit: Nombre maximum de résultats à retourner

        Returns:
            Liste des N meilleures demandes avec leur score
        """
        matches = MatchingService.find_matching_requests(offer)
        return matches[:limit]

    @staticmethod
    def get_top_matches_for_request(request: PurchaseRequest, limit: int = 10) -> list:
        """
        Retourne les N meilleures offres compatibles avec une demande.

        Args:
            request: La demande pour laquelle chercher des offres
            limit: Nombre maximum de résultats à retourner

        Returns:
            Liste des N meilleures offres avec leur score
        """
        matches = MatchingService.find_matching_offers(request)
        return matches[:limit]
