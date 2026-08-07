from django.urls import path

from . import views


app_name = "cms"


urlpatterns = [

    path(
        "faq/",
        views.faq_list,
        name="faq"
    ),


    path(
        "<slug:slug>/",
        views.page_detail,
        name="page_detail"
    ),

    path(
    "robots.txt",
    views.robots_txt,
    name="robots"
),

]