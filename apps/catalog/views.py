from django.views.generic import DetailView, ListView, TemplateView
from rest_framework import filters, permissions, response, viewsets
from rest_framework.decorators import action

from apps.prices.services.price_context import PriceContextService

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


class ProductListView(ListView):
    model = Product
    template_name = "products/list.html"
    context_object_name = "products"


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name"]

    def get_permissions(self):
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            return [permissions.IsAdminUser()]

        return [permissions.AllowAny()]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "name",
        "description",
        "category__name",
    ]
    ordering_fields = [
        "name",
        "created_at",
    ]

    def perform_create(self, serializer):
        serializer.save(
            created_by=(
                self.request.user
                if self.request.user.is_authenticated
                else None
            )
        )

    def get_permissions(self):
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny()]

    @action(detail=True, methods=["get"], url_path="price-context")
    def price_context(self, request, pk=None):
        product = self.get_object()
        province = request.query_params.get("province")
        data = PriceContextService.get_context(
            product_id=product.pk,
            province=province,
        )
        return response.Response(data)


class ObservatoryView(TemplateView):
    template_name = "observatory/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summaries"] = PriceContextService.get_observatory_summary()
        return context