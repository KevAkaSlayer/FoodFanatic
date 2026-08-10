from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from menu.models import CartItem

from .forms import OrderHistoryFilterForm
from .models import Order, OrderItem


@login_required(login_url="login")
@require_POST
@transaction.atomic
def place_order(request):
    cart_items = list(
        CartItem.objects.select_for_update()
        .filter(user=request.user)
        .select_related("product")
    )
    if not cart_items:
        messages.info(
            request,
            "Your cart is empty. Add an item before placing an order.",
        )
        return redirect("cart")

    unavailable = [item.product.title for item in cart_items if not item.product.is_available]
    if unavailable:
        messages.error(
            request,
            f"These items are no longer available: {', '.join(unavailable)}.",
        )
        return redirect("cart")

    # A cart price is only a quote. Charge the price that is live at checkout,
    # and let the customer re-confirm whenever that differs from what they saw.
    repriced = []
    for item in cart_items:
        current_price = item.product.current_price
        if current_price != item.unit_price:
            repriced.append((item.product.title, item.unit_price, current_price))
            item.unit_price = current_price
    if repriced:
        CartItem.objects.bulk_update(cart_items, ("unit_price",))
        changes = ", ".join(
            f"{title} is now {new_price} (was {old_price})"
            for title, old_price, new_price in repriced
        )
        messages.warning(
            request,
            f"Prices changed while the items were in your cart: {changes}. "
            "Review your cart and place the order again.",
        )
        return redirect("cart")

    total_amount = sum(
        (item.line_total for item in cart_items),
        start=Decimal("0.00"),
    )
    order = Order.objects.create(user=request.user, total_amount=total_amount)
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                product=item.product,
                product_name=item.product.title,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in cart_items
        ]
    )
    CartItem.objects.filter(pk__in=[item.pk for item in cart_items]).delete()

    messages.success(request, "Your order has been placed successfully.")
    return redirect("order_details", order_id=order.id)


@login_required(login_url="login")
def order_details(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        pk=order_id,
        user=request.user,
    )
    return render(
        request,
        "order_details.html",
        {"order": order, "order_items": order.items.all()},
    )


class OrderHistoryView(LoginRequiredMixin, ListView):
    template_name = "orderhistory.html"
    model = Order
    paginate_by = 20

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .filter(user=self.request.user)
            .prefetch_related("items")
        )
        self.filter_form = OrderHistoryFilterForm(self.request.GET or None)
        if self.filter_form.is_valid():
            start_date = self.filter_form.cleaned_data.get("start_date")
            end_date = self.filter_form.cleaned_data.get("end_date")
            if start_date:
                queryset = queryset.filter(placed_at__date__gte=start_date)
            if end_date:
                queryset = queryset.filter(placed_at__date__lte=end_date)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context
