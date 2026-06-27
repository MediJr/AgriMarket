from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Profile, User
from .serializers import ProfileSerializer, RegisterSerializer, UserSerializer
from .validators import REGISTRATION_ROLES


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = "home"


class RegisterView(CreateView):
    model = User
    template_name = "accounts/register.html"
    fields = ["username", "email", "first_name", "last_name", "role", "phone", "password"]
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        user = form.save(commit=False)
        if user.role not in REGISTRATION_ROLES:
            from django.contrib import messages
            messages.error(self.request, "Rôle non autorisé à l'inscription.")
            return self.form_invalid(form)
        user.set_password(form.cleaned_data["password"])
        user.save()
        Profile.objects.create(user=user)
        return redirect("login")

    def post(self, request, *args, **kwargs):
        role = request.POST.get("role")
        if role and role not in REGISTRATION_ROLES:
            from django.contrib import messages
            messages.error(request, "Rôle non autorisé à l'inscription.")
            return self.get(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)


class IsSelfOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        target_user = obj.user if hasattr(obj, "user") else obj
        return target_user == request.user


class IsProducerOrSupplier(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [User.Role.PRODUCER, User.Role.SUPPLIER]
        )


class IsBuyer(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.BUYER
        )


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.select_related("profile").all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsSelfOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Profile.objects.select_related("user").all()
        return Profile.objects.select_related("user").filter(user=self.request.user)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {"message": "Utilisateur créé avec succès", "user_id": user.id},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
