from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("packages/", views.PackageListView.as_view(), name="packages"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("orders/<str:reference>/", views.OrderStatusView.as_view(), name="order-status"),
    path("transactions/", views.transaction_history, name="transactions"),
    path("webhooks/<str:provider>/", views.WebhookView.as_view(), name="webhook"),
]
