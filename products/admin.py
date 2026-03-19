from django.contrib import admin
from .models import Category, Extra, Product, ProductAllowedExtra


class ProductAllowedExtraInline(admin.TabularInline):
    model = ProductAllowedExtra
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    inlines = [ProductAllowedExtraInline]
