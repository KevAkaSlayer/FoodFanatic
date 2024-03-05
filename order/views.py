from django.shortcuts import render,redirect,get_object_or_404
from menu.models import CartItem,FoodItem
from .models import OrderItem,SpecialOffer,Order
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from datetime import datetime
from django.db.models import Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.contrib import messages

# Create your views here.
@login_required(login_url='login')
def place_order(request):
    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items:
        messages.info(request, "Your cart is empty. Please add items to your cart before placing an order.")
        return redirect('cart')

    order = Order.objects.create(user=request.user, status='PENDING')

    for item in cart_items:
        item_price = item.product.price 
        OrderItem.objects.create(order=order, cartitem=item, quantity=item.quantity, price=item_price)

    CartItem.objects.filter(user=request.user).delete()

    messages.success(request, "Your order has been placed successfully!")
    return redirect('order_details', order_id=order.id)  

@login_required(login_url='login')
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
   
        
    return render(request, 'product_list.html', {'active_offers': active_offers})


# def product_list(request):
#     products = FoodItem.objects.all()
#     active_offers = SpecialOffer.objects.all
#     for product in products:
#         discount_percentage = Decimal(str(discount_percentage))
#         discounted_price = product.price * (1 - discount_percentage / 100)
#     product.discounted_price = discounted_price

#     return render(request, 'product_list.html', {'products': active_offers,''})










class OrderHistoryView(LoginRequiredMixin, ListView):
    template_name = 'orderhistory.html'
    model = Order
    balance = 0 # filter korar pore ba age amar total balance ke show korbe
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(
            user=self.request.user
        )
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            queryset = queryset.filter(placed_at__date__gte=start_date, placed_at__date__lte=end_date)
       
        return queryset.distinct()