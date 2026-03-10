from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser): 
    ROLE_CHOICES = (
        ('buyer', 'buyer'),
        ('seller', 'seller'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return self.username
    
    
# Crop model to store crop details for sellers
# This model will be linked to the User model through a ForeignKey relationship, allowing us to associate each crop with a specific seller. 
from django.db import models
from django.conf import settings

class Crop(models.Model):
    CROP_TYPES = [
        ('food', 'Food Crop'),
        ('industrial', 'Industrial Crop'),
    ]

    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=50)  # e.g., kg, bag, bunch
    price = models.DecimalField(max_digits=10, decimal_places=2)

    image = models.ImageField(upload_to='crops/', null=True, blank=True)

    crop_type = models.CharField(max_length=20, choices=CROP_TYPES)
    location = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.quantity} {self.unit}"


# Cart model to store items in the user's shopping cart
class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> {self.crop.name} ({self.quantity})"
    


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