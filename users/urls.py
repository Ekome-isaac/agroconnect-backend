from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CreateStripeCheckoutSession

from .views import (
    RegisterView,
    MyTokenObtainPairView,
    CropListCreateView,
    CropRetrieveUpdateDestroyView,
    CartListCreateView,
    CartItemUpdateView,
    CartItemDeleteView,
    CreateOrderView,
    OrderListView,
    FarmerOrdersView,
    FarmerDashboardView,
    CategoryListView,
    CreateRatingView,
    checkout,
    BuyerOrdersView,
    SellerOrdersView,
    SellerDashboardView,
    OrderStatusUpdateView,
    OrderDetailView,
    stripe_webhook,
)

urlpatterns = [
    # ----------------------
    # AUTHENTICATION
    # ----------------------
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ----------------------
    # CROPS
    # ----------------------
    path('crops/', CropListCreateView.as_view(), name='crop_list_create'),
    path('crops/<int:pk>/', CropRetrieveUpdateDestroyView.as_view(), name='crop_detail'),

    # ----------------------
    # CART
    # ----------------------
    path('cart/', CartListCreateView.as_view(), name='cart_list_create'),
    path('cart/<int:pk>/update/', CartItemUpdateView.as_view(), name='cart_item_update'),
    path('cart/<int:pk>/delete/', CartItemDeleteView.as_view(), name='cart_delete'),

    # ----------------------
    # ORDERS
    # ----------------------
    path('orders/create/', CreateOrderView.as_view(), name='create_order'),
    path('orders/', OrderListView.as_view(), name='order_list'),

    # Buyer + Seller Orders
    path('buyer/orders/', BuyerOrdersView.as_view(), name='buyer_orders'),
    path('seller/orders/', SellerOrdersView.as_view(), name='seller_orders'),

    # ----------------------
    # DASHBOARDS
    # ----------------------
    path('farmer/dashboard/', FarmerDashboardView.as_view(), name='farmer_dashboard'),
    path('seller/dashboard/', SellerDashboardView.as_view(), name='seller_dashboard'),

    # ----------------------
    # CATEGORY
    # ----------------------
    path('categories/', CategoryListView.as_view(), name='categories'),

    # ----------------------
    # RATINGS
    # ----------------------
    path('rate-farmer/', CreateRatingView.as_view(), name='rate_farmer'),

    # ----------------------
    # CHECKOUT
    # ----------------------
    path('checkout/', checkout, name='checkout'),

    # ----------------------
    # ORDER STATUS UPDATE
    # ----------------------
    path('seller/orders/<int:order_id>/update-status/', OrderStatusUpdateView.as_view(), name='order_status_update'),

    path('orders/<int:pk>/', OrderDetailView.as_view()),

    path('payment/stripe/', CreateStripeCheckoutSession.as_view(), name='stripe_payment'),

    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),
]