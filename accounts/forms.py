from django import forms

from accounts.utils.mobile import normalize_mobile


class LoginForm(forms.Form):
    mobile = forms.CharField(
        label="شماره موبایل",
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "09123456789",
                "autocomplete": "tel",
                "inputmode": "numeric",
            }
        ),
    )

    def clean_mobile(self):
        return normalize_mobile(
            self.cleaned_data["mobile"]
        )


class VerifyOTPForm(forms.Form):
    code = forms.CharField(
        label="کد تأیید",
        min_length=6,
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "123456",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
            }
        ),
    )

    def clean_code(self):
        code = self.cleaned_data["code"].strip()

        if not code.isdigit():
            raise forms.ValidationError(
                "کد تأیید باید فقط شامل عدد باشد."
            )

        return code