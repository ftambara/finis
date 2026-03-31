from django.db import models
from django.utils import timezone

from accounts.models import Organization


class Category(models.Model):
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="categories",
    )

    def __str__(self) -> str:
        return str(self.name)

    class Meta:
        verbose_name_plural = "Categories"


class CategoryParent(models.Model):
    category = models.OneToOneField(
        Category,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="parent_link",
    )
    parent = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="child_links")


class Brand(models.Model):
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="brands")

    class Meta:
        unique_together = ("name", "organization")

    def __str__(self) -> str:
        return str(self.name)


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="products",
    )

    def __str__(self) -> str:
        return str(self.name)


class ProductBrand(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="brand_link",
    )
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")

    def __str__(self) -> str:
        return f"Variant of {self.product.name}"


class ProductVariantAttribute(models.Model):
    class AttributeType(models.TextChoices):
        SIZE = "SIZE", "Size"
        COLOR = "COLOR", "Color"
        FLAVOUR = "FLAVOUR", "Flavour"
        EAN = "EAN", "EAN"

    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="attributes")
    type = models.CharField(max_length=20, choices=AttributeType.choices)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ("variant", "type")


class Order(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="orders")
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_discounts = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=255)
    seller_name = models.CharField(max_length=255)
    brands = models.ManyToManyField(Brand, related_name="orders")
    purchased_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"Order {self.id} at {self.seller_name}"


class OrderSellerDetails(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="seller_details",
    )
    address = models.TextField()
    external_id = models.CharField(max_length=255)  # Key-value sorted string


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    raw_product_name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discounts = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self) -> str:
        return f"{self.quantity} x {self.raw_product_name}"


class OrderItemLink(models.Model):
    order_item = models.OneToOneField(
        OrderItem,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="product_link",
    )
    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="order_items",
    )
