import base64
import json
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any, cast

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


class ReceiptProcessingService:
    def __init__(self, requester: Callable[..., Any] | None = None) -> None:
        self.api_key = settings.GROK_API_KEY
        self.api_url = settings.GROK_API_URL
        self.model = settings.GROK_MODEL
        self.max_tokens = settings.GROK_MAX_TOKENS
        self.timeout = settings.GROK_API_TIMEOUT
        self.requester = requester or urllib.request.urlopen

    def process_receipt(self, receipt: Receipt) -> None:
        """
        Process a receipt by sending its images to the LLM and parsing the result.
        """
        log = logger.bind(receipt_id=receipt.id, user_id=receipt.user.id)
        log.info("receipt_processing_started", image_count=receipt.images.count())

        # Check budget before starting
        if not receipt.organization.has_budget():
            error_msg = f"Organization {receipt.organization.name} has exceeded its monthly token limit."
            log.error("organization_out_of_budget", limit=receipt.organization.spending_tier.token_limit)
            ReceiptError.objects.update_or_create(receipt=receipt, defaults={"message": error_msg})
            receipt.status = Receipt.Status.FAILED
            receipt.save()
            return

        receipt.status = Receipt.Status.PROCESSING
        receipt.save()

        try:
            raw_result = self._call_llm(receipt)
            self._save_result(receipt, raw_result)
            receipt.status = Receipt.Status.COMPLETED
            receipt.save()
            log.info("receipt_processing_completed")
        except Exception as e:
            log.exception("receipt_processing_failed", error=str(e))
            ReceiptError.objects.update_or_create(receipt=receipt, defaults={"message": str(e)})
            receipt.status = Receipt.Status.FAILED
            receipt.save()

    def _call_llm(self, receipt: Receipt) -> dict[str, Any]:
        """Send receipt images to LLM and return raw JSON response."""
        log = logger.bind(receipt_id=receipt.id)
        prompt = (
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

        log.info("llm_request_sent", model=self.model, max_tokens=self.max_tokens)
        try:
            with self.requester(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise Exception(f"API call failed: {e}") from e
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse LLM API response: {e}") from e

        # Record token usage
        usage = result.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        if total_tokens > 0:
            log.info(
                "llm_token_usage",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )
            TokenUsage.objects.create(
                organization=receipt.organization,
                user=receipt.user,
                tokens=total_tokens,
                action=TokenUsage.Action.RECEIPT_SCAN,
            )

        choices = result.get("choices", [])
        if not choices:
            raise Exception("No choices returned from LLM")

        choice = choices[0]
        finish_reason = choice.get("finish_reason")
        log.info("llm_response_received", finish_reason=finish_reason)

        if finish_reason == "length":
            log.warning("llm_response_truncated", finish_reason=finish_reason)

        message_content = choice.get("message", {}).get("content", "")
        try:
            return cast(dict[str, Any], json.loads(message_content))
        except json.JSONDecodeError as e:
            log.error("llm_invalid_json_content", content=message_content)
            raise Exception(f"LLM returned invalid JSON content: {e}") from e

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
