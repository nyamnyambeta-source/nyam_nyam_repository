from decimal import Decimal

from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404

from zeta.models import Operation, Zeta


def get_active_zeta(zeta_id=None):
    if zeta_id is None or int(zeta_id) == 0:
        zeta = Zeta.objects.filter(closed_at__isnull=True).order_by("opened_at").first()

        if zeta is None:
            zeta = Zeta.objects.create()

        return zeta

    return get_object_or_404(Zeta, id=zeta_id)


def get_report_zeta(zeta_id=None):
    if zeta_id is None or int(zeta_id) == 0:
        return Zeta.objects.order_by("-opened_at").first()

    return get_object_or_404(Zeta, id=zeta_id)


def get_zeta_operations(zeta):
    if zeta is None:
        return Operation.objects.none()

    return zeta.operations.select_related("order").order_by("-operation_datetime")


def get_zeta_totals(zeta):
    operations = get_zeta_operations(zeta)
    total_operations = operations.count()
    total_cash_amount = operations.filter(
        Q(payment_type="C") | Q(payment_type="CASH")
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    total_visa_amount = operations.filter(
        Q(payment_type="V") | Q(payment_type="VISA")
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    total_amount = operations.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    return {
        "operations": operations,
        "total_operations": total_operations,
        "total_cash_amount": total_cash_amount,
        "total_visa_amount": total_visa_amount,
        "total_amount": total_amount,
    }


def get_total_paid(order):
    return order.operations.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")


def get_total_pending(order):
    return order.total - get_total_paid(order)
