from typing import Any

import django_stubs_ext
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import FileExtensionValidator

from .models import Receipt

django_stubs_ext.monkeypatch()

# Maximum file size: 10MB
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
# Maximum total upload size: 50MB
MAX_TOTAL_SIZE = 50 * 1024 * 1024


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data: Any, initial: Any = None) -> Any:  # noqa: ANN401
        single_file_clean = super().clean
        if isinstance(data, list | tuple):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ReceiptUploadForm(forms.ModelForm[Receipt]):
    images = MultipleFileField(
        label="Receipt Images",
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])],
        widget=MultipleFileInput(
            attrs={
                "multiple": True,
                "capture": "camera",
                "class": (
                    "block w-full text-sm text-gray-900 border border-gray-300 "
                    "rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
                ),
            }
        ),
    )

    class Meta:
        model = Receipt
        fields: list[str] = []

    def clean_images(self) -> list[UploadedFile]:
        files: list[UploadedFile] = self.files.getlist("images")
        total_size = 0
        for f in files:
            if f.size is not None:
                if f.size > MAX_UPLOAD_SIZE:
                    raise ValidationError(f"File {f.name} is too large. Max size is 10MB.")
                total_size += f.size

        if total_size > MAX_TOTAL_SIZE:
            raise ValidationError("Total upload size exceeds 50MB.")

        return files
