import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.utils.datastructures import MultiValueDict

from accounts.models import Organization, SpendingTier, User
from scanning.models import Receipt


@pytest.fixture
def organization(db: object) -> Organization:
    tier = SpendingTier.objects.using("admin").create(name="Standard", token_limit=1000)
    return Organization.objects.using("admin").create(name="Acme Corp", spending_tier=tier)


@pytest.fixture
def user(organization: Organization) -> User:
    return User.objects.db_manager("admin").create_user(
        email="test@example.com", password="password", organization=organization
    )


@pytest.mark.django_db(transaction=True, databases="__all__")
class TestUploadLimits:
    def test_individual_file_size_limit(
        self, client: Client, user: User, organization: Organization
    ) -> None:
        client.login(username="test@example.com", password="password")
        # 10MB + 1 byte
        content = b"0" * (10 * 1024 * 1024 + 1)
        image = SimpleUploadedFile("large.jpg", content, content_type="image/jpeg")
        data = MultiValueDict({"images": [image]})

        response = client.post(reverse("scanning:receipt-upload"), data=data, follow=True)
        assert Receipt.objects.using("admin").filter(organization_id=organization.id).count() == 0
        assert "is too large. Max size is 10MB." in response.content.decode()

    def test_total_file_size_limit(
        self, client: Client, user: User, organization: Organization
    ) -> None:
        client.login(username="test@example.com", password="password")
        # 6 files of 9MB each = 54MB total (exceeds 50MB limit)
        content = b"0" * (9 * 1024 * 1024)
        images = [
            SimpleUploadedFile(f"receipt_{i}.jpg", content, content_type="image/jpeg")
            for i in range(6)
        ]
        data = {"images": images}

        response = client.post(reverse("scanning:receipt-upload"), data=data, follow=True)
        assert Receipt.objects.using("admin").filter(organization_id=organization.id).count() == 0
        assert "Total upload size exceeds 50MB." in response.content.decode()
