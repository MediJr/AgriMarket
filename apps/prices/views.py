from django.db.models import Avg, Max, Min
from rest_framework import decorators, filters, permissions, response, viewsets

from .models import Market, PriceRecord
from .serializers import MarketSerializer, PriceRecordSerializer


class MarketViewSet(viewsets.ModelViewSet):
    queryset = Market.objects.all()
    serializer_class = MarketSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "city", "province"]
    ordering_fields = ["name", "city", "province"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


class PriceRecordViewSet(viewsets.ModelViewSet):
    serializer_class = PriceRecordSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["product__name", "market__name", "market__city", "market__province"]
    ordering_fields = ["recorded_at", "price"]

    def get_queryset(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            queryset = PriceRecord.objects.select_related(
                "product", "market", "collector"
            )
        else:
            queryset = PriceRecord.objects.filter(is_validated=True).select_related(
                "product", "market", "collector"
            )

        product = self.request.query_params.get("product")
        market = self.request.query_params.get("market")
        province = self.request.query_params.get("province")
        if product:
            queryset = queryset.filter(product_id=product)
        if market:
            queryset = queryset.filter(market_id=market)
        if province:
            queryset = queryset.filter(market__province__icontains=province)
        return queryset

    def perform_create(self, serializer):
        serializer.save(collector=self.request.user if self.request.user.is_authenticated else None)

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @decorators.action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def summary(self, request):
        queryset = self.get_queryset()
        data = (
            queryset.values("product__name", "market__province")
            .annotate(avg_price=Avg("price"), min_price=Min("price"), max_price=Max("price"))
            .order_by("product__name", "market__province")
        )
        return response.Response(list(data))
