from django.shortcuts import render
from menu.models import Category,FoodItem
def home(request,category_slug = None):
    data = FoodItem.objects.all()
 
    if category_slug is not None:
        category = Category.objects.get(slug= category_slug)
        data = FoodItem.objects.filter(category=category)

    category = Category.objects.all()



    return render(request,'home.html',{'data':data,'categories':category})