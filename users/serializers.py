# Serializers for User model.
from rest_framework import serializers
from .models import Rating, User
from django.contrib.auth.password_validation import validate_password


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'role', 'phone_number']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


# Serializer for Crop model

from rest_framework import serializers
from .models import Crop

class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = [
            'id',
            'farmer',
            'name',
            'description',
            'price',
            'price_type',
            'quantity',
            'unit',
            'category',
            'crop_type',
            'image',
            'created_at',
            'location',
        ]
        read_only_fields = ['farmer']


# Serializer for JWT token to include user role and username in the token response

# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from django.contrib.auth import authenticate

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from rest_framework import serializers

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get('request'),
            username=email,   # 🔥 MUST BE username
            password=password
        )

        if not user:
            raise serializers.ValidationError({
                "non_field_errors": ["Invalid email or password"]
            })

        if not user.is_active:
            raise serializers.ValidationError({
                "non_field_errors": ["User account is disabled"]
            })

        token = super().get_token(user)

        return {
            "refresh": str(token),
            "access": str(token.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
            }
        }


# Serializer for CartItem model
from .models import CartItem

class CartItemSerializer(serializers.ModelSerializer):
    crop_name = serializers.ReadOnlyField(source='crop.name')
    crop_price = serializers.ReadOnlyField(source='crop.price')
    farmer = serializers.ReadOnlyField(source='crop.farmer.username')

    class Meta:
        model = CartItem
        fields = ['id', 'crop', 'crop_name', 'crop_price', 'farmer', 'quantity', 'added_at']



# Serializers for Order and OrderItem models
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    crop_name = serializers.ReadOnlyField(source='crop.name')
    class Meta:
        model = OrderItem
        fields = ['id', 'crop', 'crop_name', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'

    def get_total_price(self, obj):
        return sum(item.price * item.quantity for item in obj.items.all())


#serializer for Category model 
from .models import Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


#
from .models import Rating 
class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = [
            'id',
            'farmer',
            'buyer',
            'order',
            'rating',
            'review',
            'created_at'
        ]
        read_only_fields = ['buyer']

# Serializers for Conversation and Message models

from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model = Message
        fields = "__all__"


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = "__all__"


# Serializers for Conversation and Message models
from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    is_me = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "text", "created_at", "is_me"]

    def get_is_me(self, obj):
        request = self.context.get("request")
        return obj.sender == request.user if request else False

# Serializer for Conversation model that includes nested messages
class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = "__all__"