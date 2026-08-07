from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from accounts.forms import LoginForm, VerifyOTPForm
from accounts.models import User
from accounts.services.auth_service import AuthService
from accounts.services.otp_service import OTPService
from accounts.services.sms_service import SMSServiceError


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            OTPService.request_otp(
                form.cleaned_data["mobile"]
            )

            request.session["otp_mobile"] = (
                form.cleaned_data["mobile"]
            )

            return redirect("accounts:verify_otp")

        except SMSServiceError:
            messages.error(
                request,
                "ارسال پیامک با مشکل مواجه شد."
            )

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
        },
    )


@require_http_methods(["GET", "POST"])
def verify_otp_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    mobile = request.session.get("otp_mobile")

    if not mobile:
        return redirect("accounts:login")

    form = VerifyOTPForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            messages.error(
                request,
                "کاربر یافت نشد."
            )
            return redirect("accounts:login")

        if OTPService.verify(
            user,
            form.cleaned_data["code"],
        ):
            AuthService.login(
                request,
                user,
            )

            request.session.pop(
                "otp_mobile",
                None,
            )

            return redirect("core:home")

        messages.error(
            request,
            "کد وارد شده معتبر نیست."
        )

    return render(
        request,
        "accounts/verify_otp.html",
        {
            "form": form,
            "mobile": mobile,
        },
    )


@require_POST
def logout_view(request):
    AuthService.logout(request)
    return redirect("core:home")