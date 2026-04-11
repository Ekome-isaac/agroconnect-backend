from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenObtainPairView,
)
from .views import CreateStripeCheckoutSession, get_messages
from . import views

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
    ForgotPasswordView,
    ResetPasswordView,
    confirm_delivery,
    ConversationListView,
    ConversationDetailView,
    SendMessageView,
    get_conversations,
    send_message,
    get_or_create_conversation,
    unread_messages_count,
)

urlpatterns = [
    # ----------------------
    # AUTHENTICATION
    # ----------------------
    path('register/', RegisterView.as_view(), name='register'),
    path('auth/login/', MyTokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ----------------------
    # CROPS
    # ----------------------
    path('crops/', CropListCreateView.as_view(), name='crop_list_create'),
    path('crops/<int:pk>/', CropRetrieveUpdateDestroyView.as_view(), name='crop_detail'),

    # ----------------------
    # CART
    # ----------------------
    path('cart/', CartListCreateView.as_view(), name='cart_list_create'),
    path('cart/<int:pk>/', CartItemUpdateView.as_view(), name='cart_item_update'),
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

    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    
    path('reset-password/<uidb64>/<token>/', ResetPasswordView.as_view(), name='reset_password'),

    path("confirm-delivery/<int:order_id>/", confirm_delivery, name="confirm_delivery"),

    # ----------------------
    # MESSAGING SYSTEM
    # ----------------------
    path('conversations/', ConversationListView.as_view(), name='conversation_list'),
    path('conversations/<int:pk>/', ConversationDetailView.as_view(), name='conversation_detail'),
    path('message/send/', SendMessageView.as_view(), name='send_message'),

    path('chat/conversations/', views.get_conversations, name='get_conversations'),

    path("chat/send", send_message, name="send_message"),

    path("chat/start/", get_or_create_conversation, name='get_or_create_conversation'),

    path("chat/messages/<int:conversation_id>/", get_messages, name='get_messages'),

    path("chat/unread-count/", unread_messages_count, name='unread_messages_count'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]