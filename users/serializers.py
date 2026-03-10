# Serializers for User model.
from rest_framework import serializers
from .models import User
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
        fields = '__all__'  # includes all fields
        read_only_fields = ['farmer', 'created_at']  # farmer is set automatically



# Serializer for JWT token to include user role and username in the token response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Include additional user information in the token response
        token['username'] = user.username
        return token
    

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
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'

    def get_total_price(self, obj):
        return obj.total_price()