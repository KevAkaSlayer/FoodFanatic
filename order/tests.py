from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from menu.models import CartItem, FoodItem

from .models import Order, OrderItem


class CheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("customer", password="test-password")
        self.other_user = User.objects.create_user("other", password="test-password")
        self.item = FoodItem.objects.create(
            title="Burger",
            description="Fresh burger",
            price=Decimal("10.00"),
        )
        self.client.force_login(self.user)

    def test_checkout_is_post_only_and_preserves_order_item_snapshot(self):
        CartItem.objects.create(
            user=self.user,
            product=self.item,
            quantity=2,
            unit_price=Decimal("10.00"),
        )
        url = reverse("placeorder")

        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url)

        order = Order.objects.get(user=self.user)
        self.assertRedirects(response, reverse("order_details", args=(order.pk,)))
        self.assertFalse(CartItem.objects.filter(user=self.user).exists())
        order_item = OrderItem.objects.get(order=order)
        self.assertEqual(order_item.product, self.item)
        self.assertEqual(order_item.product_name, "Burger")
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.unit_price, Decimal("10.00"))
        self.assertEqual(order.total_amount, Decimal("20.00"))

        # Repricing the menu afterwards must not rewrite what was charged.
        self.item.price = Decimal("12.00")
        self.item.save(update_fields=("price",))
        order_item.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(order_item.unit_price, Decimal("10.00"))
        self.assertEqual(order.total_amount, Decimal("20.00"))

    def test_empty_cart_does_not_create_order(self):
        response = self.client.post(reverse("placeorder"))

        self.assertRedirects(response, reverse("cart"))
        self.assertFalse(Order.objects.exists())

    def test_unavailable_item_blocks_checkout_without_clearing_cart(self):
        self.item.is_available = False
        self.item.save(update_fields=("is_available",))
        CartItem.objects.create(
            user=self.user,
            product=self.item,
            unit_price=Decimal("10.00"),
        )

        response = self.client.post(reverse("placeorder"))

        self.assertRedirects(response, reverse("cart"))
        self.assertFalse(Order.objects.exists())
        self.assertTrue(CartItem.objects.filter(user=self.user).exists())

    def test_price_change_refreshes_the_cart_instead_of_charging_the_old_price(self):
        CartItem.objects.create(
            user=self.user,
            product=self.item,
            quantity=2,
            unit_price=Decimal("8.00"),
        )

        response = self.client.post(reverse("placeorder"))

        self.assertRedirects(response, reverse("cart"))
        self.assertFalse(Order.objects.exists())
        cart_item = CartItem.objects.get(user=self.user)
        self.assertEqual(cart_item.unit_price, Decimal("10.00"))

        # The refreshed cart now matches the live price, so checkout proceeds.
        self.client.post(reverse("placeorder"))

        order = Order.objects.get(user=self.user)
        self.assertEqual(order.total_amount, Decimal("20.00"))
        self.assertEqual(OrderItem.objects.get(order=order).unit_price, Decimal("10.00"))

    def test_expired_discount_is_not_charged_at_checkout(self):
        self.item.discount_price = Decimal("6.00")
        self.item.active = True
        self.item.end_date = timezone.localdate() - timedelta(days=1)
        self.item.save()
        CartItem.objects.create(
            user=self.user,
            product=self.item,
            unit_price=Decimal("6.00"),
        )

        self.client.post(reverse("placeorder"))

        self.assertFalse(Order.objects.exists())
        self.assertEqual(
            CartItem.objects.get(user=self.user).unit_price,
            Decimal("10.00"),
        )

    def test_user_cannot_view_another_users_order(self):
        order = Order.objects.create(
            user=self.other_user,
            total_amount=Decimal("10.00"),
        )

        response = self.client.get(reverse("order_details", args=(order.pk,)))

        self.assertEqual(response.status_code, 404)

    def test_invalid_history_date_range_is_handled(self):
        response = self.client.get(
            reverse("orderhistory"),
            {"start_date": "2026-02-02", "end_date": "2026-01-01"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "start date must be before")


class RecordRetentionTests(TestCase):
    """Financial history must survive deletion of the records it points at."""

    def setUp(self):
        self.user = User.objects.create_user("customer", password="test-password")
        self.item = FoodItem.objects.create(
            title="Burger",
            description="Fresh burger",
            price=Decimal("10.00"),
        )
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal("20.00"),
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.item,
            product_name=self.item.title,
            quantity=2,
            unit_price=Decimal("10.00"),
        )

    def test_deleting_a_menu_item_keeps_the_order_line_and_its_snapshot(self):
        self.item.delete()

        self.order_item.refresh_from_db()
        self.assertIsNone(self.order_item.product)
        self.assertEqual(self.order_item.product_name, "Burger")
        self.assertEqual(self.order_item.unit_price, Decimal("10.00"))
        self.assertEqual(self.order_item.quantity, 2)
        self.assertEqual(self.order_item.line_total, Decimal("20.00"))

    def test_a_user_with_orders_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.user.delete()

        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

    def test_deleting_an_order_removes_only_its_own_lines(self):
        other_order = Order.objects.create(
            user=self.user,
            total_amount=Decimal("10.00"),
        )
        other_item = OrderItem.objects.create(
            order=other_order,
            product=self.item,
            product_name=self.item.title,
            quantity=1,
            unit_price=Decimal("10.00"),
        )

        self.order.delete()

        self.assertFalse(OrderItem.objects.filter(pk=self.order_item.pk).exists())
        self.assertTrue(OrderItem.objects.filter(pk=other_item.pk).exists())
        self.assertTrue(FoodItem.objects.filter(pk=self.item.pk).exists())
