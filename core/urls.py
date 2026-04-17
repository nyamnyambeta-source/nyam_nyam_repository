from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path('config', views.config_view, name='config'),
    
    #kitchen
    path('kitchen/', views.kitchen_screen_view, name='kitchen_screen'),
    path('kitchen/<str:str_type>', views.refresh_orders_view, name='refresh_orders'),
    path('kitchen/items/<int:item_id>/ok/', views.kitchen_item_ok_view, name='kitchen_item_ok'),
    path('kitchen/orders/<int:order_id>/ok/', views.kitchen_order_ok_view, name='kitchen_order_ok'),
    

    # map and tables
    path('', views.index, name="core"),
    path('map', views.table_map_view, name="map"),
    path('map/section/<int:section_id>', views.get_tables_view, name="get_tables"),
    path('tables/<int:table_id>/screen/', views.table_screen_view, name='table_screen'),
    
    # order panels
    path('orders/<int:table_id>/<int:order_id>/', views.order_screen_view, name='order_screen'),
    path('orders/<int:order_id>/categories/<int:category_id>/products/', views.category_products_view, name='category_products'),
    path('orders/<int:order_id>/products/<int:product_id>/add/', views.add_product_form_view, name='add_product_form'),
    
    # order actions
    path('orders/<int:order_id>/send/', views.send_order_view, name='send_order'),
    path('orders/<int:order_id>/divide/', views.divide_order_view, name='divide_order'),
    # path('orders/<int:order_id>/sleep/', views.divide_order_view, name='divide_order'),    
    path('orders/<int:order_id>/<int:new_order_id>/delete/', views.delete_order_view, name='delete_order'),
    path('orders/<int:order_id>/divide/<int:new_order_id>/', views.confirm_divided_order_view, name='confirm_divide'),
    
    # orderItem actions    
    path('orders/items/<int:item_id>/delete/', views.delete_orderitem_view, name='delete_orderitem'),
    path('orders/<int:order_id>/<int:item_id>/edit/', views.edit_orderitem_view, name='edit_orderitem'),
]
