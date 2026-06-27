from rest_framework import serializers

from .models import User

REGISTRATION_ROLES = {
    User.Role.PRODUCER,
    User.Role.SUPPLIER,
    User.Role.BUYER,
}


def validate_registration_role(value):
    if value not in REGISTRATION_ROLES:
        raise serializers.ValidationError(
            "Rôle non autorisé à l'inscription. "
            "Choisissez producteur, fournisseur ou acheteur."
        )
    return value
