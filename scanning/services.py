import base64
import json
import urllib.error
import urllib.request
from typing import Any, Protocol, Self, cast

import structlog
from django.conf import settings
from django.db import transaction

from accounts.models import TokenUsage

from .models import (
    LineItemDiscount,
    PaymentMethod,
    PointOfSale,
    ProcessedReceipt,
    Receipt,
    ReceiptError,
    ReceiptLineItem,
    ReceiptResult,
    Seller,
    SellerOrderId,
)

logger = structlog.get_logger(__name__)


GEMINI_RECEIPT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "order": {
            "type": "OBJECT",
            "properties": {
                "total_price": {"type": "NUMBER"},
                "total_discounts": {"type": "NUMBER"},
                "payment_method": {"type": "STRING"},
                "seller_name": {"type": "STRING"},
                "seller_address": {"type": "STRING"},
                "seller_order_id": {"type": "STRING"},
            },
        },
        "line_items": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "price": {"type": "NUMBER"},
                    "product": {"type": "STRING"},
                    "quantity": {"type": "NUMBER"},
                    "discounts": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "amount": {"type": "NUMBER"},
                                "description": {"type": "STRING"},
                            },
                        },
                    },
                },
            },
        },
    },
}


class UrlResponse(Protocol):
    def read(self) -> bytes: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None: ...


class Requester(Protocol):
    def __call__(
        self,
        url: str | urllib.request.Request,
        data: bytes | None = None,
        timeout: float = ...,
        *,
        cafile: str | None = None,
        capath: str | None = None,
        cadefault: bool = False,
        context: object | None = None,
    ) -> UrlResponse: ...


class LLMProvider(Protocol):
    def process(self, receipt: Receipt) -> tuple[dict[str, Any], int]:
        """Process receipt and return (parsed_data, total_tokens)"""
        ...


class GrokProvider:
    def __init__(self, requester: Requester | None = None) -> None:
        self.api_key = settings.GROK_API_KEY
        self.api_url = settings.GROK_API_URL
        self.model = settings.GROK_MODEL
        self.max_tokens = settings.GROK_MAX_TOKENS
        self.timeout = settings.GROK_API_TIMEOUT
        self.requester = requester or urllib.request.urlopen

    def process(self, receipt: Receipt) -> tuple[dict[str, Any], int]:
        log = logger.bind(receipt_id=receipt.id, provider="grok")
        prompt = self._get_prompt()

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]

        for receipt_image in receipt.images.all():
            with open(receipt_image.image.path, "rb") as f:
                encoded_image = base64.b64encode(f.read()).decode("utf-8")
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"},
                    }
                )

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "max_tokens": self.max_tokens,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        req = urllib.request.Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        log.info("llm_request_sent", model=self.model)
        try:
            with self.requester(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise Exception(f"Grok API call failed: {e}") from e
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Grok API response: {e}") from e

        usage = result.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)

        choices = result.get("choices", [])
        if not choices:
            raise Exception("No choices returned from Grok")

        message_content = choices[0].get("message", {}).get("content", "")
        try:
            return cast(dict[str, Any], json.loads(message_content)), total_tokens
        except json.JSONDecodeError as e:
            log.error("llm_invalid_json_content", content=message_content)
            raise Exception(f"Grok LLM returned invalid JSON content: {e}") from e

    def _get_prompt(self) -> str:
        return (
            "Extract transaction details from this receipt. You may be provided with one or "
            "multiple images of the same receipt. If multiple images are provided, they may "
            "overlap to ensure full coverage. Your task is to merge the information from all "
            "images into a single, deduplicated logical receipt.\n\n"
            "Return a JSON object with:\n"
            "- order: {total_price, total_discounts, payment_method, seller_name, "
            "seller_address, seller_order_id}\n"
            "- line_items: [{price, product, quantity, "
            "discounts: [{amount, description}]}]\n\n"
            "Rules:\n"
            "1. seller_order_id should be formatted as key=value strings separated by "
            "spaces and sorted alphabetically.\n"
            "2. All prices and amounts should be numbers.\n"
            "3. If a field is missing, omit it from the JSON or set to null.\n"
            "4. Deduplicate line items that appear in multiple images due to overlap."
        )


class GeminiProvider:
    def __init__(self, requester: Requester | None = None) -> None:
        self.api_key = settings.GEMINI_API_KEY
        self.api_url = settings.GEMINI_API_URL
        self.model = settings.GEMINI_MODEL
        self.max_tokens = settings.GEMINI_MAX_TOKENS
        self.timeout = settings.GEMINI_API_TIMEOUT
        self.requester = requester or urllib.request.urlopen

    def process(self, receipt: Receipt) -> tuple[dict[str, Any], int]:
        log = logger.bind(receipt_id=receipt.id, provider="gemini")
        prompt = self._get_prompt()

        parts: list[dict[str, Any]] = [{"text": prompt}]

        for receipt_image in receipt.images.all():
            with open(receipt_image.image.path, "rb") as f:
                encoded_image = base64.b64encode(f.read()).decode("utf-8")
                parts.append(
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": encoded_image,
                        }
                    }
                )

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "maxOutputTokens": self.max_tokens,
                "responseJsonSchema": GEMINI_RECEIPT_SCHEMA,
                "temperature": 0,
            },
        }

        # Gemini uses API key in URL
        url = f"{self.api_url}/{self.model}:generateContent"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        log.info("llm_request_sent", model=self.model)
        try:
            with self.requester(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise Exception(f"Gemini API call failed: {e}") from e
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Gemini API response: {e}") from e

        usage_metadata = result.get("usageMetadata", {})
        total_tokens = usage_metadata.get("totalTokenCount", 0)

        candidates = result.get("candidates", [])
        if not candidates:
            # Check for error in response
            if "error" in result:
                error_msg = result["error"].get("message", "Unknown Gemini error")
                raise Exception(f"Gemini API error: {error_msg}")
            raise Exception("No candidates returned from Gemini")

        candidate = candidates[0]
        message_content = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")

        try:
            return cast(dict[str, Any], json.loads(message_content)), total_tokens
        except json.JSONDecodeError as e:
            log.error("llm_invalid_json_content", content=message_content)
            raise Exception(f"Gemini LLM returned invalid JSON content: {e}") from e

    def _get_prompt(self) -> str:
        return (
            "Extract transaction details from this receipt. You may be provided with one or "
            "multiple images of the same receipt. If multiple images are provided, they may "
            "overlap to ensure full coverage. Your task is to merge the information from all "
            "images into a single, deduplicated logical receipt.\n\n"
            "Rules:\n"
            "1. seller_order_id should be formatted as key=value strings separated by "
            "spaces and sorted alphabetically.\n"
            "2. Deduplicate line items that appear in multiple images due to overlap."
        )


class ReceiptProcessingService:
    def __init__(self, requester: Requester | None = None) -> None:
        self.provider = self._get_provider(requester)

    def _get_provider(self, requester: Requester | None) -> LLMProvider:
        provider_name = settings.SCANNING_LLM_PROVIDER
        if provider_name == "grok":
            return GrokProvider(requester)
        if provider_name == "gemini":
            return GeminiProvider(requester)
        raise ValueError(f"Unsupported LLM provider: {provider_name}")

    def process_receipt(self, receipt: Receipt) -> None:
        """
        Process a receipt by sending its images to the LLM and parsing the result.
        """
        log = logger.bind(receipt_id=receipt.id, user_id=receipt.user.id)
        log.info("receipt_processing_started", image_count=receipt.images.count())

        # Check budget before starting
        if not receipt.organization.has_budget():
            error_msg = (
                f"Organization {receipt.organization.name} has exceeded its monthly token limit."
            )
            log.error(
                "organization_out_of_budget", limit=receipt.organization.spending_tier.token_limit
            )
            ReceiptError.objects.update_or_create(receipt=receipt, defaults={"message": error_msg})
            receipt.status = Receipt.Status.FAILED
            receipt.save()
            return

        receipt.status = Receipt.Status.PROCESSING
        receipt.save()

        try:
            raw_result, total_tokens = self.provider.process(receipt)
            self._record_usage(receipt, total_tokens)
            self._save_result(receipt, raw_result)
            receipt.status = Receipt.Status.COMPLETED
            receipt.save()
            log.info("receipt_processing_completed")
        except Exception as e:
            log.exception("receipt_processing_failed", error=str(e))
            ReceiptError.objects.update_or_create(receipt=receipt, defaults={"message": str(e)})
            receipt.status = Receipt.Status.FAILED
            receipt.save()

    def _record_usage(self, receipt: Receipt, total_tokens: int) -> None:
        if total_tokens > 0:
            logger.info(
                "llm_token_usage",
                receipt_id=receipt.id,
                total_tokens=total_tokens,
            )
            TokenUsage.objects.create(
                organization=receipt.organization,
                user=receipt.user,
                tokens=total_tokens,
                action=TokenUsage.Action.RECEIPT_SCAN,
            )

    @transaction.atomic
    def _save_result(self, receipt: Receipt, data: dict[str, Any]) -> None:
        """Save the parsed LLM result into the database models."""
        log = logger.bind(receipt_id=receipt.id)
        ReceiptResult.objects.update_or_create(receipt=receipt, defaults={"raw_json": data})

        order_data = data.get("order", {})
        line_items_data = data.get("line_items", [])

        # 1. Seller & POS
        seller_name = order_data.get("seller_name") or "Unknown Seller"
        seller_address = order_data.get("seller_address") or "Unknown Address"

        seller, _ = Seller.objects.get_or_create(name=seller_name)
        pos, _ = PointOfSale.objects.get_or_create(seller=seller, address=seller_address)

        # 2. Processed Receipt
        processed_receipt = ProcessedReceipt.objects.create(
            receipt=receipt,
            point_of_sale=pos,
            total_price=order_data.get("total_price") or 0,
            total_discounts=order_data.get("total_discounts") or 0,
        )

        # 3. Optional Order Info
        if method := order_data.get("payment_method"):
            PaymentMethod.objects.create(processed_receipt=processed_receipt, method=method)

        if order_id := order_data.get("seller_order_id"):
            SellerOrderId.objects.create(processed_receipt=processed_receipt, identifier=order_id)

        # 4. Line Items
        for item_data in line_items_data:
            line_item = ReceiptLineItem.objects.create(
                processed_receipt=processed_receipt,
                product_description=item_data.get("product") or "Unknown Product",
                price=item_data.get("price") or 0,
                quantity=item_data.get("quantity") or 1,
            )

            for discount_data in item_data.get("discounts", []):
                LineItemDiscount.objects.create(
                    line_item=line_item,
                    amount=discount_data.get("amount") or 0,
                    description=discount_data.get("description") or "Discount",
                )

        log.info(
            "receipt_data_saved",
            seller=seller_name,
            total=processed_receipt.total_price,
            line_items=len(line_items_data),
        )
