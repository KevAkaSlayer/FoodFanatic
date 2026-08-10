from datetime import timedelta
from decimal import Decimal
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db.utils import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from order.models import Order, OrderItem

from .models import CartItem, FoodItem, Review
from Food_Fanatic.storage import SupabaseStorage


class SupabaseStorageTests(TestCase):
    def test_public_url_uses_the_bucket_and_escapes_object_names(self):
        storage = SupabaseStorage(
            url="https://example.supabase.co/",
            key="test-key",
            bucket_name="foodfanatic-media",
        )

        self.assertEqual(
            storage.url("menu/images/chicken wings.jpg"),
            "https://example.supabase.co/storage/v1/object/public/"
            "foodfanatic-media/menu/images/chicken%20wings.jpg",
        )


class FoodItemPricingTests(TestCase):
    def test_current_price_respects_discount_dates(self):
        item = FoodItem(
            title="Burger",
            description="Fresh burger",
            price=Decimal("10.00"),
            discount_price=Decimal("8.00"),
            active=True,
            start_date=timezone.localdate() - timedelta(days=1),
            end_date=timezone.localdate() + timedelta(days=1),
        )

        self.assertTrue(item.is_discount_active)
        self.assertEqual(item.current_price, Decimal("8.00"))

        item.end_date = timezone.localdate() - timedelta(days=1)
        self.assertFalse(item.is_discount_active)
        self.assertEqual(item.current_price, Decimal("10.00"))

    def test_discount_must_be_lower_than_regular_price(self):
        item = FoodItem(
            title="Burger",
            description="Fresh burger",
            price=Decimal("10.00"),
            discount_price=Decimal("12.00"),
            active=True,
        )

        with self.assertRaises(ValidationError):
            item.full_clean()


class MenuSeedCommandTests(TestCase):
    def test_if_empty_does_not_change_an_existing_menu(self):
        FoodItem.objects.create(
            title="Restaurant Special",
            description="A menu item entered by staff.",
            price=Decimal("12.00"),
        )

        call_command("seed_menu", skip_images=True, if_empty=True, verbosity=0)

        self.assertEqual(FoodItem.objects.count(), 1)
        self.assertTrue(FoodItem.objects.filter(title="Restaurant Special").exists())

    def test_seed_is_idempotent_and_updates_only_when_requested(self):
        call_command("seed_menu", skip_images=True, verbosity=0)
        call_command("seed_menu", skip_images=True, verbosity=0)

        self.assertEqual(FoodItem.objects.count(), 20)
        self.assertEqual(
            FoodItem.objects.get(title="Beef Burger").category.get().slug,
            "burger",
        )

        burger = FoodItem.objects.get(title="Beef Burger")
        burger.price = Decimal("1.00")
        burger.save(update_fields=("price",))

        call_command("seed_menu", skip_images=True, verbosity=0)
        burger.refresh_from_db()
        self.assertEqual(burger.price, Decimal("1.00"))

        call_command(
            "seed_menu",
            skip_images=True,
            update_existing=True,
            verbosity=0,
        )
        burger.refresh_from_db()
        self.assertEqual(burger.price, Decimal("200.00"))

    def test_fill_missing_images_only_updates_missing_image_references(self):
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                call_command("seed_menu", skip_images=True, verbosity=0)
                burger = FoodItem.objects.get(title="Beef Burger")
                burger.price = Decimal("1.00")
                burger.save(update_fields=("price",))

                call_command("seed_menu", fill_missing_images=True, verbosity=0)

                burger.refresh_from_db()
                self.assertEqual(burger.price, Decimal("1.00"))
                self.assertEqual(burger.image.name, "menu/images/beefburger.jpg")
                self.assertTrue(default_storage.exists(burger.image.name))


class CartSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("customer", password="test-password")
        self.other_user = User.objects.create_user("other", password="test-password")
        self.item = FoodItem.objects.create(
            title="Burger",
            description="Fresh burger",
            price=Decimal("10.00"),
        )
        self.client.force_login(self.user)

    def test_add_to_cart_requires_post_and_snapshots_price(self):
        url = reverse("addcart", args=(self.item.pk,))

        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url)

        self.assertRedirects(response, reverse("cart"))
        cart_item = CartItem.objects.get(user=self.user, product=self.item)
        self.assertEqual(cart_item.quantity, 1)
        self.assertEqual(cart_item.unit_price, Decimal("10.00"))

    def test_user_cannot_remove_another_users_cart_item(self):
        cart_item = CartItem.objects.create(
            user=self.other_user,
            product=self.item,
            quantity=1,
            unit_price=Decimal("10.00"),
        )

        response = self.client.post(reverse("remove", args=(cart_item.pk,)))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(CartItem.objects.filter(pk=cart_item.pk).exists())


class ReviewAuthorizationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("customer", password="test-password")
        self.item = FoodItem.objects.create(
            title="Burger",
            description="Fresh burger",
            price=Decimal("10.00"),
        )
        self.client.force_login(self.user)

    def test_review_requires_a_purchase(self):
        response = self.client.post(
            reverse("review", args=(self.item.pk,)),
            {"body": "This was delicious.", "rating": 5},
        )

        self.assertRedirects(response, reverse("detail", args=(self.item.pk,)))
        self.assertFalse(Review.objects.exists())

    def test_purchaser_can_create_and_update_review(self):
        order = Order.objects.create(user=self.user, total_amount=Decimal("10.00"))
        OrderItem.objects.create(
            order=order,
            product=self.item,
            product_name=self.item.title,
            quantity=1,
            unit_price=Decimal("10.00"),
        )
        url = reverse("review", args=(self.item.pk,))

        self.client.post(url, {"body": "This was delicious.", "rating": 5})
        self.client.post(url, {"body": "Still very delicious.", "rating": 4})

        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.get()
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.body, "Still very delicious.")

    def test_database_rejects_a_second_review_of_the_same_item(self):
        Review.objects.create(
            reviewer=self.user,
            item=self.item,
            body="This was delicious.",
            rating=5,
        )

        with self.assertRaises(IntegrityError):
            Review.objects.create(
                reviewer=self.user,
                item=self.item,
                body="Reviewing it a second time.",
                rating=1,
            )
