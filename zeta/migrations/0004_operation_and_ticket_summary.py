from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


ZERO = Decimal("0.00")
VALID_PAYMENT_TYPES = {"C", "V", "T"}
PAYMENT_TYPE_ALIASES = {
    "C": "C",
    "CASH": "C",
    "cash": "C",
    "V": "V",
    "VISA": "V",
    "visa": "V",
    "T": "T",
    "ticket": "T",
    "TICKET RESTAURANT": "T",
}


def normalize_payment_type(raw_payment_type):
    value = (raw_payment_type or "").strip()
    normalized_value = PAYMENT_TYPE_ALIASES.get(value, value)
    if normalized_value in VALID_PAYMENT_TYPES:
        return normalized_value
    return "C"


def migrate_ticket_data(apps, schema_editor):
    Ticket = apps.get_model("zeta", "Ticket")
    Operation = apps.get_model("zeta", "Operation")

    for ticket in Ticket.objects.all().iterator():
        normalized_payment_type = normalize_payment_type(ticket.payment_type)
        amount = ticket.amount or ZERO
        cash_amount = amount if normalized_payment_type == "C" else ZERO
        visa_amount = amount if normalized_payment_type == "V" else ZERO

        ticket.cash_amount = cash_amount
        ticket.visa_amount = visa_amount
        ticket.total_amount = amount
        ticket.ticket_summary = {}
        ticket.save(update_fields=["cash_amount", "visa_amount", "total_amount", "ticket_summary"])

        operation = Operation.objects.create(
            payment_type=normalized_payment_type,
            amount=amount,
            order_id=ticket.order_id,
            zeta_id=ticket.zeta_id,
        )
        Operation.objects.filter(pk=operation.pk).update(operation_datetime=ticket.ticket_datetime)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_alter_orderitem_product_and_more"),
        ("zeta", "0003_alter_ticket_order"),
    ]

    operations = [
        migrations.CreateModel(
            name="Operation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("payment_type", models.CharField(choices=[("V", "VISA"), ("C", "CASH"), ("T", "TICKET RESTAURANT")], max_length=20, verbose_name="Payment type")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))], verbose_name="Total amount")),
                ("operation_datetime", models.DateTimeField(auto_now_add=True, verbose_name="Operation datetime")),
                ("order", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="operations", to="core.order")),
                ("zeta", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="operations", to="zeta.zeta", verbose_name="Zeta operations")),
            ],
            options={
                "verbose_name": "Operation",
                "verbose_name_plural": "Operations",
                "ordering": ["-operation_datetime"],
            },
        ),
        migrations.AddField(
            model_name="ticket",
            name="cash_amount",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))], verbose_name="Cash amount"),
        ),
        migrations.AddField(
            model_name="ticket",
            name="total_amount",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))], verbose_name="Total amount"),
        ),
        migrations.AddField(
            model_name="ticket",
            name="ticket_summary",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="ticket",
            name="visa_amount",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))], verbose_name="Visa amount"),
        ),
        migrations.RunPython(migrate_ticket_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="ticket",
            name="amount",
        ),
        migrations.RemoveField(
            model_name="ticket",
            name="payment_type",
        ),
    ]
