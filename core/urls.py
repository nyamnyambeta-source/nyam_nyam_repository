from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path('', views.index, name="core"),
    path('map', views.table_map_view, name="map"),
    path('tables/<int:table_id>/screen/', views.table_screen_view, name='table_screen'),
    
    path('orders/<int:table_id>/<int:order_id>/', views.order_screen_view, name='order_screen'),
    path('orders/<int:order_id>/categories/<int:category_id>/products/', views.category_products_view, name='category_products'),
    path('orders/<int:order_id>/products/<int:product_id>/add/', views.add_product_form_view, name='add_product_form'),
    path('orders/<int:order_id>/send/', views.send_order_view, name='send_order'),
    path('orders/<int:order_id>/close/', views.close_order_view, name='close_order'),
    path('orders/<int:order_id>/create_operation/', views.create_operation_view, name='create_operation'),
    path('orders/<int:order_id>/create_ticket/', views.create_ticket_view, name='create_ticket'),
    path('orders/<int:order_id>/delete/', views.delete_order_view, name='delete_order'),
    path('orders/<int:order_id>/divide/', views.divide_order_view, name='divide_order'),
]
