from typing import Any

import posthog.contexts
import structlog
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, View

from accounts.utils import get_auth_user

from .forms import MAX_TOTAL_SIZE, MAX_UPLOAD_SIZE, ReceiptUploadForm
from .models import Receipt, ReceiptImage
from .tasks import process_receipt_task

logger = structlog.get_logger(__name__)


class ReceiptListView(LoginRequiredMixin, ListView[Receipt]):
    model = Receipt
    template_name = "scanning/list.html"
    context_object_name = "receipts"
    ordering = ["-created_at"]


class ReceiptUploadView(LoginRequiredMixin, CreateView[Receipt, ReceiptUploadForm]):
    model = Receipt
    form_class = ReceiptUploadForm
    template_name = "scanning/upload.html"
    success_url = reverse_lazy("scanning:receipt-list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["max_upload_size"] = MAX_UPLOAD_SIZE
        context["max_total_size"] = MAX_TOTAL_SIZE
        try:
            user = get_auth_user(self.request)
            context["has_budget"] = user.organization.has_budget()
        except ValueError:
            context["has_budget"] = False
        return context

    def form_valid(self, form: ReceiptUploadForm) -> HttpResponse:
        user = get_auth_user(self.request)

        if not user.organization.has_budget():
            form.add_error(None, "Your organization has reached its monthly token limit.")
            return self.form_invalid(form)

        files = self.request.FILES.getlist("images")
        log = logger.bind(user_id=user.id, image_count=len(files))

        with transaction.atomic():
            self.object = form.save(commit=False)

            self.object.user = user
            self.object.organization = user.organization
            self.object.save()

            for i, f in enumerate(files):
                ReceiptImage.objects.create(receipt=self.object, image=f, sequence=i)

        receipt_id = self.object.id
        org_id = user.organization_id
        log.info("receipt_upload_success", receipt_id=receipt_id)
        transaction.on_commit(lambda: process_receipt_task.delay(receipt_id, org_id))

        return HttpResponseRedirect(self.get_success_url())


class ReceiptDetailView(LoginRequiredMixin, DetailView[Receipt]):
    model = Receipt
    template_name = "scanning/detail.html"
    context_object_name = "receipt"


class ReceiptStatusView(LoginRequiredMixin, View):
    """View to return the status of a receipt for HTMX polling."""

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        receipt = get_object_or_404(Receipt, pk=pk)

        if request.headers.get("HX-Request"):
            logger.info("receipt_status_poll", receipt_id=receipt.id, status=receipt.status)
            # Simple check for mobile to return the correct partial
            user_agent = request.headers.get("User-Agent", "").lower()
            is_mobile = any(ua in user_agent for ua in ["mobile", "android", "iphone"])

            template = (
                "scanning/partials/receipt_row_mobile.html"
                if is_mobile
                else "scanning/partials/receipt_row.html"
            )
            return render(request, template, {"receipt": receipt})

        return redirect("scanning:receipt-detail", pk=pk)


class DummyEventView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        user = get_auth_user(request)
        with posthog.contexts.new_context():
            posthog.contexts.identify_context(str(user.pk))
            posthog.capture("dummy-event")
        return HttpResponse(content=b"Event recorded.")
