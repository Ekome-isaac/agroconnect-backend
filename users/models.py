from django.contrib.auth.models import AbstractUser
from django.db import models
#
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager

from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, PermissionsMixin):
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()   # 🔥 ADD THIS LINE

    ROLE_CHOICES = (
        ('buyer', 'buyer'),
        ('seller', 'seller'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    farm_name = models.CharField(max_length=100, blank=True)
    farm_location = models.CharField(max_length=200, blank=True)

    is_verified_farmer = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  
    rating = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.email   # 🔥 FIX THIS TOO (username no longer exists)

    
    # method to update the average rating of a seller based on new ratings received
    def update_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            self.rating = sum(r.rating for r in ratings) / ratings.count()
            self.save()

    
# Crop model to store crop details for sellers
# This model will be linked to the User model through a ForeignKey relationship, allowing us to associate each crop with a specific seller. 
from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# class Crop(models.Model):
#     CROP_TYPES = [
#         ('food', 'Food Crop'),
#         ('industrial', 'Industrial Crop'),
#     ]

#     farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     name = models.CharField(max_length=200)
#     description = models.TextField(blank=True, null=True)
#     quantity = models.PositiveIntegerField()
#     unit = models.CharField(max_length=20, default='kg')
#     price = models.DecimalField(max_digits=10, decimal_places=2)

#     image = models.ImageField(upload_to='crops/', null=True, blank=True)

#     category = models.ForeignKey(
#         Category,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='crops'
#     )

#     crop_type = models.CharField(max_length=20, choices=CROP_TYPES)
#     location = models.CharField(max_length=200)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.name} - {self.quantity} {self.unit}"

class Crop(models.Model):
    CROP_TYPES = [
        ('food', 'Food Crop'),
        ('industrial', 'Industrial Crop'),
    ]

    PRICE_TYPES = [
        ('fixed', 'Fixed'),
        ('negotiable', 'Negotiable'),
        ('request', 'On Request'),
    ]

    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # PRODUCT CORE
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crops'
    )

    category = models.CharField(max_length=100, blank=True, null=True)  # 🔥 SIMPLIFY CATEGORY TO A STRING FIELD

    crop_type = models.CharField(max_length=20, choices=CROP_TYPES)
    location = models.CharField(max_length=200)

    # PRICING (SAAS STYLE)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_type = models.CharField(max_length=20, choices=PRICE_TYPES, default='fixed')

    # INVENTORY
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=20, default='kg')

    # MEDIA
    image = models.ImageField(upload_to='crops/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Cart model to store items in the user's shopping cart
class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> {self.crop.name} ({self.quantity})"
    
    class Meta:
        unique_together = ('user', 'crop')
    


# Order and OrderItem models to store order details and items in an order
class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
    ]

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    total_amount = models.DecimalField(max_digits = 10, decimal_places =  2, default = 0)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return sum(item.price * item.quantity for item in self.items.all())

    def __str__(self):
        return f"Order {self.id} by {self.buyer}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.crop.name} - {self.quantity}"


# Rating model to allow buyers to rate farmers after an order is completed
class Rating(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    rating = models.FloatField()
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('farmer', 'buyer', 'order')  # one rating per order


# Transaction model to store payment transaction details
from django.db import models
from django.conf import settings
from decimal import Decimal

User = settings.AUTH_USER_MODEL


class Transaction(models.Model):
    STATUS_CHOICES = (
        ("holding", "Holding"),
        ("released", "Released"),
        ("refunded", "Refunded"),
    )

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions_made")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions_received")
    order = models.OneToOneField("Order", on_delete=models.CASCADE, related_name="transaction")

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="holding")

    is_released = models.BooleanField(default=False)
    is_refunded = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.id} - {self.status}"

# Chat models to enable communication between buyers and sellers
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Conversation(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="buyer_chats")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="seller_chats")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("buyer", "seller")

    def __str__(self):
        return f"{self.buyer} ↔ {self.seller}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]