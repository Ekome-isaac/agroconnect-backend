from rest_framework import generics, status, filters

from rest_framework_simplejwt.authentication import JWTAuthentication
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
stripe.api_key = settings.STRIPE_SECRET_KEY

from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, F, Avg
from django.db import transaction

from .models import Crop, CartItem, Order, OrderItem, Category, Rating
from .serializers import (
    RegisterSerializer, CropSerializer, CartItemSerializer, OrderSerializer,
    MyTokenObtainPairSerializer, CategorySerializer, RatingSerializer
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
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

class CropListCreateView(generics.ListCreateAPIView):
    serializer_class = CropSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'location']

    def get_queryset(self):
        # Always return ALL crops for public marketplace browsing
        return Crop.objects.all().order_by('-created_at')
    
    def get_permissions(self):
        if self.request.method in ["POST"]:
            return [IsAuthenticated()]
        return [AllowAny()]
    

    def perform_create(self, serializer):
        user = self.request.user

        # Only logged-in sellers can create crops
        if not user.is_authenticated:
            raise PermissionDenied("Login required to create crops")

        if user.role != "seller":
            raise PermissionDenied("Only sellers can create crops")

        serializer.save(farmer=user)

class CropRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAuthenticated()]
        return [AllowAny()]

# =====================================================
# CART VIEWS
# =====================================================
class CartListCreateView(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        total_price = sum(item.crop.price * item.quantity for item in queryset)
        return Response({
            'items': serializer.data,
            'total_price': total_price
        })
    
    
    def perform_create(self, serializer):
        user = self.request.user
        crop = serializer.validated_data['crop']
        quantity = serializer.validated_data.get('quantity', 1)
        cart_item, created = CartItem.objects.get_or_create(user=user, crop=crop, defaults={'quantity': quantity})
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        # else:
        #     cart_item.quantity = quantity
        #     cart_item.save()



class CartItemUpdateView(generics.UpdateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)


class CartItemDeleteView(generics.DestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]


# =====================================================
# ORDER VIEWS
# =========================
# CREATE ORDER (BUYER)
# =========================
class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart_items = CartItem.objects.filter(user=request.user)

        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=400)

        with transaction.atomic():
            order = Order.objects.create(buyer=request.user)
            total_price = 0

            for item in cart_items.select_related("crop"):
                OrderItem.objects.create(
                    order=order,
                    crop=item.crop,
                    quantity=item.quantity,
                    price=item.crop.price
                )
                total_price += item.crop.price * item.quantity

            cart_items.delete()

        serializer = OrderSerializer(order)
        return Response({
            "order": serializer.data,
            "total_price": total_price
        })


# =========================
# BUYER ORDERS (ONLY HIS ORDERS)
# =========================
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            buyer=self.request.user
        ).prefetch_related("items", "items__crop").order_by("-id")


# =========================
# FARMER / SELLER ORDERS
# =========================
class FarmerOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            items__crop__seller=self.request.user   # ✅ FIXED FIELD NAME
        ).distinct().prefetch_related("items", "items__crop").order_by("-id")

# =====================================================
# DASHBOARDS
# =====================================================
class FarmerDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        farmer = request.user
        total_crops = Crop.objects.filter(farmer=farmer).count()
        orders = OrderItem.objects.filter(crop__farmer=farmer)
        total_orders = orders.values('order').distinct().count()
        revenue = orders.aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0
        total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0
        recent_orders = orders.order_by('-order__created_at')[:5].values(
            'order__id', 'crop__name', 'quantity', 'price'
        )
        top_crops = orders.values('crop__name').annotate(
            total_sold=Sum('quantity')
        ).order_by('-total_sold')[:5]

        return Response({
            "total_crops": total_crops,
            "total_orders": total_orders,
            "total_revenue": revenue,
            "total_quantity": total_quantity,
            "recent_orders": list(recent_orders),
            "top_crops": list(top_crops)
        })


# =====================================================
# CATEGORY VIEW
# =====================================================
class CategoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer


# =====================================================
# RATING VIEW
# =====================================================
class CreateRatingView(generics.CreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        rating = serializer.save(buyer=self.request.user)
        farmer = rating.farmer
        avg_rating = farmer.ratings.aggregate(Avg('rating'))['rating'] or 0
        farmer.rating = avg_rating
        farmer.save()


# =====================================================
# CHECKOUT VIEW
# =====================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):
    user = request.user

    cart_items = CartItem.objects.filter(user=user).select_related('crop')

    if not cart_items.exists():
        return Response({
            "success": False,
            "error": "Cart is empty"
        }, status=400)

    # =========================
    # ✅ VALIDATION FIRST
    # =========================
    for item in cart_items:

        # Prevent buying own product
        if item.crop.farmer == user:
            return Response({
                "success": False,
                "error": f"You cannot buy your own product: {item.crop.name}"
            }, status=400)

        # Check stock
        if item.quantity > item.crop.quantity:
            return Response({
                "success": False,
                "error": f"Not enough stock for {item.crop.name}"
            }, status=400)

    # =========================
    # ✅ PROCESS ORDER
    # =========================
    try:
        with transaction.atomic():

            order = Order.objects.create(buyer=user)
            total_amount = 0
            order_items = []

            for item in cart_items:
                # Deduct stock
                item.crop.quantity -= item.quantity
                item.crop.save()

                # Create order item
                order_items.append(
                    OrderItem(
                        order=order,
                        crop=item.crop,
                        quantity=item.quantity,
                        price=item.crop.price
                    )
                )

                total_amount += item.crop.price * item.quantity

            OrderItem.objects.bulk_create(order_items)

            order.total_amount = total_amount
            order.save()

            # Clear cart
            cart_items.delete()

        return Response({
            "success": True,
            "message": "Order placed successfully",
            "data": {
                "order_id": order.id,
                "total_amount": total_amount
            }
        }, status=201)

    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=500)
    
    
    

# =====================================================
# CUSTOM PERMISSIONS
# =====================================================
class IsSeller(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'seller'


class IsBuyer(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'buyer'


# =====================================================
# BUYER AND SELLER ORDERS
# =====================================================
class BuyerOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsBuyer]

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user)


class SellerOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsSeller]

    def get_queryset(self):
        return Order.objects.filter(items__crop__farmer=self.request.user).distinct()


# =====================================================
# SELLER DASHBOARD
# =====================================================
class SellerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsSeller]

    def get(self, request):
        farmer = request.user
        total_crops = Crop.objects.filter(farmer=farmer).count()
        orders = OrderItem.objects.filter(crop__farmer=farmer)
        total_orders = orders.values('order').distinct().count()
        revenue = orders.aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0
        total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0
        recent_orders = orders.order_by('-order__created_at')[:5].values(
            'order__id', 'crop__name', 'quantity', 'price', 'order__status'
        )
        top_crops = orders.values('crop__name').annotate(total_sold=Sum('quantity')).order_by('-total_sold')[:5]

        return Response({
            "total_crops": total_crops,
            "total_orders": total_orders,
            "total_revenue": revenue,
            "total_quantity_sold": total_quantity,
            "recent_orders": list(recent_orders),
            "top_crops": list(top_crops)
        })


# =====================================================
# ORDER STATUS UPDATE
# =====================================================
class OrderStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsSeller]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        seller_order_items = order.items.filter(crop__farmer=request.user)
        if not seller_order_items.exists():
            return Response({"error": "You cannot update this order"}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        allowed_statuses = ['pending', 'confirmed', 'in_transit', 'delivered']

        if new_status not in allowed_statuses:
            return Response({"error": f"Invalid status. Allowed: {allowed_statuses}"}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save()
        serializer = OrderSerializer(order)
        return Response({"message": "Order status updated", "order": serializer.data})
    

class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]


# =====================================================
# STRIPE CHECKOUT VIEW
# =====================================================
class CreateStripeCheckoutSession(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        cart_items = CartItem.objects.filter(user=user)

        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=400)

        line_items = []
        total_amount = 0

        for item in cart_items:
            if item.crop.farmer == user:
                return Response({
                    "error": f"You cannot buy your own product: {item.crop.name}"
                }, status=400)

            line_items.append({
                "price_data": {
                    "currency": "frs",
                    "product_data": {
                        "name": item.crop.name,
                    },
                    "unit_amount": int(item.crop.price * 100),
                },
                "quantity": item.quantity,
            })

            total_amount += item.crop.price * item.quantity

        # Create Order first
        order = Order.objects.create(
            buyer=user,
            total_amount=total_amount,
            status='pending'
        )

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=f"{settings.FRONTEND_URL}/payment-success?order_id={order.id}",
                cancel_url=f"{settings.FRONTEND_URL}/payment-cancel",
                metadata={
                    "order_id": order.id  # keep it as int, webhook reads it directly
                }
            )

            return Response({
                "checkout_url": session.url,
                "order_id": order.id
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)


# =====================================================
# STRIPE WEBHOOK VIEW
# =====================================================
from .utils import send_email_notification

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET  # set this in your .env

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Retrieve order id from metadata or success_url
        order_id = session.get('metadata', {}).get('order_id') or session.get('client_reference_id')
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                # Mark order as confirmed
                order.status = 'confirmed'
                order.save()

                # Clear the buyer's cart
                CartItem.objects.filter(user=order.buyer).delete()

                # ===== EMAIL NOTIFICATIONS =====
                buyer_email = order.buyer.email
                seller_emails = list(order.items.values_list('crop__farmer__email', flat=True).distinct())

                # Email to Buyer
                send_email_notification(
                    subject="Order Confirmed - AgroConnect",
                    message=f"Hi {order.buyer.email},\n\nYour order #{order.id} has been confirmed!\nThank you for shopping with us.",
                    recipient_list=[buyer_email]
                )

                # Email to Sellers
                for email in seller_emails:
                    send_email_notification(
                        subject="New Order Received - AgroConnect",
                        message=f"Hi Seller,\n\nYou have a new order #{order.id}.\nPlease prepare the crops for delivery.",
                        recipient_list=[email]
                    )

            except Order.DoesNotExist:
                pass

    return HttpResponse(status=200)



from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings


User = get_user_model()


# =========================
# FORGOT PASSWORD
# =========================
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "If email exists, link sent"}, status=200)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

        print("Reset Link:", reset_link)  # For debugging, remove in production

        try:
            send_mail(
                subject="Password Reset",
                message=f"Click the link to reset your password: {reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            print("EMAIL ERROR:", str(e))
            return Response({"error": "Email sending failed"}, status=500)

        return Response({"message": "Password reset link sent"})
     

# =========================
# RESET PASSWORD
# =========================
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({"error": "Invalid link"}, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=400)

        password = request.data.get("password")
        user.set_password(password)
        user.save()

        return Response({"message": "Password reset successful"})
    

# ========================= 
# CONFIRM DELIVERY (RELEASE PAYMENT)
# =========================
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Order, Transaction


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirm_delivery(request, order_id):
    try:
        order = Order.objects.get(id=order_id, buyer=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    if order.status != "delivered":
        return Response({"error": "Order not delivered yet"}, status=400)

    transaction = order.transaction

    if transaction.is_released:
        return Response({"error": "Already confirmed"}, status=400)

    transaction.status = "released"
    transaction.is_released = True
    transaction.save()

    return Response({"message": "Payment released to seller"})


# =========================
# conversation and messaging views
# =========================
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


# =========================
# GET USER CONVERSATIONS
# =========================
class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(
            buyer=user
        ) | Conversation.objects.filter(
            seller=user
        )


# =========================
# GET SINGLE CONVERSATION
# =========================
class ConversationDetailView(generics.RetrieveAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Conversation.objects.all()


# =========================
# SEND MESSAGE
# =========================
class SendMessageView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


# =========================
# SIMPLE TEST ENDPOINT FOR CHAT
# =========================
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET'])
def get_conversations(request):
    conversations = [
        {
            "id": 1,
            "last_message": "hello",
            "updated_at": "2026-01-01"
        }
    ]
    return Response(conversations)

# =========================
# GET USER CONVERSATIONS (REAL IMPLEMENTATION)
# =========================
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Conversation
from .serializers import ConversationSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    user = request.user

    conversations = Conversation.objects.filter(
        buyer=user
    ) | Conversation.objects.filter(
        seller=user
    )

    conversations = conversations.order_by("-created_at")

    serializer = ConversationSerializer(conversations, many=True)

    return Response(serializer.data)


# =========================
# GET SINGLE CONVERSATION WITH MESSAGES (REAL IMPLEMENTATION)
# =========================
from .models import Message, Conversation

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message(request):
    user = request.user
    conversation_id = request.data.get("conversation_id")
    text = request.data.get("text")

    conversation = Conversation.objects.get(id=conversation_id)

    message = Message.objects.create(
        conversation=conversation,
        sender=user,
        text=text
    )

    return Response({
        "id": message.id,
        "text": message.text,
        "sender": message.sender.id
    })

# ========================= 
# PERFORM CREATE CONVERSATION (REAL IMPLEMENTATION)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_or_create_conversation(request):
    user = request.user

    seller_id = request.data.get("seller_id")

    if not seller_id:
        return Response({"error": "seller_id required"}, status=400)

    # Check if conversation already exists
    conversation = Conversation.objects.filter(
        buyer=user,
        seller_id=seller_id
    ).first()

    # If not, create it
    if not conversation:
        conversation = Conversation.objects.create(
            buyer=user,
            seller_id=seller_id
        )

    return Response({
        "conversation_id": conversation.id
    })


# ========================= 
# GET Messages
# =========================
from .models import Message, Conversation
from .serializers import MessageSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_messages(request, conversation_id):
    user = request.user

    try:
        conversation = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=404)

    # 🔒 SECURITY: only buyer or seller can access
    if conversation.buyer != user and conversation.seller != user:
        return Response({"error": "Unauthorized"}, status=403)

    messages = Message.objects.filter(conversation=conversation)

    # ✅ IMPORTANT: pass request context
    serializer = MessageSerializer(
        messages,
        many=True,
        context={"request": request}
    )

    return Response(serializer.data)


# =========================
# websocket routing for chat
# =========================
from django.urls import re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<conversation_id>\d+)/$", ChatConsumer.as_asgi()),
]


# ========================= 
# UNREAD MESSAGES COUNT
# =========================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_messages_count(request):
    count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False
    ).exclude(sender=request.user).count()

    return Response({"count": count})