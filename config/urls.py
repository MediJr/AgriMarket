from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.accounts.views import (
    CustomLoginView,
    CustomLogoutView,
    ProfileViewSet,
    RegisterView,
    UserViewSet,
    register_view,
)

from apps.catalog.views import (
    CategoryViewSet,
    ProductViewSet,
    ProductListView,
    ProductDetailView,
    ObservatoryView,
)

from apps.marketplace.views import (
    OfferViewSet,
    OrderViewSet,
    PurchaseRequestViewSet,
    OfferListView,
    OfferDetailView,
    OfferCreateView,
    OfferOrderCreateView,
    OrderAcceptView,
    OrderRejectView,
    OrderCompleteView,
    PurchaseRequestListView,
    PurchaseRequestDetailView,
    PurchaseRequestCreateView,
    MyOffersListView,
    MyRequestsListView,
    MyOrdersListView,
)

from apps.notifications.views import MyNotificationsListView, NotificationViewSet

from apps.prices.views import (
    MarketViewSet,
    PriceRecordViewSet,
)


router = DefaultRouter()

router.register(
    "users",
    UserViewSet,
    basename="user"
)

router.register(
    "profiles",
    ProfileViewSet,
    basename="profile"
)

router.register(
    "categories",
    CategoryViewSet,
    basename="category"
)

router.register(
    "products",
    ProductViewSet,
    basename="product"
)

router.register(
    "offers",
    OfferViewSet,
    basename="offer"
)

router.register(
    "orders",
    OrderViewSet,
    basename="order"
)

router.register(
    "purchase-requests",
    PurchaseRequestViewSet,
    basename="purchase-request"
)

router.register(
    "markets",
    MarketViewSet,
    basename="market"
)

router.register(
    "prices",
    PriceRecordViewSet,
    basename="price"
)

router.register(
    "notifications",
    NotificationViewSet,
    basename="notification"
)


urlpatterns = [

    path(
        "django-admin/",
        admin.site.urls
    ),

    path(
        "api/auth/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair"
    ),

    path(
        "api/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh"
    ),

    path(
        "api/auth/register/",
        register_view,
        name="api-register"
    ),

    path(
        "api/",
        include(router.urls)
    ),

    path(
        "",
        TemplateView.as_view(
            template_name="home.html"
        ),
        name="home"
    ),

    path(
        "login/",
        CustomLoginView.as_view(),
        name="login"
    ),

    path(
        "logout/",
        CustomLogoutView.as_view(),
        name="logout"
    ),

    path(
        "register/",
        RegisterView.as_view(),
        name="register"
    ),

    path(
        "products/",
        ProductListView.as_view(),
        name="products"
    ),

    path(
        "products/<slug:slug>/",
        ProductDetailView.as_view(),
        name="product-detail"
    ),

    path(
        "offers/",
        OfferListView.as_view(),
        name="offers"
    ),

    path(
        "offers/create/",
        OfferCreateView.as_view(),
        name="offer-create"
    ),

    path(
        "offers/<int:pk>/order/",
        OfferOrderCreateView.as_view(),
        name="offer-order-create"
    ),

    path(
        "offers/<int:pk>/",
        OfferDetailView.as_view(),
        name="offer-detail"
    ),

    path(
        "requests/",
        PurchaseRequestListView.as_view(),
        name="requests"
    ),

    path(
        "requests/create/",
        PurchaseRequestCreateView.as_view(),
        name="request-create"
    ),

    path(
        "requests/<int:pk>/",
        PurchaseRequestDetailView.as_view(),
        name="request-detail"
    ),

    path(
        "my/offers/",
        MyOffersListView.as_view(),
        name="my-offers"
    ),

    path(
        "my/requests/",
        MyRequestsListView.as_view(),
        name="my-requests"
    ),

    path(
        "my/orders/",
        MyOrdersListView.as_view(),
        name="my-orders"
    ),

    path(
        "my/orders/<int:pk>/accept/",
        OrderAcceptView.as_view(),
        name="order-accept"
    ),

    path(
        "my/orders/<int:pk>/reject/",
        OrderRejectView.as_view(),
        name="order-reject"
    ),

    path(
        "my/orders/<int:pk>/complete/",
        OrderCompleteView.as_view(),
        name="order-complete"
    ),

    path(
        "my/notifications/",
        MyNotificationsListView.as_view(),
        name="my-notifications"
    ),

    path(
        "observatory/",
        ObservatoryView.as_view(),
        name="observatory"
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )