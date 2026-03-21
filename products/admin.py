from django.contrib import admin
from .models import Category, Extra, Product, ProductAllowedExtra

# admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Extra)
admin.site.register(ProductAllowedExtra)

class ProductAllowedExtraInline(admin.TabularInline):
    model = ProductAllowedExtra
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'active')
    list_filter = ('category', 'active')
    search_fields = ('name',)
    inlines = [ProductAllowedExtraInline]
