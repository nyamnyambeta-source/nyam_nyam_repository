from django.db import models
# Validator to validate image extensions
from django.core.validators import FileExtensionValidator, MinValueValidator
import os

# NOMBRE
# PRECIO
# IMAGEN 
# SECCION (CAFETERIA, COMIDA, BEBIDA, VITRINA...)
# EXTRAS (DE PAGO (EXTRA DE QUESO, EXTRA DE BACON... ) Y DE NO PAGO (EXTRA DE AZUCAR, CON TOMATE EN EL BOCADILLO, LECHE FRÍA, HUEVO POCO HECHO...))

# ImageField get the path of settings.py/MEDIA_URL
def get_media_products_path(instance, filename):
    return os.path.join('products', filename)


# Different categories ['Cafés', 'Bebidas', 'Bocadillos', 'Vitrina', etc.]
class Category(models.Model):
    name = models.CharField("nombre", max_length=100, unique=True)
    active = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']

    def __str__(self):
        return self.name


# Class base of extras, the admin/user/worker can add all extras they want with prices for each one
class Extra(models.Model):
    name = models.CharField("nombre", max_length=100, unique=True)
    price = models.DecimalField("precio", max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    active = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "Extra"
        verbose_name_plural = "Extras"
        ordering = ['name']
        unique_together = ("name", "price")

    def __str__(self):
        if self.price > 0:
            return f"{self.name} (+{self.price}€)"
        return self.name


# Class Product: CocaCola, Café, Bocadillo, Croissant, etc. 
class Product(models.Model):
    name = models.CharField("name", max_length=100)
    price = models.DecimalField("price", max_digits=8, decimal_places=2)
    active = models.BooleanField("activo", default=True)
    kitchen = models.BooleanField("Kitchen product", default=False)
    image = models.ImageField(
        "image",
        upload_to=get_media_products_path,
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'bmp'])],
        default=os.path.join('products', 'colacao.bmp')
    )
    # Relationship with Category (ManyToOne) - One category can have many products but one product belongs to only one category
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT, # we dont delete the products related to a category
        related_name='products',
        verbose_name="categoría"
    )
    # description = models.TextField("descripción", blank=True)

    # Relationship with Extra (ManyToMany) - One Product can have many extras and one extra can be in many products
    # The different thing here is that we manage the intermediate table (ProductAllowedExtra) because we control the extras allowed in one product, 
    # if we dont do that we could pick a "cafe con queso"
    allowed_extras = models.ManyToManyField(
        Extra,
        through='ProductAllowedExtra',
        related_name='allowed_extras',
        blank=True,
        verbose_name="extras permitidos"
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        unique_together = ("name", "category", "price")
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductAllowedExtra(models.Model):
    # required = models.BooleanField("obligatorio", default=False)
    max_quantity = models.PositiveIntegerField("cantidad máxima", default=1) # in the case of free extra like 'leche fria', 'sacarina' we dont have to specify the quantity 
                    # but in paid extras can be that a customer wnat 2 extra of cheese 
    active = models.BooleanField("activo", default=True)
    
    # Indicates which product is related
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='allowed_extra_links',
        verbose_name="producto"
    )
    # Indicates which extra is related
    extra = models.ForeignKey(
        Extra,
        on_delete=models.PROTECT,
        related_name='allowed_in_products',
        verbose_name="extra"
    )


    class Meta:
        verbose_name = "Extra permitido en producto"
        verbose_name_plural = "Extras permitidos en productos"
        constraints = [
        models.UniqueConstraint(
            fields=['product', 'extra'],
            name='unique_product_allowed_extra'
        )
    ]
        ordering = ['product__name', 'extra__name']

    def __str__(self):
        return f"{self.product.name} -> {self.extra.name}"