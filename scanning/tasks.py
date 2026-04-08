import structlog
from celery import shared_task
from django.db import transaction

from accounts.utils import set_tenant

from .models import Receipt
from .services import ReceiptProcessingService

logger = structlog.get_logger(__name__)


@shared_task
def process_receipt_task(receipt_id: int, organization_id: int) -> None:
    """
    Celery task to process a receipt.

    The organization_id parameter exists because it is necessary to conform with
    the enforced row-level security of the receipts table.
    """
    log = logger.bind(receipt_id=receipt_id, organization_id=organization_id)
    try:
        with transaction.atomic():
            set_tenant(organization_id)

            receipt = Receipt.objects.get(id=receipt_id)
            service = ReceiptProcessingService()
            service.process_receipt(receipt)
    except Receipt.DoesNotExist:
        log.error("receipt_not_found")
    except Exception as e:
        log.exception("receipt_task_failed", error=str(e))
