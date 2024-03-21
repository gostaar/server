from django.urls import path
from .views import MyTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from . import views

urlpatterns = [
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("orders/", views.getAllOrders, name="orders"),
    path("orders/<str:pk>", views.getOrderById, name="get-order"),
    path("orders/<str:pk>/update", views.updateOrder, name="update-order"),
    path("orders/<str:pk>/history", views.getOrderHistory, name="order-history"),
    path("order/", views.createOrder, name="create"),
    path("order/<str:pk>/abandon", views.abandonOrder, name="abandon-order"),
    path("order-status", views.getAllOrderStatus, name="order-status"),
    path("contact/<str:pk>", views.deleteContact, name="delete-contact"),
    path("order-line/<str:pk>", views.deleteOrderLine, name="delete-order-line"),
    path("attachments/delete", views.deleteAttachements, name="delete-attachments"),
    path("attachment", views.uploadFile, name="upload-file"),
    path("file-types", views.getAllFileTypes, name="file-types"),
    path("attachment/<str:pk>/type", views.changeFileType, name="change-file-type"),
    path("alerts", views.getAlerts, name="get-alerts"),
]