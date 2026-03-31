from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class SpendingTier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    token_limit = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return str(self.name)


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    spending_tier = models.ForeignKey(
        SpendingTier,
        on_delete=models.PROTECT,
        related_name="organizations",
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return str(self.name)


class User(AbstractUser):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="users",
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return str(self.username)


class TokenUsage(models.Model):
    class Action(models.TextChoices):
        RECEIPT_SCAN = "RECEIPT_SCAN", _("Receipt Scan")
        CATEGORY_REEVALUATION = "CATEGORY_REEVALUATION", _("Category Re-evaluation")

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="token_usages",
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="token_usages")
    tokens = models.PositiveIntegerField()
    action = models.CharField(
        max_length=50,
        choices=Action.choices,
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.tokens} tokens for {self.action} by {self.organization.name}"
