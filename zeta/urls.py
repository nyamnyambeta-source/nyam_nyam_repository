from django.urls import path

from . import views

app_name = "zeta"

urlpatterns = [
    path("operations/<int:zeta_id>", views.operations_view, name="operations"),
    path("inform/<int:zeta_id>", views.zeta_view, name="zeta_inform"),
    path("close/<int:zeta_id>", views.close_zeta_view, name="close_zeta"),
    path("orders/<int:order_id>/close/", views.close_order_view, name="close_order"),
    path("orders/<int:order_id>/create_operation/", views.create_operation_view, name="create_operation"),
    path("orders/<int:order_id>/create_ticket/", views.create_ticket_view, name="create_ticket"),
]
