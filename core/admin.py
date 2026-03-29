from django.contrib import admin
from .models import Section, Order, Table, OrderItem, OrderItemExtra

admin.site.register(Section)
#admin.site.register(Order)
#admin.site.register(Table)
admin.site.register(OrderItem)
admin.site.register(OrderItemExtra)

class ProductsInOrderInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'created_at')
    list_filter = ['created_at']
    inlines = [ProductsInOrderInline]


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'section') # add User (Waiter) in future