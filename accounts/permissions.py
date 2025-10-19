from rest_framework.permissions import BasePermission

class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

class AllowAny(BasePermission):
    def has_permission(self, request, view):
        return True