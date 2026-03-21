from django.contrib import admin
from .models import Section, Order, Table, ProductsInOrder

admin.site.register(Section)
#admin.site.register(Order)
#admin.site.register(Table)
admin.site.register(ProductsInOrder)

class ProductsInOrderInline(admin.TabularInline):
    model = ProductsInOrder
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [ProductsInOrderInline]


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'section') # add User (Waiter) in future