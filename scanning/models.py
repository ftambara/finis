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
