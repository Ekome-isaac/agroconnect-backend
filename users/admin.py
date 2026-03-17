from django.contrib import admin
from .models import User, Crop, Category, CartItem, Order, OrderItem

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_verified_farmer', 'rating', 'total_sales', 'is_staff', 'is_superuser')
    list_filter = ('role', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')

admin.site.register(Crop)
admin.site.register(Category)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
# Register your models here.
