from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    #sales and operations
    path('config', views.config_view, name='config'),
    path('operations/<int:zeta_id>', views.operations_view, name='operations'),
    path('inform/<int:zeta_id>', views.zeta_view, name='zeta_inform'),
    path('close/<int:zeta_id>', views.close_zeta_view, name='close_zeta'),
    # map and tables
    path('', views.index, name="core"),
    path('map', views.table_map_view, name="map"),
    path('tables/<int:table_id>/screen/', views.table_screen_view, name='table_screen'),
    # order panels
    path('orders/<int:table_id>/<int:order_id>/', views.order_screen_view, name='order_screen'),
    path('orders/<int:order_id>/categories/<int:category_id>/products/', views.category_products_view, name='category_products'),
    path('orders/<int:order_id>/products/<int:product_id>/add/', views.add_product_form_view, name='add_product_form'),
    # order actions
    path('orders/<int:order_id>/send/', views.send_order_view, name='send_order'),
    path('orders/<int:order_id>/close/', views.close_order_view, name='close_order'),
    path('orders/<int:order_id>/create_operation/', views.create_operation_view, name='create_operation'),
    path('orders/<int:order_id>/create_ticket/', views.create_ticket_view, name='create_ticket'),
    path('orders/<int:order_id>/delete/', views.delete_order_view, name='delete_order'),
    path('orders/<int:order_id>/divide/', views.divide_order_view, name='divide_order'),
    path('orders/<int:order_id>/divide/<int:new_order_id>/', views.confirm_divided_order_view, name='confirm_divide'),
]
