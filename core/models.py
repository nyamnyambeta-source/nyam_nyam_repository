from decimal import Decimal

from django.db import models
from products.models import Extra, Product, ProductAllowedExtra
from django.conf import settings
from nyam_nyam_1_0.settings import PAYMENT_TYPE
from django.core.validators import MinValueValidator


STATUS = [
    ("P", "PENDING"), 
    ("S", "SENDED"),
    ("D", "DONE"),
    ("DE", "DELIVERED")]


class Section(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)


class Table(models.Model):
    number = models.PositiveIntegerField("Number of table")
    guests_quantity = models.PositiveIntegerField("Number of guests per table", default=2)
    map_units = models.PositiveSmallIntegerField("Quantity of squares in establishment map", default=1, null=True, blank=True)
    busy = models.BooleanField("Table busy", default=False)
    
    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name='tables',
        verbose_name="section's tables"
    )
    waiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='tables',
        verbose_name="waiter's tables",
        null=True,
        blank=True,
        limit_choices_to= {'role': 'worker'}
    )
    
    class Meta():
        unique_together = ("number", "section")
    
    def __str__(self):
        return f"Table n {self.number}; Section {self.section.name}"
    

class Order(models.Model):
    created_at = models.DateTimeField("Date and time of order created", auto_now_add=True)
    closed_at = models.DateTimeField("Date and time of order closed", null=True, blank=True)
    #para controlar estados de una orden (desde panel de cocina por ejemplo)
    # status = models.CharField("Order status", max_length=2, choices=STATUS, default="P")
    observations = models.TextField("Observations", default="", blank=True)

    table = models.ForeignKey(
        Table, 
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="orders of table",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Comanda"
        verbose_name_plural = "Comandas"
        ordering = ['-created_at']

    def __str__(self):
        return f"Comanda #{self.id} - Mesa {self.table.number}: " + ", ".join(item.__str__() for item in self.items.all())
    
    @property
    def total(self):
        return sum((item.total for item in self.items.all()), Decimal("0.00"))
    
    def get_ticket_summary(self):
        return {
            "order_id": self.id,
            "table_id": self.table_id,
            "table_number": self.table.number if self.table else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "observations": self.observations,
            "items": [
                {
                    "order_item_id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product.name,
                    "product_price": str(item.product.price),
                    "observations": item.observations,
                    "extras": [
                        {
                            "order_item_extra_id": extra.id,
                            "extra_id": extra.allowed_extra.extra.id,
                            "extra_name": extra.allowed_extra.extra.name,
                            "unit_price": str(extra.allowed_extra.extra.price),
                            "quantity": extra.quantity,
                            "total": str(extra.total),
                        }
                        for extra in item.extras.all()
                    ],
                    "extras_total": str(item.extras_total),
                    "item_total": str(item.total),
                }
                for item in self.items.all()
            ],
            "order_total": str(self.total),
        }
  

class OrderItem(models.Model):
    status = models.CharField("Order status", max_length=2, choices=STATUS, default="P")
    observations = models.TextField("observations of order product", max_length=100, null=True, blank=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_items',
        verbose_name="producto"
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="comanda"
    )

    class Meta:
        verbose_name = "Productos ordenados dentro de una comanda"

    def __str__(self):
        if self.extras.exists():
            extras_text = ", ".join(
                extra.allowed_extra.extra.name
                for extra in self.extras.all()
            )
            return f"{self.product.name} -> EXTRAS: [{extras_text}]"

        return f"{self.product.name} -> NO EXTRAS"
        
    
    @property
    def extras_total(self):
        return sum(
            (
                extra.quantity * extra.allowed_extra.extra.price
                for extra in self.extras.all()
            ),
            Decimal("0.00")
        )

    @property
    def total(self):
        return self.product.price + self.extras_total
    

class OrderItemExtra(models.Model):
    quantity = models.PositiveIntegerField(default=1)

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='extras',
        verbose_name="línea de comanda"
    )

    allowed_extra = models.ForeignKey(
        ProductAllowedExtra,
        on_delete=models.CASCADE,
        related_name='allowed_extras',
        verbose_name="extra permitido"
    )

    class Meta:
        verbose_name = "Extra seleccionado en comanda"
        verbose_name_plural = "Extras seleccionados en comanda"

    def __str__(self):
        return f"{self.allowed_extra.extra.name} "#- {self.order_item.product.name}"
    
    
    @property
    def total(self):
        return self.allowed_extra.extra.price * self.quantity