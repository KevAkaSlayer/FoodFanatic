from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length = 100,unique = True ,null = True ,blank = True)

    def __str__(self):
        return f'{self.name}'


class FoodItem(models.Model):
    image = models.ImageField(upload_to='menu/images',blank = True,null = True)
    title = models.CharField(max_length = 50)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ManyToManyField(Category)
    
    def __str__(self):
        return self.title
class CartItem(models.Model):
    product = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2,null= True , blank =True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

# class Order(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     items = models.ManyToManyField(CartItem, blank=True)
#     shipping_address = models.CharField(max_length=100)


STAR_CHOICES = [
    ('⭐','⭐'),
    ('⭐⭐','⭐⭐'),
    ('⭐⭐⭐','⭐⭐⭐'),
    ('⭐⭐⭐⭐','⭐⭐⭐⭐'),
    ('⭐⭐⭐⭐⭐','⭐⭐⭐⭐⭐'),
]

class Review(models.Model):
    reviewer = models.ForeignKey(User,on_delete = models.CASCADE)
    item = models.ForeignKey(FoodItem,on_delete = models.CASCADE,related_name = 'review')
    body = models.TextField()
    created  = models.DateTimeField(auto_now_add = True)
    rating = models.CharField(max_length = 10,choices = STAR_CHOICES)
