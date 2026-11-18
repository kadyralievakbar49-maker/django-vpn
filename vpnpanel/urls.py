from django.urls import path

from . import views

app_name = "vpnpanel"

urlpatterns = [
    path("", views.index, name="index"),
    path("toggle/", views.toggle, name="toggle"),
    path("status/", views.status_api, name="status"),
]
