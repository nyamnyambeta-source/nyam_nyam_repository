from django.db import models
from products.models import Extra, Product, ProductAllowedExtra
from django.conf import settings
from nyam_nyam_1_0.settings import PAYMENT_TYPE
from django.core.validators import MinValueValidator

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
    map_units = models.PositiveSmallIntegerField("Quantity of squares in establishment map", default=1, null=True, blank=True)
    busy = models.BooleanField("Table busy", default=False)
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
    '''STATUS = [
        ("O", "OPENED"), 
        ("A", "ACTIVE"),
        ("C", "CLOSED")
    ]'''
    #puede que sea mejor quitarlo y que esta opcion sea valida en ticket; cuando se va a pagar un order -> se crea ticket -> seleccionas metodo de pago
    #payment_type = models.CharField("Payment type", max_length=20, choices=PAYMENT_TYPE) #puede que sea mejor quitarlo y que esta opcion sea valida en ticket
    created_at = models.DateTimeField("Date and time of order created", auto_now_add=True)
    closed_at = models.DateTimeField("Date and time of order closed", null=True, blank=True, default=models.SET_NULL)
    #status = models.CharField("order status", max_length=1, choices=STATUS, default="O")
    observations = models.TextField("observations", default=" ", blank=True)

    table = models.ForeignKey(
        Table, 
        on_delete=models.PROTECT,
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
        return f"Comanda #{self.id} - Mesa {self.table.number}"
  

class OrderItem(models.Model):
    sended = models.BooleanField("product order sended", default=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
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
        return f"{self.product.name} - Comanda #{self.order.id}"
    

class OrderItemExtra(models.Model):
    quantity = models.PositiveIntegerField(default=1)
    
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='selected_extras',
        verbose_name="línea de comanda"
    )

    allowed_extra = models.ForeignKey(
        ProductAllowedExtra,
        on_delete=models.PROTECT,
        related_name='order_item_extras',
        verbose_name="extra permitido"
    )

    class Meta:
        verbose_name = "Extra seleccionado en comanda"
        verbose_name_plural = "Extras seleccionados en comanda"

    def __str__(self):
        return f"{self.allowed_extra.extra.name} - {self.order_item.product.name}"