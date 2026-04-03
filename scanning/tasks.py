import structlog
from celery import shared_task

from .models import Receipt
from .services import ReceiptProcessingService

logger = structlog.get_logger(__name__)


@shared_task
def process_receipt_task(receipt_id: int) -> None:
    """
    Celery task to process a receipt.
    """
    log = logger.bind(receipt_id=receipt_id)
    try:
        receipt = Receipt.objects.get(id=receipt_id)
        service = ReceiptProcessingService()
        service.process_receipt(receipt)
    except Receipt.DoesNotExist:
        log.error("receipt_not_found")
    except Exception as e:
        log.exception("receipt_task_failed", error=str(e))
