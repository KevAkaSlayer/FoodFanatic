from django.shortcuts import render,redirect,get_object_or_404
from menu.models import CartItem,FoodItem
from .models import OrderItem,SpecialOffer,Order
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def place_order(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items:
        return redirect('cart') 

    order = Order.objects.create(user=request.user)
    for item in cart_items:
        item_price = item.product.price 
        OrderItem.objects.create(order=order, cartitem=item, quantity=item.quantity, price=item_price)

    CartItem.objects.filter(user=request.user).delete()  

    return redirect('order_details', order_id=order.id)

def order_details(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    order_items = order.items.all()
    total_cost = sum(item.price * item.quantity for item in order_items)
    return render(request, 'order_details.html', {'order': order, 'order_items': order_items, 'total_cost': total_cost})

# def checkout(request, order_id):
    
#     return redirect('order_details', order_id=order_id)

def product_list(request):
    products = FoodItem.objects.all()
    active_offers = SpecialOffer.objects.filter(active=True)

    for product in products:
        for offer in active_offers:
            if offer.product == product:
                product.discounted_price = product.price * (1 - offer.discount_percentage / 100)
                break 

    context = {
        'products': products,
        'active_offers': active_offers,
    }
    return render(request, 'product_list.html', context)