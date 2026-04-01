from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, View

from .forms import ReceiptUploadForm
from .models import Receipt, ReceiptImage
from .tasks import process_receipt_task


class OrganizationFilteredMixin:
    """Mixin to filter querysets by the user's organization."""

    def get_queryset(self: Any) -> QuerySet[Receipt]:
        # Handle cases where the base class doesn't have get_queryset (like View)
        qs = super().get_queryset() if hasattr(super(), "get_queryset") else Receipt.objects.all()  # type: ignore[misc]

        user = self.request.user
        if isinstance(user, AnonymousUser):
            return Receipt.objects.none()

        return qs.filter(organization=user.organization)


class ReceiptListView(LoginRequiredMixin, OrganizationFilteredMixin, ListView[Receipt]):
    model = Receipt
    template_name = "scanning/list.html"
    context_object_name = "receipts"
    ordering = ["-created_at"]


class ReceiptUploadView(LoginRequiredMixin, CreateView[Receipt, ReceiptUploadForm]):
    model = Receipt
    form_class = ReceiptUploadForm
    template_name = "scanning/upload.html"
    success_url = reverse_lazy("scanning:receipt-list")

    def form_valid(self, form: ReceiptUploadForm) -> HttpResponse:
        files = self.request.FILES.getlist("images")

        with transaction.atomic():
            self.object = form.save(commit=False)

            user = self.request.user
            if isinstance(user, AnonymousUser):
                raise ValueError("User must be authenticated")

            self.object.user = user
            self.object.organization = user.organization
            self.object.save()

            for i, f in enumerate(files):
                ReceiptImage.objects.create(receipt=self.object, image=f, sequence=i)

        receipt_id = self.object.id
        transaction.on_commit(lambda: process_receipt_task.delay(receipt_id))

        return HttpResponseRedirect(self.get_success_url())


class ReceiptDetailView(LoginRequiredMixin, OrganizationFilteredMixin, DetailView[Receipt]):
    model = Receipt
    template_name = "scanning/detail.html"
    context_object_name = "receipt"


class ReceiptStatusView(LoginRequiredMixin, OrganizationFilteredMixin, View):
    """View to return the status of a receipt for HTMX polling."""

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        receipt = get_object_or_404(self.get_queryset(), pk=pk)

        if request.headers.get("HX-Request"):
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
