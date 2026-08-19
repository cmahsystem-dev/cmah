from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cases.models import ServiceRequest
from cases.services.user_request_service import UserRequestService
from payments.models import Payment, PaymentMethod
from payments.services.card_to_card_payment_service import (
    CardToCardPaymentService,
)
from payments.services.payment_availability_service import (
    PaymentAvailabilityService,
)
from payments.services.payment_service import PaymentService
from services.models import Service


@login_required
@require_POST
def start_request(request, service_slug):
    service = get_object_or_404(
        Service,
        slug=service_slug,
        is_active=True,
    )

    service_request = UserRequestService.create_draft(
        user=request.user,
        service=service,
    )

    return redirect(
        "cases:request_form",
        tracking_code=service_request.tracking_code,
    )


@login_required
def request_form(request, tracking_code):
    service_request = get_object_or_404(
        ServiceRequest.objects.select_related(
            "service",
            "user",
        ),
        tracking_code=tracking_code,
        user=request.user,
    )

    if request.method == "POST":
        form_context = UserRequestService.get_form(
            service_request=service_request,
            user=request.user,
        )

        data = request.POST.dict()
        data.pop("csrfmiddlewaretoken", None)

        checkbox_keys = {
            field["key"]
            for field in form_context["schema"]
            if field["type"] == "checkbox"
        }

        for key in checkbox_keys:
            data[key] = key in request.POST

        UserRequestService.save_form(
            service_request=service_request,
            user=request.user,
            data=data,
            files=request.FILES,
        )

        service_request = UserRequestService.submit(
            service_request=service_request,
            user=request.user,
        )

        if service_request.status == ServiceRequest.Status.READY_FOR_PAYMENT:
            messages.success(
                request,
                "اطلاعات درخواست شما ثبت شد. برای تکمیل درخواست، پرداخت هزینه را انجام دهید."
            )
        else:
            if service_request.status == ServiceRequest.Status.READY_FOR_PAYMENT:
                messages.success(
                    request,
                    "اطلاعات درخواست شما ثبت شد. برای تکمیل درخواست، پرداخت هزینه را انجام دهید."
                )
            else:
                messages.success(
                    request,
                    "درخواست شما با موفقیت ثبت نهایی شد."
                )

        if (
            service_request.status
            == ServiceRequest.Status.READY_FOR_PAYMENT
        ):
            return redirect(
                "cases:payment_checkout",
                tracking_code=service_request.tracking_code,
            )

        return redirect(
            "cases:request_form",
            tracking_code=service_request.tracking_code,
        )

    form_context = UserRequestService.get_form(
        service_request=service_request,
        user=request.user,
    )

    form_schema = []

    for field in form_context["schema"]:
        field = field.copy()
        field["value"] = form_context["data"].get(
            field["key"]
        )
        form_schema.append(field)

    return render(
        request,
        "cases/request_form.html",
        {
            "service_request": service_request,
            "form_schema": form_schema,
        },
    )


@login_required
@require_POST
def submit_request(request, tracking_code):
    service_request = get_object_or_404(
        ServiceRequest,
        tracking_code=tracking_code,
        user=request.user,
    )

    service_request = UserRequestService.submit(
        service_request=service_request,
        user=request.user,
    )

    messages.success(
        request,
        "درخواست شما با موفقیت ثبت نهایی شد.",
    )

    if (
        service_request.status
        == ServiceRequest.Status.READY_FOR_PAYMENT
    ):
        return redirect(
            "cases:payment_checkout",
            tracking_code=service_request.tracking_code,
        )

    return redirect(
        "cases:request_form",
        tracking_code=service_request.tracking_code,
    )


@login_required
def payment_checkout(request, tracking_code):
    service_request = get_object_or_404(
        ServiceRequest.objects.select_related(
            "service",
            "user",
        ),
        tracking_code=tracking_code,
        user=request.user,
    )

    if (
        service_request.status
        != ServiceRequest.Status.READY_FOR_PAYMENT
    ):
        messages.warning(
            request,
            "این درخواست در حال حاضر آماده پرداخت نیست.",
        )

        return redirect(
            "core:home",
        )

    awaiting_payment_exists = (
        service_request.payments
        .filter(
            status=Payment.Status.AWAITING_VERIFICATION,
        )
        .exists()
    )

    if awaiting_payment_exists:
        return redirect(
            "cases:payment_status",
            tracking_code=service_request.tracking_code,
        )

    payment_methods = (
        PaymentAvailabilityService
        .get_available_methods()
    )

    return render(
        request,
        "cases/payment_checkout.html",
        {
            "service_request": service_request,
            "payment_methods": payment_methods,
        },
    )


@login_required
@require_POST
def select_payment_method(request, tracking_code):
    service_request = get_object_or_404(
        ServiceRequest.objects.select_related(
            "service",
            "user",
        ),
        tracking_code=tracking_code,
        user=request.user,
    )

    if (
        service_request.status
        != ServiceRequest.Status.READY_FOR_PAYMENT
    ):
        messages.error(
            request,
            "این درخواست در وضعیت فعلی آماده پرداخت نیست.",
        )

        return redirect(
            "cases:payment_checkout",
            tracking_code=service_request.tracking_code,
        )

    method_code = (
        request.POST.get("method") or ""
    ).strip()

    try:
        method = PaymentMethod.objects.get(
            code=method_code,
        )
    except PaymentMethod.DoesNotExist:
        messages.error(
            request,
            "روش پرداخت انتخاب‌شده معتبر نیست.",
        )

        return redirect(
            "cases:payment_checkout",
            tracking_code=service_request.tracking_code,
        )

    if not PaymentAvailabilityService.is_available(
        method=method,
    ):
        messages.error(
            request,
            "این روش پرداخت در حال حاضر قابل استفاده نیست.",
        )

        return redirect(
            "cases:payment_checkout",
            tracking_code=service_request.tracking_code,
        )

    payment = PaymentService.create_payment(
        service_request=service_request,
        method_code=method.code,
    )

    if method.code == "card_to_card":
        CardToCardPaymentService.prepare_payment(
            payment=payment,
        )

        return redirect(
            "cases:card_to_card_payment",
            tracking_code=service_request.tracking_code,
        )

    messages.error(
        request,
        "این روش پرداخت هنوز عملیاتی نشده است.",
    )

    return redirect(
        "cases:payment_checkout",
        tracking_code=service_request.tracking_code,
    )


@login_required
def card_to_card_payment(request, tracking_code):
    service_request = get_object_or_404(
        ServiceRequest.objects.select_related(
            "service",
            "user",
        ),
        tracking_code=tracking_code,
        user=request.user,
    )

    if (
        service_request.status
        != ServiceRequest.Status.READY_FOR_PAYMENT
    ):
        messages.error(
            request,
            "این درخواست در وضعیت فعلی آماده پرداخت نیست.",
        )

        return redirect(
            "cases:payment_status",
            tracking_code=service_request.tracking_code,
        )

    payment = (
        service_request.payments
        .select_related(
            "method",
            "gateway_provider",
        )
        .filter(
            method__code="card_to_card",
            status=Payment.Status.PENDING,
        )
        .order_by("-created_at")
        .first()
    )

    if payment is None:
        awaiting_payment_exists = (
            service_request.payments
            .filter(
                method__code="card_to_card",
                status=Payment.Status.AWAITING_VERIFICATION,
            )
            .exists()
        )

        if awaiting_payment_exists:
            return redirect(
                "cases:payment_status",
                tracking_code=service_request.tracking_code,
            )

        messages.error(
            request,
            "پرداخت کارت‌به‌کارت برای این درخواست ایجاد نشده است.",
        )

        return redirect(
            "cases:payment_checkout",
            tracking_code=service_request.tracking_code,
        )

    if request.method == "POST":
        payer_reference = (
            request.POST.get("payer_reference") or ""
        ).strip()

        receipt = request.FILES.get("receipt")

        CardToCardPaymentService.submit_payment(
            payment=payment,
            payer_reference=payer_reference,
            receipt=receipt,
        )

        messages.success(
            request,
            "اطلاعات پرداخت شما ثبت شد و در انتظار بررسی است.",
        )

        return redirect(
            "cases:payment_status",
            tracking_code=service_request.tracking_code,
        )

    detail = CardToCardPaymentService.prepare_payment(
        payment=payment,
    )

    return render(
        request,
        "cases/card_to_card_payment.html",
        {
            "service_request": service_request,
            "payment": payment,
            "detail": detail,
        },
    )


@login_required
def payment_status(request, tracking_code):
    service_request = get_object_or_404(
        ServiceRequest.objects.select_related(
            "service",
            "user",
        ),
        tracking_code=tracking_code,
        user=request.user,
    )

    payment = (
        service_request.payments
        .select_related(
            "method",
            "gateway_provider",
        )
        .order_by("-created_at")
        .first()
    )

    if payment is None:
        messages.warning(
            request,
            "برای این درخواست هنوز پرداختی ثبت نشده است.",
        )

        return redirect(
            "cases:payment_checkout",
            tracking_code=service_request.tracking_code,
        )

    return render(
        request,
        "cases/payment_status.html",
        {
            "service_request": service_request,
            "payment": payment,
        },
    )