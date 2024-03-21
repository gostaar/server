from django.urls import path

from . import views
app_name = "companies"
urlpatterns = [
    path("", views.index, name="index"),
    path("enterprises", views.searchEnterprises, name="search-enterprises"),
    path("enterprises/<int:pk>", views.getEnterprise, name="get-enterprise"),
    path("enterprises/<int:pk>/establishments", views.getEnterpriseEstablishments, name="get-enterprise-establishments")
]