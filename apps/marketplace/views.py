from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.accounts.views import IsBuyer, IsProducerOrSupplier

from .mixins import BuyerRequiredMixin, ProducerOrSupplierRequiredMixin
from .forms import OfferForm, OrderForm, PurchaseRequestForm
from .models import Offer, Order, PurchaseRequest
from .permissions import IsOfferOwner, IsOrderSeller, IsPurchaseRequestOwner
from .serializers import OfferSerializer, OrderSerializer, PurchaseRequestSerializer
from .services.matching import MatchingService
from .services.notifications import NotificationService
from .services.orders import OrderService
from apps.prices.services.price_context import PriceContextService


class OfferViewSet(viewsets.ModelViewSet):
    serializer_class = OfferSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "title",
        "description",
        "product__name",
        "city",
        "province",
    ]
    ordering_fields = [
        "created_at",
        "unit_price",
        "quantity",
    ]

    def get_queryset(self):
        queryset = Offer.objects.select_related("producer", "product").all()

        status_value = self.request.query_params.get("status")
        province = self.request.query_params.get("province")
        city = self.request.query_params.get("city")
        product = self.request.query_params.get("product")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")

        if status_value:
            queryset = queryset.filter(status=status_value)
        if province:
            queryset = queryset.filter(province__icontains=province)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if product:
            queryset = queryset.filter(product_id=product)
        if min_price:
            queryset = queryset.filter(unit_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(unit_price__lte=max_price)

        return queryset

    def perform_create(self, serializer):
        offer = serializer.save(producer=self.request.user)
        NotificationService.notify_matches_for_offer(offer)

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsProducerOrSupplier()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [
                permissions.IsAuthenticated(),
                IsProducerOrSupplier(),
                IsOfferOwner(),
            ]
        return [permissions.AllowAny()]

    @action(detail=True, methods=["get"], url_path="matching-requests")
    def matching_requests(self, request, pk=None):
        offer = self.get_object()
        matches = MatchingService.get_top_matches_for_offer(offer, limit=10)

        data = [
            {
                "id": purchase_request.id,
                "product": purchase_request.product.name,
                "buyer": purchase_request.buyer.username,
                "quantity": str(purchase_request.quantity),
                "unit": purchase_request.unit,
                "target_price": str(purchase_request.target_price),
                "currency": purchase_request.currency,
                "city": purchase_request.city,
                "province": purchase_request.province,
                "match_score": score,
            }
            for purchase_request, score in matches
        ]
        return Response(data)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.select_related(
            "buyer",
            "offer",
            "offer__product",
            "offer__producer",
        )

        if user.is_staff:
            return queryset.all()

        return queryset.filter(
            Q(buyer=user) | Q(offer__producer=user)
        )

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsBuyer()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        order = serializer.save(buyer=self.request.user)
        NotificationService.notify_new_order(order)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsOrderSeller])
    def accept(self, request, pk=None):
        order = self.get_object()
        try:
            OrderService.accept(order, request.user)
        except PermissionDenied as exc:
            return Response({"error": str(exc.detail)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as exc:
            return Response({"error": exc.detail}, status=status.HTTP_400_BAD_REQUEST)

        NotificationService.notify_order_accepted(order)
        return Response(
            {"message": "Commande acceptée", "status": order.status},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsOrderSeller])
    def reject(self, request, pk=None):
        order = self.get_object()
        try:
            OrderService.reject(order, request.user)
        except PermissionDenied as exc:
            return Response({"error": str(exc.detail)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as exc:
            return Response({"error": exc.detail}, status=status.HTTP_400_BAD_REQUEST)

        NotificationService.notify_order_rejected(order)
        return Response(
            {"message": "Commande refusée", "status": order.status},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsOrderSeller])
    def complete(self, request, pk=None):
        order = self.get_object()
        try:
            OrderService.complete(order, request.user)
        except PermissionDenied as exc:
            return Response({"error": str(exc.detail)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as exc:
            return Response({"error": exc.detail}, status=status.HTTP_400_BAD_REQUEST)

        NotificationService.notify_order_completed(order)
        return Response(
            {"message": "Commande terminée", "status": order.status},
            status=status.HTTP_200_OK,
        )


class PurchaseRequestViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseRequestSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "product__name",
        "city",
        "province",
        "description",
    ]
    ordering_fields = [
        "created_at",
        "target_price",
        "quantity",
    ]

    def get_queryset(self):
        queryset = PurchaseRequest.objects.select_related("buyer", "product").all()

        status_value = self.request.query_params.get("status")
        province = self.request.query_params.get("province")
        city = self.request.query_params.get("city")
        product = self.request.query_params.get("product")

        if status_value:
            queryset = queryset.filter(status=status_value)
        if province:
            queryset = queryset.filter(province__icontains=province)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if product:
            queryset = queryset.filter(product_id=product)

        return queryset

    def perform_create(self, serializer):
        purchase_request = serializer.save(buyer=self.request.user)
        NotificationService.notify_matches_for_request(purchase_request)

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsBuyer()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [
                permissions.IsAuthenticated(),
                IsBuyer(),
                IsPurchaseRequestOwner(),
            ]
        return [permissions.AllowAny()]

    @action(detail=True, methods=["get"], url_path="matching-offers")
    def matching_offers(self, request, pk=None):
        purchase_request = self.get_object()
        matches = MatchingService.get_top_matches_for_request(purchase_request, limit=10)

        data = [
            {
                "id": offer.id,
                "title": offer.title,
                "product": offer.product.name,
                "producer": offer.producer.username,
                "quantity": str(offer.quantity),
                "unit": offer.unit,
                "unit_price": str(offer.unit_price),
                "currency": offer.currency,
                "city": offer.city,
                "province": offer.province,
                "match_score": score,
            }
            for offer, score in matches
        ]
        return Response(data)


class OfferListView(ListView):
    model = Offer
    template_name = "offers/list.html"
    context_object_name = "offers"

    def get_queryset(self):
        return (
            Offer.objects.select_related("product", "producer")
            .order_by("-created_at")
        )


class OfferDetailView(DetailView):
    model = Offer
    template_name = "offers/detail.html"
    context_object_name = "offer"

    def get_queryset(self):
        return Offer.objects.select_related("product", "producer")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offer = self.object
        context["matching_requests"] = MatchingService.get_top_matches_for_offer(
            offer, limit=5
        )
        context["order_form"] = OrderForm(offer=offer)
        context["price_context"] = PriceContextService.get_context(
            product_id=offer.product_id,
            province=offer.province,
        )
        return context


class PurchaseRequestListView(ListView):
    model = PurchaseRequest
    template_name = "requests/list.html"
    context_object_name = "requests"

    def get_queryset(self):
        return (
            PurchaseRequest.objects.select_related("product", "buyer")
            .order_by("-created_at")
        )


class PurchaseRequestDetailView(DetailView):
    model = PurchaseRequest
    template_name = "requests/detail.html"
    context_object_name = "purchase_request"

    def get_queryset(self):
        return PurchaseRequest.objects.select_related("product", "buyer")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["matching_offers"] = MatchingService.get_top_matches_for_request(
            self.object, limit=5
        )
        context["price_context"] = PriceContextService.get_context(
            product_id=self.object.product_id,
            province=self.object.province,
        )
        return context


class OfferCreateView(ProducerOrSupplierRequiredMixin, CreateView):
    model = Offer
    form_class = OfferForm
    template_name = "offers/create.html"
    success_url = reverse_lazy("offers")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.request.POST.get("product")
        province = self.request.POST.get("province")
        if product_id and province:
            context["price_context"] = PriceContextService.get_context(
                product_id=product_id,
                province=province,
            )
        return context

    def form_valid(self, form):
        offer = form.save(commit=False)
        offer.producer = self.request.user
        offer.save()
        NotificationService.notify_matches_for_offer(offer)
        messages.success(self.request, "Offre publiée avec succès.")
        return redirect(self.success_url)


class PurchaseRequestCreateView(BuyerRequiredMixin, CreateView):
    model = PurchaseRequest
    form_class = PurchaseRequestForm
    template_name = "requests/create.html"
    success_url = reverse_lazy("requests")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.request.POST.get("product")
        province = self.request.POST.get("province")
        if product_id and province:
            context["price_context"] = PriceContextService.get_context(
                product_id=product_id,
                province=province,
            )
        return context

    def form_valid(self, form):
        purchase_request = form.save(commit=False)
        purchase_request.buyer = self.request.user
        purchase_request.save()
        NotificationService.notify_matches_for_request(purchase_request)
        messages.success(self.request, "Demande publiée avec succès.")
        return redirect(self.success_url)


class OfferOrderCreateView(BuyerRequiredMixin, View):
    def post(self, request, pk):
        offer = get_object_or_404(
            Offer.objects.select_related("product", "producer"),
            pk=pk,
        )

        form = OrderForm(request.POST, offer=offer)
        if not form.is_valid():
            messages.error(request, "Impossible de passer la commande.")
            return redirect("offer-detail", pk=pk)

        try:
            OrderService.validate_create(
                offer=offer,
                quantity=form.cleaned_data["quantity"],
                buyer=request.user,
            )
        except ValidationError as exc:
            detail = exc.detail
            message = detail[0] if isinstance(detail, list) else detail
            messages.error(request, str(message))
            return redirect("offer-detail", pk=pk)

        order = form.save(commit=False)
        order.offer = offer
        order.buyer = request.user
        order.save()
        NotificationService.notify_new_order(order)
        messages.success(request, "Commande enregistrée avec succès.")
        return redirect("my-orders")


class OrderActionView(ProducerOrSupplierRequiredMixin, View):
    action_name = None

    def post(self, request, pk):
        order = get_object_or_404(
            Order.objects.select_related("offer", "offer__producer", "buyer"),
            pk=pk,
            offer__producer=request.user,
        )

        action_handlers = {
            "accept": (OrderService.accept, NotificationService.notify_order_accepted),
            "reject": (OrderService.reject, NotificationService.notify_order_rejected),
            "complete": (
                OrderService.complete,
                NotificationService.notify_order_completed,
            ),
        }

        handler, notifier = action_handlers[self.action_name]

        try:
            handler(order, request.user)
        except PermissionDenied as exc:
            messages.error(request, str(exc.detail))
            return redirect("my-offers")
        except ValidationError as exc:
            detail = exc.detail
            message = detail[0] if isinstance(detail, list) else detail
            messages.error(request, str(message))
            return redirect("my-offers")

        notifier(order)
        messages.success(request, "Commande mise à jour.")
        return redirect("my-offers")


class OrderAcceptView(OrderActionView):
    action_name = "accept"


class OrderRejectView(OrderActionView):
    action_name = "reject"


class OrderCompleteView(OrderActionView):
    action_name = "complete"


class MyOffersListView(ProducerOrSupplierRequiredMixin, ListView):
    model = Offer
    template_name = "marketplace/my_offers.html"
    context_object_name = "offers"

    def get_queryset(self):
        return (
            Offer.objects.select_related("product", "producer")
            .prefetch_related("orders__buyer")
            .filter(producer=self.request.user)
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["received_orders"] = (
            Order.objects.select_related(
                "buyer",
                "offer",
                "offer__product",
            )
            .filter(offer__producer=self.request.user)
            .order_by("-created_at")
        )
        return context


class MyRequestsListView(BuyerRequiredMixin, ListView):
    model = PurchaseRequest
    template_name = "marketplace/my_requests.html"
    context_object_name = "requests"

    def get_queryset(self):
        return (
            PurchaseRequest.objects.select_related("product", "buyer")
            .filter(buyer=self.request.user)
            .order_by("-created_at")
        )


class MyOrdersListView(BuyerRequiredMixin, ListView):
    model = Order
    template_name = "marketplace/my_orders.html"
    context_object_name = "orders"

    def get_queryset(self):
        return (
            Order.objects.select_related(
                "buyer",
                "offer",
                "offer__product",
                "offer__producer",
            )
            .filter(buyer=self.request.user)
            .order_by("-created_at")
        )
