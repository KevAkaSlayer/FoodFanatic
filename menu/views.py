from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import FoodItem,CartItem,Category,Review
from .forms import ReviewForm
from order.models import Order
# from order.models import SpecialOffer

@login_required(login_url='login')
def add_to_cart(request, product_id):
    product = get_object_or_404(FoodItem, pk=product_id)
    
    cart_item = CartItem.objects.filter(product=product, user=request.user).first()
    if cart_item:
        cart_item.quantity += 1
        cart_item.save()
    else:
        item = CartItem.objects.create(product=product, user=request.user,price = product.price, quantity=1)
        special = FoodItem.objects.filter(active = True).first()
        if product.active :
            item.price= product.discount_price
            item.save()
            
    return redirect('cart')


@login_required(login_url='login')
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.price * item.quantity for item in cart_items)
    dis_total = sum(item.product.discount_price * item.quantity for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price,'dis_total':dis_total})



@login_required(login_url='login')
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, pk=item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')

def details(request,id):
    item = FoodItem.objects.get(pk=id)
    review =Review.objects.filter(item=item)

    if request.user.is_authenticated :
        has_ordered = Order.objects.filter(user=request.user,id = id).exists()
        return render(request,'fooddetail.html',{'has_ordered':has_ordered,'item':item,'review':review})
    else:
        return render(request,'fooddetail.html',{'item':item,'review':review})



    # if request.method == 'POST':
    #     form = ReviewForm(request.POST)
    #     if form.is_valid():
    #         review = form.save(commit=False)
    #         review.item = item
    #         review.save()
    #         return redirect('detail',id = id)
    # else :
    #     form = ReviewForm()
    # return render (request,'fooddetail.html',{'item':item,'form':form,'review':review})

@login_required(login_url='login')
def ReviewView(request,id):
    form =ReviewForm()
    if request.method=='POST':
        form =ReviewForm(request.POST)
        if form.is_valid():
            item = FoodItem.objects.get(pk=id)
            body = form.cleaned_data['body']
            rating = form.cleaned_data['rating']
            Review.objects.create(reviewer=request.user,body=body ,item=item,rating = rating)
            return redirect('detail',id=id)
    return render(request,'review.html',{'form':form})