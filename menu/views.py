from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from order.models import Order, OrderItem

from .forms import ReviewForm
from .models import CartItem, FoodItem, Review


@login_required(login_url="login")
@require_POST
@transaction.atomic
def add_to_cart(request, product_id):
    product = get_object_or_404(FoodItem, pk=product_id, is_available=True)
    cart_item, created = CartItem.objects.select_for_update().get_or_create(
        product=product,
        user=request.user,
        defaults={"unit_price": product.current_price, "quantity": 1},
    )
    if not created:
        cart_item.quantity += 1
        cart_item.unit_price = product.current_price
        cart_item.save(update_fields=("quantity", "unit_price"))

    messages.success(request, f"{product.title} was added to your cart.")
    return redirect("cart")


@login_required(login_url="login")
def view_cart(request):
    cart_items = list(
        CartItem.objects.filter(user=request.user).select_related("product")
    )
    total_price = sum(
        (item.line_total for item in cart_items),
        start=Decimal("0.00"),
    )
    return render(
        request,
        "cart.html",
        {"cart_items": cart_items, "total_price": total_price},
    )


@login_required(login_url="login")
@require_POST
@transaction.atomic
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(
        CartItem.objects.select_for_update(),
        pk=item_id,
        user=request.user,
    )
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save(update_fields=("quantity",))
    else:
        cart_item.delete()
    return redirect("cart")


def details(request, id):
    item = get_object_or_404(
        FoodItem.objects.prefetch_related("category"),
        pk=id,
        is_available=True,
    )
    reviews = item.reviews.select_related("reviewer")
    has_ordered = False
    if request.user.is_authenticated:
        has_ordered = (
            OrderItem.objects.filter(order__user=request.user, product=item)
            .exclude(order__status=Order.Status.CANCELLED)
            .exists()
        )
    return render(
        request,
        "fooddetail.html",
        {"has_ordered": has_ordered, "item": item, "review": reviews},
    )


@login_required(login_url="login")
def ReviewView(request, id):
    item = get_object_or_404(FoodItem, pk=id, is_available=True)
    has_ordered = (
        OrderItem.objects.filter(order__user=request.user, product=item)
        .exclude(order__status=Order.Status.CANCELLED)
        .exists()
    )
    if not has_ordered:
        messages.error(request, "You can review an item after purchasing it.")
        return redirect("detail", id=id)

    review = Review.objects.filter(reviewer=request.user, item=item).first()
    form = ReviewForm(request.POST or None, instance=review)
    if request.method == "POST" and form.is_valid():
        saved_review = form.save(commit=False)
        saved_review.reviewer = request.user
        saved_review.item = item
        saved_review.save()
        messages.success(request, "Thank you for your review.")
        return redirect("detail", id=id)

    return render(request, "review.html", {"form": form, "item": item})
