from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from core.models import Order, Section, Table
from zeta.models import Operation, Ticket, Zeta
from zeta.services import (
    get_active_zeta,
    get_report_zeta,
    get_total_paid,
    get_zeta_totals,
)


def render_screen(request, template_name, context=None):
    context = context or {}

    if request.headers.get("HX-Request") == "true":
        return render(request, template_name, context)

    return render(request, "core/base.html", {
        **context,
        "content_template": template_name,
    })


@require_GET
def operations_view(request, zeta_id):
    try:
        selected_zeta = get_active_zeta(zeta_id)
        zetas = Zeta.objects.all().order_by("-opened_at")

        # last_day = selected_zeta.opened_at.strftime("%d-%m-%Y")
        date_from = request.GET.get("date_from", "")
        date_to = request.GET.get("date_to", "") 

        parsed_date_from = parse_date(date_from)
        parsed_date_to = parse_date(date_to)

        if parsed_date_from:
            zetas = zetas.filter(opened_at__date__gte=parsed_date_from)

        if parsed_date_to:
            zetas = zetas.filter(opened_at__date__lte=parsed_date_to)

        if selected_zeta and zetas.filter(id=selected_zeta.id).exists():
            operations = selected_zeta.operations.all().order_by("-operation_datetime")
        else:
            selected_zeta = None
            operations = Operation.objects.filter(zeta__in=zetas).order_by("-operation_datetime")

        total_cash_amount = operations.filter(
            payment_type__in=("C", "CASH")
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        total_visa_amount = operations.filter(
            payment_type__in=("V", "VISA")
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        return render_screen(request, "zeta/zeta_sales_screen.html", {
            "zetas": zetas,
            "selected_zeta": selected_zeta,
            "operations": operations,
            "total_cash_amount": total_cash_amount,
            "total_visa_amount": total_visa_amount,
            "date_from": date_from,
            "date_to": date_to,
        })
    except Exception as e:
        print(e)
        return redirect("core:config")


@require_GET
def zeta_view(request, zeta_id):
    zeta = get_report_zeta(zeta_id)
    totals = get_zeta_totals(zeta)

    return render_screen(request, "zeta/zeta_report.html", {
        "zeta": zeta,
        "operations": totals["operations"],
        "total_operations": totals["total_operations"],
        "total_cash_amount": totals["total_cash_amount"],
        "total_visa_amount": totals["total_visa_amount"],
        "total_amount": totals["total_amount"],
    })


@require_POST
def close_zeta_view(request, zeta_id):
    zeta = get_active_zeta(zeta_id)

    if zeta is None:
        return redirect("core:config")

    totals = get_zeta_totals(zeta)

    if zeta.closed_at is None:
        zeta.closed_at = timezone.now()

    zeta.total_operations = totals["total_operations"]
    zeta.total_cash_amount = totals["total_cash_amount"]
    zeta.total_visa_amount = totals["total_visa_amount"]
    zeta.total_amount = totals["total_amount"]
    zeta.save(update_fields=[
        "closed_at",
        "total_operations",
        "total_cash_amount",
        "total_visa_amount",
        "total_amount",
    ])

    if request.headers.get("HX-Request") == "true":
        response = render(request, "zeta/zeta_report.html", {
            "zeta": zeta,
            "operations": totals["operations"],
            "total_operations": totals["total_operations"],
            "total_cash_amount": totals["total_cash_amount"],
            "total_visa_amount": totals["total_visa_amount"],
            "total_amount": totals["total_amount"],
        })
        response["HX-Push-Url"] = reverse("zeta:zeta_inform", args=[zeta.id])
        return response

    return redirect("zeta:zeta_inform", zeta_id=zeta.id)


@require_GET
def close_order_view(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("table").prefetch_related("tickets"),
        id=order_id,
    )

    total_paid = get_total_paid(order)
    total_pending = order.total - total_paid

    return render(request, "zeta/blocks/payment_block.html", {
        "order": order,
        "total_paid": total_paid,
        "total_pending": total_pending,
        "payment_attempted": False,
        "payment_success": False,
    })


@require_http_methods(["GET", "POST"])
def create_operation_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    try:
        total_paid = get_total_paid(order)
        total_pending = order.total - total_paid
        payment_success = False
        payment_attempted = request.method == "POST"

        payment_aliases = {
            "V": "VISA",
            "VISA": "VISA",
            "C": "CASH",
            "CASH": "CASH",
        }

        if request.method == "POST":
            payment_type = payment_aliases.get(
                request.POST.get("payment_type", "").upper()
            )
            request_amount = Decimal(request.POST.get("request_amount"))

            if payment_type is not None:
                operation = Operation.objects.create(
                    payment_type=payment_type,
                    amount=request_amount,
                    order=order,
                    zeta=get_active_zeta(),
                )
                payment_success = operation is not None

                print(request_amount)
                print(payment_type)
                
                if request_amount > 0:
                    if request_amount == total_pending:
                        total_pending = 0
                        total_paid = order.total
                    elif request_amount < total_pending:
                        total_pending -= request_amount
                        total_paid += request_amount
                    else:
                        total_paid = order.total

                        if payment_type == "CASH":
                            total_pending -= request_amount
                            Operation.objects.create(
                                payment_type=payment_type,
                                amount=total_pending,
                                order=order,
                                zeta=get_active_zeta(),
                            )
                        else:
                            total_pending *= -1

                return render(request, "zeta/blocks/payment_block.html", {
                    "order": order,
                    "total_paid": total_paid,
                    "total_pending": total_pending,
                    "payment_attempted": True,
                    "payment_success": payment_success,
                })

        return render(request, "zeta/blocks/payment_block.html", {
            "order": order,
            "total_paid": total_paid,
            "total_pending": total_pending,
            "payment_attempted": payment_attempted,
            "payment_success": payment_success,
        })
    except Exception as e:
        print("ERROR: ", e)
        return redirect("core:map")


@require_GET
def create_ticket_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    try:
        visa_amount = order.operations.filter(
            payment_type__in=("V", "VISA")
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        cash_amount = order.operations.filter(
            payment_type__in=("C", "CASH")
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        Ticket.objects.create(
            visa_amount=visa_amount,
            cash_amount=cash_amount,
            total_amount=order.total,
            ticket_summary=order.get_ticket_summary(),
            order=order,
        )

        order.delete()

        sections = Section.objects.all()
        tables = Table.objects.all()
        open_orders = list(
            Order.objects.filter(closed_at__isnull=True).values_list("table_id", flat=True)
        )

        return render_screen(request, "core/map.html", {
            "sections": sections,
            "tables": tables,
            "open_orders": open_orders,
        })
    except Exception as e:
        print("ERROR: ", e)
        return redirect("core:map")
