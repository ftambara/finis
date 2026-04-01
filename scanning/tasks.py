from celery import shared_task

from .models import Receipt
from .services import ReceiptProcessingService


@shared_task
def process_receipt_task(receipt_id: int) -> None:
    """
    Celery task to process a receipt.
    """
    try:
        receipt = Receipt.objects.get(id=receipt_id)
        service = ReceiptProcessingService()
        service.process_receipt(receipt)
    except Receipt.DoesNotExist:
        pass
