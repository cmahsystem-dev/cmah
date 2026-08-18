from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.html import format_html

from payments.models import (
    CardToCardDestination,
    CardToCardPaymentDetail,
    GatewayProvider,
    Payment,
    PaymentMethod,
)
from payments.services.card_to_card_payment_service import (
    CardToCardPaymentService,
)


class CardToCardReviewForm(forms.Form):
    class Decision:
        APPROVE = "approve"
        REJECT = "reject"

    decision = forms.ChoiceField(
        label="نتیجه بررسی",
        choices=[
            (
                Decision.APPROVE,
                "تأیید پرداخت",
            ),
            (
                Decision.REJECT,
                "رد پرداخت",
            ),
        ],
        widget=forms.RadioSelect,
    )

    rejection_reason = forms.CharField(
        label="دلیل رد",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "در صورت رد پرداخت، دلیل را وارد کنید.",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        decision = cleaned_data.get("decision")
        rejection_reason = (
            cleaned_data.get("rejection_reason") or ""
        ).strip()

        if (
            decision == self.Decision.REJECT
            and not rejection_reason
        ):
            self.add_error(
                "rejection_reason",
                "دلیل رد پرداخت الزامی است.",
            )

        cleaned_data["rejection_reason"] = (
            rejection_reason
        )

        return cleaned_data


class ProtectedHistoryAdminMixin:
    """
    اگر رکورد سابقه Payment داشته باشد، حذف مستقیم ممنوع است.

    Bulk delete نیز به‌طور کامل غیرفعال می‌شود تا حذف گروهی
    نتواند قوانین سابقه مالی را دور بزند.
    """

    def get_actions(self, request):
        actions = super().get_actions(request)

        actions.pop(
            "delete_selected",
            None,
        )

        return actions

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        if (
            obj is not None
            and obj.payments.exists()
        ):
            return False

        return super().has_delete_permission(
            request,
            obj,
        )


@admin.register(PaymentMethod)
class PaymentMethodAdmin(
    ProtectedHistoryAdminMixin,
    admin.ModelAdmin,
):
    list_display = (
        "title",
        "code",
        "is_active",
        "priority",
        "payment_count",
        "updated_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "title",
        "code",
        "description",
    )

    ordering = (
        "priority",
        "id",
    )

    list_editable = (
        "is_active",
        "priority",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "payment_count",
    )

    fieldsets = (
        (
            "اطلاعات روش پرداخت",
            {
                "fields": (
                    "code",
                    "title",
                    "description",
                    "icon",
                ),
            },
        ),
        (
            "وضعیت نمایش",
            {
                "fields": (
                    "is_active",
                    "priority",
                ),
            },
        ),
        (
            "اطلاعات سیستم",
            {
                "fields": (
                    "payment_count",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(
        description="تعداد پرداخت‌ها",
    )
    def payment_count(self, obj):
        if not obj.pk:
            return 0

        return obj.payments.count()


@admin.register(GatewayProvider)
class GatewayProviderAdmin(
    ProtectedHistoryAdminMixin,
    admin.ModelAdmin,
):
    list_display = (
        "title",
        "code",
        "is_active",
        "priority",
        "payment_count",
        "updated_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "title",
        "code",
        "description",
    )

    ordering = (
        "priority",
        "id",
    )

    list_editable = (
        "is_active",
        "priority",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "payment_count",
    )

    fieldsets = (
        (
            "اطلاعات درگاه",
            {
                "fields": (
                    "code",
                    "title",
                    "description",
                    "logo",
                ),
            },
        ),
        (
            "وضعیت",
            {
                "fields": (
                    "is_active",
                    "priority",
                ),
            },
        ),
        (
            "اطلاعات سیستم",
            {
                "fields": (
                    "payment_count",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(
        description="تعداد پرداخت‌ها",
    )
    def payment_count(self, obj):
        if not obj.pk:
            return 0

        return obj.payments.count()


class CardToCardPaymentDetailInline(
    admin.StackedInline
):
    model = CardToCardPaymentDetail

    extra = 0
    max_num = 1
    can_delete = False

    readonly_fields = (
        "payer_reference",
        "receipt",
        "submitted_at",
        "verified_by",
        "verified_at",
        "rejection_reason",
        "created_at",
        "updated_at",
    )

    fields = (
        "payer_reference",
        "receipt",
        "submitted_at",
        "verified_by",
        "verified_at",
        "rejection_reason",
        "created_at",
        "updated_at",
    )

    def has_add_permission(
        self,
        request,
        obj=None,
    ):
        return False


@admin.register(CardToCardDestination)
class CardToCardDestinationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "bank_name",
        "masked_card_number",
        "account_holder",
        "is_active",
        "priority",
        "payment_count",
        "updated_at",
    )

    list_filter = (
        "is_active",
        "bank_name",
    )

    search_fields = (
        "title",
        "card_number",
        "iban",
        "account_holder",
        "bank_name",
    )

    ordering = (
        "priority",
        "id",
    )

    list_editable = (
        "is_active",
        "priority",
    )

    readonly_fields = (
        "payment_count",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "اطلاعات کارت",
            {
                "fields": (
                    "title",
                    "card_number",
                    "iban",
                    "account_holder",
                    "bank_name",
                    "description",
                ),
            },
        ),
        (
            "وضعیت",
            {
                "fields": (
                    "is_active",
                    "priority",
                ),
            },
        ),
        (
            "اطلاعات سیستم",
            {
                "fields": (
                    "payment_count",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        if (
            obj is not None
            and obj.payment_details.exists()
        ):
            return False

        return super().has_delete_permission(
            request,
            obj,
        )

    @admin.display(
        description="شماره کارت",
    )
    def masked_card_number(self, obj):
        number = obj.card_number.replace(
            " ",
            "",
        ).replace(
            "-",
            "",
        )

        if len(number) < 8:
            return obj.card_number

        return (
            f"{number[:4]}-"
            f"****-****-"
            f"{number[-4:]}"
        )

    @admin.display(
        description="تعداد پرداخت‌ها",
    )
    def payment_count(self, obj):
        if not obj.pk:
            return 0

        return obj.payment_details.count()


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "service_request",
        "amount",
        "method",
        "gateway_provider",
        "status",
        "reference_id",
        "paid_at",
        "review_action",
        "created_at",
    )

    list_filter = (
        "status",
        "method",
        "gateway_provider",
        "created_at",
    )

    search_fields = (
        "service_request__tracking_code",
        "reference_id",
        "authority",
        "card_to_card_detail__payer_reference",
    )

    list_select_related = (
        "service_request",
        "method",
        "gateway_provider",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "service_request",
        "amount",
        "method",
        "gateway_provider",
        "status",
        "authority",
        "reference_id",
        "paid_at",
        "card_to_card_review_link",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "پرداخت",
            {
                "fields": (
                    "service_request",
                    "amount",
                    "status",
                ),
            },
        ),
        (
            "روش پرداخت",
            {
                "fields": (
                    "method",
                    "gateway_provider",
                ),
            },
        ),
        (
            "اطلاعات تراکنش",
            {
                "fields": (
                    "authority",
                    "reference_id",
                    "paid_at",
                ),
            },
        ),
        (
            "بررسی پرداخت",
            {
                "fields": (
                    "card_to_card_review_link",
                ),
            },
        ),
        (
            "اطلاعات سیستم",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    inlines = (
        CardToCardPaymentDetailInline,
    )

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "<int:payment_id>/review-card-to-card/",
                self.admin_site.admin_view(
                    self.review_card_to_card_view
                ),
                name=(
                    "payments_payment_"
                    "review_card_to_card"
                ),
            ),
        ]

        return custom_urls + urls

    def has_add_permission(self, request):
        # Payment فقط باید از Service Layer ساخته شود.
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        # سابقه مالی هیچ‌وقت از Admin حذف نمی‌شود.
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)

        actions.pop(
            "delete_selected",
            None,
        )

        return actions

    def _review_url(self, payment):
        return reverse(
            "admin:payments_payment_review_card_to_card",
            kwargs={
                "payment_id": payment.pk,
            },
        )

    def _is_reviewable_card_to_card(
        self,
        payment,
    ):
        return (
            payment.method_id is not None
            and payment.method.code == "card_to_card"
            and (
                payment.status
                == Payment.Status.AWAITING_VERIFICATION
            )
        )

    @admin.display(
        description="بررسی",
    )
    def review_action(self, obj):
        if not self._is_reviewable_card_to_card(
            obj
        ):
            return "-"

        return format_html(
            '<a class="button" href="{}">'
            "بررسی پرداخت"
            "</a>",
            self._review_url(obj),
        )

    @admin.display(
        description="عملیات بررسی",
    )
    def card_to_card_review_link(
        self,
        obj,
    ):
        if not obj or not obj.pk:
            return "-"

        if not self._is_reviewable_card_to_card(
            obj
        ):
            return (
                "این پرداخت در حال حاضر "
                "نیاز به بررسی کارت‌به‌کارت ندارد."
            )

        return format_html(
            '<a class="button" href="{}">'
            "بررسی و تعیین نتیجه پرداخت"
            "</a>",
            self._review_url(obj),
        )

    def review_card_to_card_view(
        self,
        request,
        payment_id,
    ):
        payment = get_object_or_404(
            Payment.objects.select_related(
                "method",
                "gateway_provider",
                "service_request",
                "service_request__user",
            ),
            pk=payment_id,
        )

        if not self.has_change_permission(
            request,
            payment,
        ):
            self.message_user(
                request,
                "شما اجازه بررسی این پرداخت را ندارید.",
                level=messages.ERROR,
            )

            return HttpResponseRedirect(
                reverse(
                    "admin:payments_payment_changelist"
                )
            )

        if not self._is_reviewable_card_to_card(
            payment
        ):
            self.message_user(
                request,
                (
                    "این پرداخت در وضعیت فعلی "
                    "قابل بررسی کارت‌به‌کارت نیست."
                ),
                level=messages.WARNING,
            )

            return HttpResponseRedirect(
                reverse(
                    "admin:payments_payment_change",
                    args=[
                        payment.pk,
                    ],
                )
            )

        try:
            detail = payment.card_to_card_detail

        except CardToCardPaymentDetail.DoesNotExist:
            self.message_user(
                request,
                (
                    "جزئیات پرداخت کارت‌به‌کارت "
                    "برای این Payment وجود ندارد."
                ),
                level=messages.ERROR,
            )

            return HttpResponseRedirect(
                reverse(
                    "admin:payments_payment_change",
                    args=[
                        payment.pk,
                    ],
                )
            )

        if request.method == "POST":
            form = CardToCardReviewForm(
                request.POST,
            )

            if form.is_valid():
                decision = (
                    form.cleaned_data["decision"]
                )

                if (
                    decision
                    == CardToCardReviewForm.Decision.APPROVE
                ):
                    CardToCardPaymentService.approve(
                        payment=payment,
                        verified_by=request.user,
                    )

                    self.message_user(
                        request,
                        "پرداخت با موفقیت تأیید شد.",
                        level=messages.SUCCESS,
                    )

                else:
                    CardToCardPaymentService.reject(
                        payment=payment,
                        verified_by=request.user,
                        rejection_reason=(
                            form.cleaned_data[
                                "rejection_reason"
                            ]
                        ),
                    )

                    self.message_user(
                        request,
                        "پرداخت رد شد.",
                        level=messages.WARNING,
                    )

                return HttpResponseRedirect(
                    reverse(
                        "admin:payments_payment_change",
                        args=[
                            payment.pk,
                        ],
                    )
                )

        else:
            form = CardToCardReviewForm()

        context = {
            **self.admin_site.each_context(
                request
            ),
            "title": "بررسی پرداخت کارت‌به‌کارت",
            "opts": self.model._meta,
            "payment": payment,
            "detail": detail,
            "form": form,
            "original": payment,
        }

        return render(
            request,
            (
                "admin/payments/payment/"
                "card_to_card_review.html"
            ),
            context,
        )