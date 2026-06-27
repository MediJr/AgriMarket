"""
Service de contexte prix pour AgriMarket.

Fournit des agrégats à partir des relevés validés uniquement.
Indépendant des vues — consommé par marketplace et catalog.
"""

from django.db.models import Avg, Count, Max, Min

from apps.prices.models import PriceRecord


class PriceContextService:
    @staticmethod
    def get_context(*, product_id, province=None):
        queryset = PriceRecord.objects.filter(
            is_validated=True,
            product_id=product_id,
        ).select_related("market", "product")

        if province:
            queryset = queryset.filter(market__province__iexact=province.strip())

        aggregates = queryset.aggregate(
            avg_price=Avg("price"),
            min_price=Min("price"),
            max_price=Max("price"),
            record_count=Count("id"),
            last_recorded_at=Max("recorded_at"),
        )

        if not aggregates["record_count"]:
            return {
                "product_id": product_id,
                "province": province,
                "avg_price": None,
                "min_price": None,
                "max_price": None,
                "record_count": 0,
                "last_recorded_at": None,
                "currency": "CDF",
                "unit": "kg",
            }

        sample = queryset.order_by("-recorded_at").first()

        return {
            "product_id": product_id,
            "province": province,
            "avg_price": aggregates["avg_price"],
            "min_price": aggregates["min_price"],
            "max_price": aggregates["max_price"],
            "record_count": aggregates["record_count"],
            "last_recorded_at": aggregates["last_recorded_at"],
            "currency": sample.currency if sample else "CDF",
            "unit": sample.unit if sample else "kg",
        }

    @staticmethod
    def get_observatory_summary():
        return (
            PriceRecord.objects.filter(is_validated=True)
            .select_related("product", "market")
            .values(
                "product__name",
                "product__id",
                "market__province",
            )
            .annotate(
                avg_price=Avg("price"),
                min_price=Min("price"),
                max_price=Max("price"),
                record_count=Count("id"),
                last_recorded_at=Max("recorded_at"),
            )
            .order_by("product__name", "market__province")
        )
