from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator
from nyam_nyam_1_0.settings import PAYMENT_TYPE

class Zeta(models.Model):
    opened_at = models.DateTimeField("Datetime report created", auto_now_add=True)
    closed_at = models.DateTimeField("Datetime report closed", null=True, blank=True)
    total_operations = models.PositiveIntegerField(validators=[MinValueValidator(1)],  null=True, blank=True)
    total_visa_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cash_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2,  null=True, blank=True)

    class Meta:
        verbose_name = "Zeta"
        verbose_name_plural = "Zetas"
        ordering = ['-opened_at']

    def __str__(self):
        return f"Zeta {self.id}: - {self.opened_at:%Y-%m-%d %H:%M}"


# TICKETS ( 
# ID DE CADA TICKET 
class Ticket(models.Model):
    payment_type = models.CharField("Payment type", max_length=20, choices=PAYMENT_TYPE)
    ticket_datetime = models.DateTimeField("Date and time ticket creation", auto_now_add=True)
    amount = models.DecimalField("Total amount", default=0, max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    
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
        ordering = ['-ticket_datetime']

    def __str__(self):
        return f"Ticket {self.id} - Order {self.order_id} - {self.amount}€"