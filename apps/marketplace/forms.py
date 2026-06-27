from django import forms

from .models import Offer, Order, PurchaseRequest


class OfferForm(forms.ModelForm):

    class Meta:
        model = Offer

        fields = [
            "product",
            "title",
            "quantity",
            "unit",
            "unit_price",
            "currency",
            "city",
            "province",
            "available_from",
            "description",
        ]

        widgets = {
            "available_from": forms.DateInput(
                attrs={"type": "date"}
            ),
            "description": forms.Textarea(
                attrs={"rows": 4}
            ),
        }


class PurchaseRequestForm(forms.ModelForm):

    class Meta:
        model = PurchaseRequest

        fields = [
            "product",
            "quantity",
            "unit",
            "target_price",
            "currency",
            "city",
            "province",
            "needed_before",
            "description",
        ]

        widgets = {
            "needed_before": forms.DateInput(
                attrs={"type": "date"}
            ),
            "description": forms.Textarea(
                attrs={"rows": 4}
            ),
        }


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["quantity", "note"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, offer=None, **kwargs):
        self.offer = offer
        super().__init__(*args, **kwargs)
        if offer:
            self.fields["quantity"].widget.attrs["max"] = str(offer.quantity)
            self.fields["quantity"].help_text = (
                f"Quantité disponible : {offer.quantity} {offer.unit}"
            )

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if self.offer and quantity > self.offer.quantity:
            raise forms.ValidationError(
                "La quantité demandée dépasse la quantité disponible."
            )
        return quantity