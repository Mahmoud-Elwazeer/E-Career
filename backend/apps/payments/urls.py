from django.urls import path

from . import views, admin_views

app_name = "payments"

urlpatterns = [
    path("packages/", views.PackageListView.as_view(), name="packages"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("orders/<str:reference>/", views.OrderStatusView.as_view(), name="order-status"),
    path("transactions/", views.transaction_history, name="transactions"),
    path("webhooks/<str:provider>/", views.WebhookView.as_view(), name="webhook"),

    # Admin Financial Control Center (IsAdminRole)
    path("admin/overview/", admin_views.financial_overview, name="admin-overview"),
    path("admin/ledger/", admin_views.ledger_balances, name="admin-ledger"),
    path("admin/reconciliation/", admin_views.reconciliation, name="admin-reconciliation"),
    path("admin/transactions/", admin_views.transactions, name="admin-transactions"),
    path("admin/transactions/export/", admin_views.export_transactions_csv, name="admin-transactions-export"),
    path("admin/refund/", admin_views.issue_refund, name="admin-refund"),
    path("admin/audit/", admin_views.audit_log, name="admin-audit"),
]
