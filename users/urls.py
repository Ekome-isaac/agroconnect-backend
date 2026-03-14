from django.urls import path
from .views import (
    CartItemUpdateView,
    RegisterView,
    MyTokenObtainPairView,
    CropListCreateView,
    CropRetrieveUpdateDestroyView,
    CartListCreateView,
    CartItemDeleteView,
    CreateOrderView,
    OrderListView,
    FarmerOrdersView,
    FarmerDashboardView
)

from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [

    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Crops
    path('crops/', CropListCreateView.as_view(), name='crop_list_create'),
    path('crops/<int:pk>/', CropRetrieveUpdateDestroyView.as_view(), name='crop_detail'),

    # Cart
    path('cart/', CartListCreateView.as_view(), name='cart_list_create'),
    path('cart/<int:pk>/delete/', CartItemDeleteView.as_view(), name='cart_delete'),

    # Orders
    path('orders/create/', CreateOrderView.as_view(), name='create_order'),
    path('orders/', OrderListView.as_view(), name='order_list'),

    path('farmer/orders/', FarmerOrdersView.as_view(), name='farmer_orders'),

    path('farmer/dashboard/', FarmerDashboardView.as_view(), name='farmer_dashboard'),

    path('cart/<int:pk>/update/', CartItemUpdateView.as_view(), name='cart_item_update'),
]