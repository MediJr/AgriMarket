from rest_framework import permissions


class IsOfferOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.producer == request.user


class IsPurchaseRequestOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.buyer == request.user


class IsOrderSeller(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.offer.producer == request.user
