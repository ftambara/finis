import json
from typing import Any, Self

import pytest
from pytest_django.fixtures import SettingsWrapper

from accounts.models import Organization, SpendingTier, User
from scanning.models import ProcessedReceipt, Receipt
from scanning.services import ReceiptProcessingService
from scanning.tasks import process_receipt_task


class MockResponse:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    def read(self) -> bytes:
        return json.dumps(self.data).encode("utf-8")

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass


@pytest.fixture
def organization(db: object) -> Organization:
    tier = SpendingTier.objects.create(name="Standard", token_limit=1000)
    return Organization.objects.create(name="Acme Corp", spending_tier=tier)


@pytest.fixture
def user(organization: Organization) -> User:
    return User.objects.create_user(
        email="test@example.com", password="password", organization=organization
    )


@pytest.fixture
def receipt(organization: Organization, user: User) -> Receipt:
    return Receipt.objects.create(
        organization=organization, user=user, status=Receipt.Status.PENDING
    )


@pytest.mark.django_db
class TestReceiptProcessingPipeline:
    def test_processing_service_grok_success(
        self, receipt: Receipt, settings: SettingsWrapper
    ) -> None:
        settings.SCANNING_LLM_PROVIDER = "grok"
        settings.GROK_API_KEY = "test-key"

        # Define mock response data in Grok (OpenAI) format
        mock_data = {
            "usage": {"total_tokens": 150},
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "order": {
                                    "total_price": 50.0,
                                    "total_discounts": 5.0,
                                    "payment_method": "Credit Card",
                                    "seller_name": "Test Store",
                                    "seller_address": "123 Test St",
                                    "seller_order_id": "order=123",
                                },
                                "line_items": [
                                    {
                                        "product": "Milk",
                                        "price": 4.0,
                                        "quantity": 2,
                                        "discounts": [{"amount": 1.0, "description": "Promo"}],
                                    }
                                ],
                            }
                        )
                    }
                }
            ],
        }

        def mock_requester(*args: Any, **kwargs: Any) -> MockResponse:
            return MockResponse(mock_data)

        # Execute processing with injected mock requester
        service = ReceiptProcessingService(requester=mock_requester)
        service.process_receipt(receipt)

        # Verify results
        receipt.refresh_from_db()
        assert receipt.status == Receipt.Status.COMPLETED

        processed = ProcessedReceipt.objects.get(receipt=receipt)
        assert processed.total_price == 50.0
        assert processed.point_of_sale.seller.name == "Test Store"
        assert processed.point_of_sale.address == "123 Test St"
        assert processed.payment_info.method == "Credit Card"
        assert processed.seller_order_info.identifier == "order=123"

        assert processed.line_items.count() == 1
        line_item = processed.line_items.first()
        assert line_item is not None
        assert line_item.product_description == "Milk"
        assert line_item.discounts.count() == 1
        discount = line_item.discounts.first()
        assert discount is not None
        assert discount.amount == 1.0

    def test_processing_service_gemini_success(
        self, receipt: Receipt, settings: SettingsWrapper
    ) -> None:
        settings.SCANNING_LLM_PROVIDER = "gemini"
        settings.GEMINI_API_KEY = "test-key"

        # Define mock response data in Gemini format
        mock_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "order": {
                                            "total_price": 75.0,
                                            "total_discounts": 0,
                                            "payment_method": "Cash",
                                            "seller_name": "Gemini Shop",
                                            "seller_address": "456 AI Blvd",
                                            "seller_order_id": "id=abc",
                                        },
                                        "line_items": [
                                            {
                                                "product": "Bread",
                                                "price": 3.0,
                                                "quantity": 1,
                                            }
                                        ],
                                    }
                                )
                            }
                        ]
                    },
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {"totalTokenCount": 200},
        }

        def mock_requester(*args: Any, **kwargs: Any) -> MockResponse:
            return MockResponse(mock_data)

        # Execute processing with injected mock requester
        service = ReceiptProcessingService(requester=mock_requester)
        service.process_receipt(receipt)

        # Verify results
        receipt.refresh_from_db()
        assert receipt.status == Receipt.Status.COMPLETED
        processed = ProcessedReceipt.objects.get(receipt=receipt)
        assert processed.total_price == 75.0
        assert processed.point_of_sale.seller.name == "Gemini Shop"

    def test_task_execution(self, receipt: Receipt, monkeypatch: pytest.MonkeyPatch) -> None:
        # Using monkeypatch to swap the service method for the task test
        # to avoid real network calls during task integration test.
        calls: list[Receipt] = []

        def mock_process(service_inst: object, receipt_obj: Receipt) -> None:
            calls.append(receipt_obj)

        monkeypatch.setattr(ReceiptProcessingService, "process_receipt", mock_process)

        process_receipt_task(receipt.id)
        assert len(calls) == 1
        assert calls[0].id == receipt.id
