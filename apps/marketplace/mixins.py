from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

from apps.accounts.models import User


class ProducerOrSupplierRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in [User.Role.PRODUCER, User.Role.SUPPLIER]:
            messages.error(
                request,
                "Accès réservé aux producteurs et fournisseurs.",
            )
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)


class BuyerRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != User.Role.BUYER:
            messages.error(request, "Accès réservé aux acheteurs.")
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)
