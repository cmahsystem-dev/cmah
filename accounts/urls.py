from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        views.login_view,
        name="login",
    ),
    path(
        "verify/",
        views.verify_otp_view,
        name="verify_otp",
    ),
    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),
]