from django.urls import path

from .views import (
    service_list,
    service_detail,
)
app_name = "services"
urlpatterns = [
    path(
        "",
        service_list,
        name="service_list",
    ),

    path(
        "<slug:slug>/",
        service_detail,
        name="service_detail",
    ),
]