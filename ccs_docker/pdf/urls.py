from django.urls import path

from ccs_docker.pdf import views

app_name = "pdf"

urlpatterns = [
    path("crimes/<uuid:uuid>/pdf", views.crime_pdf, name="crime-detail-pdf"),
    path("criminals/<uuid:uuid>/pdf", views.criminal_pdf, name="criminal-detail-pdf"),
]
