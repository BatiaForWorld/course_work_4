from django import forms

from .models import Mailing, Message, Recipient


def _apply_bootstrap(form: forms.BaseForm) -> None:
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, (forms.CheckboxSelectMultiple,)):
            continue
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault("class", "form-check-input")
            continue
        existing = widget.attrs.get("class", "")
        widget.attrs["class"] = (existing + " form-control").strip()


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ("email", "full_name", "comment")
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ("subject", "body")
        widgets = {
            "body": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)


class MailingForm(forms.ModelForm):
    start_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    end_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))

    class Meta:
        model = Mailing
        fields = ("start_time", "end_time", "message", "recipients", "is_active")
        widgets = {
            "recipients": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        if start_time and end_time and end_time <= start_time:
            self.add_error("end_time", "Дата окончания должна быть позже даты начала.")
        return cleaned_data
