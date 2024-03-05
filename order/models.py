from django.db import models
from django.contrib.auth.models import User
from menu.models import CartItem,FoodItem,Category
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


# class SpecialOffer(models.Model):
#     image = models.ImageField(upload_to='menu/images',blank = True,null = True)
#     title = models.CharField(max_length = 50,blank = True,null = True)
#     description = models.TextField(blank = True,null = True)
#     price = models.DecimalField(max_digits=10, decimal_places=2,blank = True,null = True)
#     category = models.ManyToManyField(Category)
#     discount_price = models.PositiveIntegerField(default=0,blank=True , null =True)
