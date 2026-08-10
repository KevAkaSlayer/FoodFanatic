from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class FoodItem(models.Model):
    image = models.ImageField(upload_to="menu/images", blank=True, null=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    category = models.ManyToManyField(Category, related_name="food_items")
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        blank=True,
        null=True,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(
        default=False,
        help_text="Enable the discount, subject to its start and end dates.",
    )
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ("title",)

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        errors = {}
        if (
            self.discount_price is not None
            and self.price is not None
            and self.discount_price >= self.price
        ):
            errors["discount_price"] = "The discount price must be lower than the regular price."
        if self.active and self.discount_price is None:
            errors["discount_price"] = "A discount price is required when the discount is active."
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors["end_date"] = "The end date must be on or after the start date."
        if errors:
            raise ValidationError(errors)

    @property
    def is_discount_active(self):
        if not self.active or self.discount_price is None:
            return False
        today = timezone.localdate()
        return (
            (self.start_date is None or self.start_date <= today)
            and (self.end_date is None or self.end_date >= today)
            and self.discount_price < self.price
        )

    @property
    def current_price(self):
        return self.discount_price if self.is_discount_active else self.price


class CartItem(models.Model):
    product = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "product"),
                name="unique_cart_product_per_user",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="cart_quantity_at_least_one",
            ),
        ]

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} × {self.product} for {self.user}"


class Review(models.Model):
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(
        FoodItem,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        ordering = ("-created",)
        constraints = [
            models.UniqueConstraint(
                fields=("reviewer", "item"),
                name="unique_review_per_reviewer_and_item",
            )
        ]

    @property
    def rating_stars(self):
        return "★" * self.rating

    def __str__(self):
        return f"{self.rating}/5 review of {self.item} by {self.reviewer}"
