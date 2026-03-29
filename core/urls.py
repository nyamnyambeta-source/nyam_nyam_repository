from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path('', views.index, name="core"),
    path('map', views.table_map_view, name="map"),
    path('tables/<int:table_id>/screen/', views.order_panel_view, name='order'),
    path('orders/<int:order_id>/categories/<int:category_id>/products/', views.category_products_view, name='category_products'),
    path('orders/<int:order_id>/products/<int:product_id>/add/', views.add_product_form_view, name='add_product_form'),
    path('orders/<int:order_id>/send/', views.send_order_view, name='send_order'),
    path('orders/<int:order_id>/close/', views.close_order_view, name='close_order'),
]
