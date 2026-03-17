from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import (
    OrderItem,
    User,
    Rating,
)


@receiver(post_save, sender=OrderItem)
def update_farmer_total_sales(sender, instance, created, **kwargs):
    """
    Every time an OrderItem is created, update the farmer's total_sales.
    """
    if created:
        farmer = instance.crop.farmer
        farmer.total_sales += instance.price * instance.quantity
        farmer.save()

@receiver(post_save, sender=User)
def update_farmer_verification(sender, instance, created, **kwargs):
    """
    Every time a User is saved, check if they meet the criteria for being a verified farmer.
    For simplicity, let's say a farmer is verified if they have at least 5 sales and an average rating of 4.0 or higher.
    """
    if instance.role == 'farmer':
        if instance.total_sales >= 1000 and instance.rating >= 4.0:  # Example criteria
            instance.is_verified_farmer = True
        else:
            instance.is_verified_farmer = False
        instance.save()

@receiver(post_save, sender=Rating)
def update_farmer_rating(sender, instance, created, **kwargs):
    """
    Every time a new Rating is created, update the farmer's average rating.
    """
    if created:
        farmer = instance.farmer
        farmer.update_rating() 