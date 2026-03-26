from rest_framework.permissions import BasePermission

class IsSeller(BasePermission):

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "seller")


class IsBuyer(BasePermission):
    
    # allows access only to users with role 'buyer'
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'buyer')
    