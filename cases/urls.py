from django.urls import path

from cases import views


app_name = "cases"


urlpatterns = [
    path(
        "start/<slug:service_slug>/",
        views.start_request,
        name="start_request",
    ),
    path(
        "<str:tracking_code>/payment/",
        views.payment_checkout,
        name="payment_checkout",
    ),
    path(
        "<str:tracking_code>/submit/",
        views.submit_request,
        name="submit_request",
    ),    
    path(
        "<str:tracking_code>/",
        views.request_form,
        name="request_form",
    ),
    path(
        "<str:tracking_code>/payment/select/",
        views.select_payment_method,
        name="select_payment_method",
    ),
    path(
        "<str:tracking_code>/payment/card-to-card/",
        views.card_to_card_payment,
        name="card_to_card_payment",
    ),
    path(
        "<str:tracking_code>/payment/status/",
        views.payment_status,
        name="payment_status",
    ),

]
