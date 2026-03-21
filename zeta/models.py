from django.db import models
from django.core.validators import MinValueValidator
from nyam_nyam_1_0.settings import PAYMENT_TYPE

class Zeta(models.Model):
    opened_at = models.DateTimeField("Datetime report created", auto_now_add=True)
    closed_at = models.DateTimeField("Datetime report closed")
    total_operations = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_visa_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    total_cash_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)


# TICKETS ( 
# ID DE CADA TICKET 
class Ticket(models.Model):
    payment_type = models.CharField("Payment type", max_length=20, choices=PAYMENT_TYPE)
    ticket_datetime = models.DateTimeField("Date and time ticket creation", auto_now_add=True)
    zeta = models.ForeignKey(
        Zeta,
        on_delete=models.PROTECT, # protect the tickets in case of delete zeta
        related_name='tickets',
        verbose_name="zeta"
    )
    order = models.ForeignKey(
        'core.Order', 
        on_delete=models.PROTECT,
        related_name="tickets"
    )
    
    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"