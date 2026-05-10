from django.urls import path, include

urlpatterns = [
    path("api/pdf/", include("api.urls")),
]
