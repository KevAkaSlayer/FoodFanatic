from django.db import models
from django.contrib.auth.models import User
from menu.models import CartItem,FoodItem
# Create your models here.
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(CartItem, through='OrderItem')
    placed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255, choices=[('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='PENDING')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    cartitem = models.ForeignKey(CartItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) 


class SpecialOffer(models.Model):
    product = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    discount_percentage = models.PositiveIntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=False)