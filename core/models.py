from django.db import models
from products.models import Product
from zeta.models import Ticket
from django.conf import settings
from nyam_nyam_1_0.settings import PAYMENT_TYPE

# UBICACIONES (
    # NOMBRE: ENTRADA, PASILLO, SOFA...
    # N DE MESAS EN ESA SECCION -> UBICACION-MESAS [1:N] 
    # )

class Section(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)


# MESAS (
    # NUMERO MESA, 
    # NUMEROS COMENSALES REOMENDADO,
    # -> ? N MESAS EN MAPA [SI ES PARA 1 PERSONA TENDRA 1 UD, SI ES PARA 8 PERSONAS TENDRA 2 UDS], 
    # CADA MESA TENDRÁ ASIGNADA UNA UBICACION Y UNA UBICACION PODRA TENER MUCHAS MESAS -> MESAS-UBICACIONES [N:1])
    # CAMARERO ASIGNADO -> MESAS TIENE 1 CAMARERO ASIGNADO Y UN CAMARERO PUEDE TENER VARIAS MESAS; MESAS-CAMARERO [N:1])

class Table(models.Model):
    number = models.PositiveIntegerField("Number of table")
    guests_quantity = models.PositiveIntegerField("Number of guests per table", default=2)
    map_quantity = models.PositiveSmallIntegerField("Quantity of squares in establishment map", default=1, null=True, blank=True)
    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT, # protect the tables in case of delete section
        related_name='tables',
        verbose_name="section's tables"
    )
    waiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT, # protect the tables in case of delete waiter
        related_name='tables',
        verbose_name="waiter's tables",
        null=True,
        blank=True,
        limit_choices_to= {'role': 'worker'}
    )

    
# MESAS (
    # NUMERO MESA, 
    # NUMEROS COMENSALES REOMENDADO,
    # -> ? N MESAS EN MAPA [SI ES PARA 1 PERSONA TENDRA 1 UD, SI ES PARA 8 PERSONAS TENDRA 2 UDS], 
    # CADA MESA TENDRÁ ASIGNADA UNA UBICACION Y UNA UBICACION PODRA TENER MUCHAS MESAS -> MESAS-UBICACIONES [N:1])
    # CAMARERO ASIGNADO -> MESAS TIENE 1 CAMARERO ASIGNADO Y UN CAMARERO PUEDE TENER VARIAS MESAS; MESAS-CAMARERO [N:1])

class Table(models.Model):
    number = models.PositiveIntegerField("Number of table")
    recommended_guests = models.PositiveIntegerField("Number of guests per table", default=2)
    map_units = models.PositiveSmallIntegerField("Number of units in establishment map", default=1, null=True, blank=True)
    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT, # protect the tables in case of delete section
        related_name='tables',
        verbose_name="section tables"
    )

    class Meta:
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"
        ordering = ['number']
        unique_together = ('number', 'section')


# CUENTA (
    # ID (CADA CUENTA TENDRA UN ID UNICO, SI UNA CUENTA SE CAMBIA DE UNA MESA A OTRA, MANTIENE SU MISMO ID)
    # LA CUENTA DE CADA MESA CON LOS PRODUCTOS -> CUENTAS-PRODUCTOS [N:N] 
        # OPCION A OBSERVACIONES, CAMARERO PUEDA ESCRIBIR ALGO
        # SI UN PRODUCTO YA SE HA ENVIADO (QUE CAMBIE DE ESTADO : PENDIENTE A ENVIADO)
    # FORMA DE PAGO (VISA O CASH),
    # JUNTO O SEPARADO ? -> ABRIR OTRA APP DE COBRO ()
    # CADA CUENTA TENDRÁ ASIGNADA UNA MESA Y UNA MESA PUEDE TENER VARIAS CUENTAS -> CUENTAS-MESAS[N:1]
    #  )


class Order(models.Model):
    STATUS = [
        ("O", "OPENED"), 
        ("A", "ACTIVE"),
        ("C", "CLOSED")
    ]
    payment_type = models.CharField("Payment type", max_length=20, choices=PAYMENT_TYPE)
    created_at = models.DateTimeField("Date and time of order created", auto_now_add=True)
    status = models.CharField("order status", choices=STATUS, default="O")
    table = models.ForeignKey(
        Table, 
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name="orders of table"
    )
    products = models.ManyToManyField(
        Product,
        through='ProductsInOrder',
        related_name='products_in_order',
        blank=True,
        verbose_name="products in order"
    )
    # if the table want to pay separate, the order will have two or more ticket


class ProductsInOrder(models.Model):
    sended = models.BooleanField("products order sended", default=False)
    
    # si en una primera instancia piden 2 cafes con leche, se sirven y luego 1 más, que solo envíe el último café pedido con sus respectivos extras/detalles
    #quantity_ordered = models.IntegerField("Number of products ordered", default=0)
    #quantity_delivered = models.IntegerField("Number of products delivered", default=0)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="products_ordered"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT
    )

    class Meta:
        verbose_name = "Productos ordenados dentro de una comanda"

