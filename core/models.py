from django.db import models
from zeta.models import Zeta

# UBICACIONES (
    # NOMBRE: ENTRADA, PASILLO, SOFA...
    # N DE MESAS EN ESA SECCION -> UBICACION-MESAS [1:N] 
    # )

# MESAS (
    # NUMERO MESA, 
    # NUMEROS COMENSALES REOMENDADO,
    # -> ? N MESAS EN MAPA [SI ES PARA 1 PERSONA TENDRA 1 UD, SI ES PARA 8 PERSONAS TENDRA 2 UDS], 
    # CADA MESA TENDRÁ ASIGNADA UNA UBICACION Y UNA UBICACION PODRA TENER MUCHAS MESAS -> MESAS-UBICACIONES [N:1])
    # CAMARERO ASIGNADO -> MESAS TIENE 1 CAMARERO ASIGNADO Y UN CAMARERO PUEDE TENER VARIAS MESAS; MESAS-CAMARERO [N:1])

# CUENTA (
    # ID (CADA CUENTA TENDRA UN ID UNICO, SI UNA CUENTA SE CAMBIA DE UNA MESA A OTRA, MANTIENE SU MISMO ID)
    # LA CUENTA DE CADA MESA CON LOS PRODUCTOS -> CUENTAS-PRODUCTOS [N:N] 
        # OPCION A OBSERVACIONES, CAMARERO PUEDA ESCRIBIR ALGO
        # SI UN PRODUCTO YA SE HA ENVIADO (QUE CAMBIE DE ESTADO : PENDIENTE A ENVIADO)
    # FORMA DE PAGO (VISA O CASH),
    # JUNTO O SEPARADO ? -> ABRIR OTRA APP DE COBRO ()
    # CADA CUENTA TENDRÁ ASIGNADA UNA MESA Y UNA MESA PUEDE TENER VARIAS CUENTAS -> CUENTAS-MESAS[N:1]
    #  )

# TICKETS ( 
    # ID DE CADA TICKET 
    # ) 

class Ticket(models.Model):
    # PAYMENT_TYPE = ['VISA', 'CASH', 'TICKET RESTAURANT']
    PAYMENT_TYPE = [("V", "VISA"),
                    ("C", "CASH"),
                    ("T", "TICKET RESTAURANT")]
    
    payment_type = models.CharField("Payment type", choices=PAYMENT_TYPE)
    ticket_datetime = models.DateTimeField("Date and time ticket creation")
    zeta = models.ForeignKey(
        Zeta,
        on_delete=models.PROTECT, # we cannot delete a ticket if
        related_name='tickets',
        verbose_name="ticket"
    )