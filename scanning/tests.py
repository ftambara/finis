import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.utils.datastructures import MultiValueDict

from accounts.models import Organization, SpendingTier, User
from scanning.models import Receipt, ReceiptImage


@pytest.fixture
def organization(db: object) -> Organization:
    tier = SpendingTier.objects.create(name="Standard", token_limit=1000)
    return Organization.objects.create(name="Acme Corp", spending_tier=tier)


@pytest.fixture
def other_organization(db: object) -> Organization:
    tier = SpendingTier.objects.create(name="Premium", token_limit=5000)
    return Organization.objects.create(name="Other Corp", spending_tier=tier)


@pytest.fixture
def user(organization: Organization) -> User:
    return User.objects.create_user(
        username="testuser", password="password", organization=organization
    )


@pytest.fixture
def other_user(other_organization: Organization) -> User:
    return User.objects.create_user(
        username="otheruser", password="password", organization=other_organization
    )


@pytest.mark.django_db
class TestScanningViews:
    def test_receipt_list_scopes_to_organization(
        self,
        client: Client,
        user: User,
        organization: Organization,
        other_user: User,
        other_organization: Organization,
    ) -> None:
        # Create receipts for both organizations
        r1 = Receipt.objects.create(
            organization=organization, user=user, status=Receipt.Status.PENDING
        )
        r2 = Receipt.objects.create(
            organization=other_organization, user=other_user, status=Receipt.Status.PENDING
        )

        client.login(username="testuser", password="password")
        response = client.get(reverse("scanning:receipt-list"))

        assert response.status_code == 200
        content = response.content.decode()
        # Search for more specific patterns to avoid matching CSS colors like #262626
        assert f">#{r1.id}</span>" in content
        assert f">#{r2.id}</span>" not in content

    def test_receipt_upload(self, client: Client, user: User, organization: Organization) -> None:
        client.login(username="testuser", password="password")
        image = SimpleUploadedFile("receipt.jpg", b"file_content", content_type="image/jpeg")

        # Use MultiValueDict for multiple files in test client
        data = MultiValueDict({"images": [image]})
        response = client.post(reverse("scanning:receipt-upload"), data=data, follow=True)

        if Receipt.objects.filter(organization=organization).count() == 0:
            print("Upload failed, content snippet:", response.content.decode()[:500])

        assert response.status_code == 200
        assert Receipt.objects.filter(organization=organization).count() == 1
        assert ReceiptImage.objects.count() == 1

    def test_receipt_detail_denies_other_organization(
        self,
        client: Client,
        user: User,
        other_user: User,
        other_organization: Organization,
    ) -> None:
        receipt = Receipt.objects.create(
            organization=other_organization, user=other_user, status=Receipt.Status.PENDING
        )

        client.login(username="testuser", password="password")
        response = client.get(reverse("scanning:receipt-detail", kwargs={"pk": receipt.pk}))

        assert response.status_code == 404

    def test_receipt_status_xhr(
        self, client: Client, user: User, organization: Organization
    ) -> None:
        receipt = Receipt.objects.create(
            organization=organization, user=user, status=Receipt.Status.PROCESSING
        )

        client.login(username="testuser", password="password")
        response = client.get(
            reverse("scanning:receipt-xhr-status", kwargs={"pk": receipt.pk}),
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        assert b"Processing" in response.content
        assert b'hx-trigger="every 5s"' in response.content

    def test_receipt_status_xhr_mobile(
        self, client: Client, user: User, organization: Organization
    ) -> None:
        receipt = Receipt.objects.create(
            organization=organization, user=user, status=Receipt.Status.PROCESSING
        )

        client.login(username="testuser", password="password")
        user_agent = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        )
        response = client.get(
            reverse("scanning:receipt-xhr-status", kwargs={"pk": receipt.pk}),
            HTTP_HX_REQUEST="true",
            HTTP_USER_AGENT=user_agent,
        )

        assert response.status_code == 200
        assert b"receipt-mobile-" in response.content
        assert b"Processing" in response.content
