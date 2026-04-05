from django.urls import path

from . import views

app_name = "scanning"

urlpatterns = [
    path("", views.ReceiptListView.as_view(), name="receipt-list"),
    path("upload/", views.ReceiptUploadView.as_view(), name="receipt-upload"),
    path("<int:pk>/", views.ReceiptDetailView.as_view(), name="receipt-detail"),
    path(
        "xhr/receipt/<int:pk>/status/", views.ReceiptStatusView.as_view(), name="receipt-xhr-status"
    ),
    path("event/", views.DummyEventView.as_view(), name="generate-event"),
]
