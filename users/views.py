from rest_framework import generics, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated

from .permissions import IsSeller

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.views import APIView, PermissionDenied

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from .models import Crop, CartItem, Order, OrderItem

from django.db.models import Sum, F

from .serializers import (
    RegisterSerializer,
    CropSerializer,
    CartItemSerializer,
    OrderSerializer,
    MyTokenObtainPairSerializer
)

# =====================================================
# AUTHENTICATION VIEWS
# =====================================================

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# =====================================================
# CROP VIEWS
# =====================================================

class CropListCreateView(generics.ListCreateAPIView):
    serializer_class = CropSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'location']

    def get_queryset(self):
        user = self.request.user

        # Farmers see only their crops
        if user.role == "seller":
            return Crop.objects.filter(farmer=user)

        # Buyers see all crops
        return Crop.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role != "seller":
            raise PermissionDenied("Only sellers can create crops")
        serializer.save(farmer=self.request.user)


class CropRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer
    permission_classes = [IsAuthenticated]


# =====================================================
# CART VIEWS
# =====================================================

class CartListCreateView(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartItemDeleteView(generics.DestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]


# =====================================================
# ORDER VIEWS
# =====================================================

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        cart_items = CartItem.objects.filter(user=request.user)

        if not cart_items.exists():
            return Response({"error": "Cart is empty"})

        order = Order.objects.create(buyer=request.user)

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                crop=item.crop,
                quantity=item.quantity,
                price=item.crop.price
            )

        # clear cart after order
        cart_items.delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user)


# =====================================================
# FARMER ORDER HISTORY
# =====================================================

class FarmerOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            items__crop__farmer=self.request.user
        ).distinct()
    

# =====================================================
# FARMER DASHBOARD VIEWS (PENDING)
# =====================================================

class FarmerDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        farmer = request.user

        # Total crops created by farmer
        total_crops = Crop.objects.filter(farmer=farmer).count()

        # Orders that contain this farmer's crops
        orders = OrderItem.objects.filter(crop__farmer=farmer)

        total_orders = orders.values('order').distinct().count()

        # Calculate revenue
        revenue = orders.aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or 0

        data = {
            "total_crops": total_crops,
            "total_orders": total_orders,
            "total_revenue": revenue
        }

        return Response(data)