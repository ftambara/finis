from django.db import models
from django.utils import timezone

from accounts.models import Organization, User


class Receipt(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="receipts",
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="receipts")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"Receipt {self.id} ({self.status})"


class ReceiptImage(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="receipts/%Y/%m/%d/")
    sequence = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sequence"]

    def __str__(self) -> str:
        return f"Image {self.sequence} for Receipt {self.receipt_id}"


class ReceiptResult(models.Model):
    receipt = models.OneToOneField(
        Receipt,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="result",
    )
    raw_json = models.JSONField()


class ReceiptError(models.Model):
    receipt = models.OneToOneField(
        Receipt,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="error",
    )
    message = models.TextField()


class Seller(models.Model):
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="sellers",
    )

    class Meta:
        unique_together = ("name", "organization")

    def __str__(self) -> str:
        return self.name


class PointOfSale(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name="points_of_sale")
    address = models.TextField()

    class Meta:
        unique_together = ("seller", "address")

    def __str__(self) -> str:
        return f"{self.seller.name} at {self.address}"


class ProcessedReceipt(models.Model):
    receipt = models.OneToOneField(
        Receipt,
        on_delete=models.CASCADE,
        related_name="processed",
        primary_key=True,
    )
    point_of_sale = models.ForeignKey(
        PointOfSale, on_delete=models.PROTECT, related_name="receipts"
    )
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_discounts = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    processed_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"Processed Receipt {self.receipt_id} - {self.point_of_sale.seller.name}"


class PaymentMethod(models.Model):
    processed_receipt = models.OneToOneField(
        ProcessedReceipt,
        on_delete=models.CASCADE,
        related_name="payment_info",
    )
    method = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.method


class SellerOrderId(models.Model):
    processed_receipt = models.OneToOneField(
        ProcessedReceipt,
        on_delete=models.CASCADE,
        related_name="seller_order_info",
    )
    # Formatted as key=value strings separated by spaces and sorted alphabetically
    identifier = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.identifier


class ReceiptLineItem(models.Model):
    processed_receipt = models.ForeignKey(
        ProcessedReceipt,
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    product_description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product_description}"


class LineItemDiscount(models.Model):
    line_item = models.ForeignKey(
        ReceiptLineItem,
        on_delete=models.CASCADE,
        related_name="discounts",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, default="Discount")

    def __str__(self) -> str:
        return f"-{self.amount} ({self.description})"
