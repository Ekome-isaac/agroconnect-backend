from rest_framework import generics, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated

from .permissions import IsSeller

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.views import APIView, PermissionDenied

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from .models import (
    Crop,
    CartItem,
    Order,
    OrderItem,
    Category,
)

from django.db.models import Sum, F

from .serializers import (
    RegisterSerializer,
    CropSerializer,
    CartItemSerializer,
    OrderSerializer,
    MyTokenObtainPairSerializer,
    CategorySerializer
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
    filterset_fields = ['category']
    search_fields = ['name', 'location']

    def get_queryset(self):
        user = self.request.user
        qs = Crop.objects.all()

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        # Farmers see only their crops
        if user.role == "seller":
            qs = qs.filter(farmer=user)

        # Buyers see all crops
        return qs

    def perform_create(self, serializer):
        if self.request.user.role != "seller":
            raise PermissionDenied("Only sellers can create crops")
        serializer.save(farmer=self.request.user)  


class CropRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer
    permission_classes = [IsAuthenticated]


from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters
from .models import Crop
from .serializers import CropSerializer

class CropListView(generics.ListAPIView):
    queryset = Crop.objects.all().order_by('-created_at')
    serializer_class = CropSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'price']
    search_fields = ['name', 'location']


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

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        total_price = sum(item.crop.price * item.quantity for item in queryset)
        return Response({
            'items': serializer.data,
            'total_price': total_price
        })    


class CartItemDeleteView(generics.DestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]


class CartItemUpdateView(generics.UpdateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # ensure users can only update their own cart items
        return CartItem.objects.filter(user=self.request.user)


# =====================================================
# ORDER VIEWS
# =====================================================

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        cart_items = CartItem.objects.filter(user=request.user)

        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=400)

        order = Order.objects.create(buyer=request.user)
        total_price = 0

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                crop=item.crop,
                quantity=item.quantity,
                price=item.crop.price
            )
            total_price += item.crop.price * item.quantity

        # clear cart after order
        cart_items.delete()

        serializer = OrderSerializer(order)
        return Response({
            "order": serializer.data,
            "total_price": total_price
        })


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

        # recent orders (last 5)
        recent_orders = orders.order_by('-order__created_at')[:5].values(
            'order__id',
            'crop__name', 
            'quantity', 
            'price',
        )

        # top selling crops
        top_crops = orders.values('crop__name').annotate(
            'crop_name'
        ).annotate(
            total_sold=Sum('quantity')
        ).order_by('-total_sold')[:5]



        # total quantity sold
        total_quantity = orders.aggregate(
            total=Sum('quantity')
        )['total'] or 0

        data = {
            "total_crops": total_crops,
            "total_orders": total_orders,
            "total_revenue": revenue,
            "total_quantity": total_quantity,
            "recent_orders": list(recent_orders),
            "top_crops": list(top_crops)
        }

        return Response(data)
    

class CategoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer



from rest_framework import generics
from .models import Rating
from .serializers import RatingSerializer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg

class CreateRatingView(generics.CreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)

    def perform_create(self, serializer):
        rating = serializer.save(buyer=self.request.user)

        farmer = rating.farmer
        avg_rating = farmer.ratings_received.aggregate(Avg('rating')) ['rating_avg']
        farmer.rating = avg_rating or 0
        farmer.save() 