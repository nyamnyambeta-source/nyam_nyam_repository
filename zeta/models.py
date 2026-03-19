from django.db import models
from django.core.validators import MinValueValidator


class Zeta(models.Model):
    init_datetime = models.DateTimeField("Datetime report created")
    end_datetime = models.DateTimeField("Datetime report closed")
    total_operations = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_visa_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    total_cash_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)