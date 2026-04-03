from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
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

    def get_monthly_usage(self) -> int:
        """Calculate the total tokens used by the organization in the current month."""
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usage = self.token_usages.filter(created_at__gte=start_of_month).aggregate(
            total=models.Sum("tokens")
        )["total"]
        return usage or 0

    def has_budget(self) -> bool:
        """Check if the organization has budget remaining in its spending tier."""
        return self.get_monthly_usage() < self.spending_tier.token_limit

    def get_usage_percentage(self) -> int:
        """Calculate the percentage of the monthly token limit used."""
        limit = self.spending_tier.token_limit
        if limit == 0:
            return 100
        usage = self.get_monthly_usage()
        return min(100, int((usage / limit) * 100))

    def __str__(self) -> str:
        return str(self.name)


class UserManager(BaseUserManager["User"]):
    def create_user(
        self, email: str, password: str | None = None, **extra_fields: object
    ) -> "User":
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields: object
    ) -> "User":
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser):
    email = models.EmailField(_("email address"), unique=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="users",
    )
    created_at = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["organization"]

    def __str__(self) -> str:
        return str(self.email)


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
