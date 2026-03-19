from django.contrib import admin
from core.models import Ticket
from products.models import Product, Category, Extra, ProductAllowedExtra
from zeta.models import Zeta


admin.site.register(Ticket)
# admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Extra)
admin.site.register(ProductAllowedExtra)
admin.site.register(Zeta)