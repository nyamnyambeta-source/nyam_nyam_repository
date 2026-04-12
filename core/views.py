from datetime import datetime
from decimal import Decimal

from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.http import Http404
from django.db.models import Q, Sum
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.urls import reverse

from core.models import Order, OrderItem, OrderItemExtra, Table
from products.models import Category, Product, ProductAllowedExtra
from zeta.models import Operation, Ticket, Zeta


def render_screen(request, template_name, context=None):
    context = context or {}

    if request.headers.get("HX-Request") == "true":
        return render(request, template_name, context)

    return render(request, "core/base.html", {
        **context,
        "content_template": template_name,
    })


def get_active_zeta(zeta_id=None):
    
    try:
        if zeta_id is None or int(zeta_id) == 0:
            zeta = Zeta.objects.filter(closed_at__isnull=True).order_by('opened_at').first()
            
            if zeta is None:
                zeta = Zeta.objects.create()
        else:
            zeta = get_object_or_404(Zeta, id=zeta_id)
        return zeta
    
    except Exception as e:
        print(e)


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


@require_GET
def config_view(request):
    return render_screen(request, "core/configuration_screen.html")


@require_GET
def operations_view(request, zeta_id):
    try:
        print("Entra a operations_view")
        selected_zeta = get_active_zeta(zeta_id)
        zetas = Zeta.objects.all().order_by("-opened_at")

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
            Q(payment_type="C") | Q(payment_type="CASH")
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        total_visa_amount = operations.filter(
            Q(payment_type="V") | Q(payment_type="VISA")
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        return render_screen(request, "core/zeta_sales_screen.html", {
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
        return render(request, "core/configuration_screen.html")


@require_GET
def zeta_view(request, zeta_id):
    zeta = get_report_zeta(zeta_id)
    totals = get_zeta_totals(zeta)

    return render_screen(request, "core/zeta_report.html", {
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
        response = render(request, "core/zeta_report.html", {
            "zeta": zeta,
            "operations": totals["operations"],
            "total_operations": totals["total_operations"],
            "total_cash_amount": totals["total_cash_amount"],
            "total_visa_amount": totals["total_visa_amount"],
            "total_amount": totals["total_amount"],
        })
        response["HX-Push-Url"] = reverse("core:zeta_inform", args=[zeta.id])
        return response

    return redirect("core:zeta_inform", zeta_id=zeta.id)


def index(request):
    return render(request, "core/base.html")


def table_map_view(request):

    try:
        tables = Table.objects.all().select_related('section')

        open_orders = Order.objects.filter(closed_at__isnull=True)

        return render_screen(request, "core/map.html", {
            'tables': tables,
            'open_orders': open_orders,
        })
    except Exception as e:
        raise Http404(e)



def table_screen_view(request, table_id):

    print("TABLE ID ", table_id)
    try:
        table = get_object_or_404(Table, id=table_id)
        orders = Order.objects.filter(table_id=table.id, closed_at__isnull=True).order_by('created_at')

        if not orders:
            new_order = Order.objects.create(
                table=table,
                #waiter=request.user if request.user.is_authenticated else None
            )
            
            orders = [new_order]

        print("ANtes de return")

        print(orders)
        return render_screen(request, 'core/table_screen.html', {
            'table': table,
            'orders': orders,
        })
    except Exception as e:
        print("ERROR: ", e)
        return redirect("core:map")
    

def order_screen_view(request, table_id, order_id):
    
    try:
        print("Ha entrado a ORDER_SCREEN_VIEW")
        table = Table.objects.get(id=table_id)
        order = Order.objects.get(id=order_id)
        orders = Order.objects.filter(table=table, closed_at__isnull=True).order_by('created_at')
        categories = Category.objects.filter(active=True).order_by('name')
        products = Product.objects.filter(active=True).select_related('category').order_by('name')
        
        return render_screen(request, 'core/order_screen.html', {
            'table': table,
            'order': order,
            'orders': orders,
            'categories': categories,
            'products': products,
        })
    except Exception as e:
        print("order_screen_view method: ", e)
        return redirect("core:map")


def category_products_view(request, order_id, category_id):
    
    try:
        order = get_object_or_404(Order, id=order_id, closed_at__isnull=True)

        if category_id == 0:
            products = Product.objects.filter(active=True).select_related('category').order_by('name')
        else:
            category = get_object_or_404(Category, id=category_id, active=True)
            products = Product.objects.filter(
                active=True,
                category=category
            ).select_related('category').order_by('name')

        return render(request, 'core/blocks/products_block.html', {
            'order': order,
            'products': products,
        })
    
    except:
        return redirect("/error")


@require_http_methods(["GET", "POST"])
def add_product_form_view(request, order_id, product_id):
    order = get_object_or_404(Order, id=order_id, closed_at__isnull=True)
    product = get_object_or_404(Product, id=product_id, active=True)

    allowed_extras = ProductAllowedExtra.objects.filter(
        product=product,
        active=True,
        extra__active=True
    ).select_related(
        'extra'
    ).order_by(
        'extra__name'
    )

    if request.method == 'POST':
        selected_extra_ids = request.POST.getlist('extras')
        observations = request.POST.get('observations', '').strip()

        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            sended=False,
            observations=observations
        )

        allowed_extras_map = {
            str(ae.id): ae
            for ae in allowed_extras
        }

        extras_to_create = []

        for extra_id in selected_extra_ids:
            allowed_extra = allowed_extras_map.get(str(extra_id))
            if not allowed_extra:
                continue

            quantity_raw = request.POST.get(f'quantity_{extra_id}', '1')

            try:
                quantity = int(quantity_raw)
            except (TypeError, ValueError):
                quantity = 1

            if quantity < 1:
                quantity = 1

            if quantity > allowed_extra.max_quantity:
                quantity = allowed_extra.max_quantity

            extras_to_create.append(
                OrderItemExtra(
                    order_item=order_item,
                    allowed_extra=allowed_extra,
                    quantity=quantity
                )
            )

        if extras_to_create:
            OrderItemExtra.objects.bulk_create(extras_to_create)

        order = Order.objects.prefetch_related(
            'items__product',
            'items__extras__allowed_extra__extra'
        ).get(id=order.id)

        return render(request, 'core/blocks/orders_block.html', {
            'order': order,
        })

    return render(request, 'core/blocks/add_product_form.html', {
        'order': order,
        'product': product,
        'allowed_extras': allowed_extras,
    })


@require_http_methods(["POST"])
def send_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, closed_at__isnull=True)
    order.items.filter(sended=False).update(sended=True)
    
    order = Order.objects.prefetch_related(
        'items__product',
        'items__extras__allowed_extra__extra'
    ).get(id=order.id)

    return render(request, 'core/blocks/orders_block.html', {
        'order': order,
    })


def get_total_paid(order):
    return order.operations.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")


def get_total_pending(order):
    return order.total - get_total_paid(order)


@require_GET
def close_order_view(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("table").prefetch_related("tickets"),
        id=order_id
    )

    total_paid = get_total_paid(order)
    total_pending = order.total - total_paid
    print(total_pending)

    return render(request, "core/blocks/payment_block.html", {
        "order": order,
        "total_paid": total_paid,
        "total_pending": total_pending,
    })


@require_http_methods(["GET", "POST"])
def create_operation_view(request, order_id):
    
    try: 
        order = Order.objects.get(id=order_id)        
        table = Table.objects.get(id=order.table.id)
        print(request)
        
        total_paid = get_total_paid(order)
        print("TOTAL PAID: ", total_paid)
        total_pending = order.total - total_paid
        payment_success = False
            
        if request.method == 'POST' and request.POST.get('payment_type') in ('VISA', 'CASH'):
            payment_type = request.POST.get('payment_type')
            request_amount = Decimal(request.POST.get('request_amount'))
            print("AMOUNT: ", request_amount)
            # every "sale order" generates a new operation
            # one order could have 3 tickets: 
            # order of 20€ -> 10€ cash; 5€ visa; 5€ cash (every operation payed for different person)  
            operation = Operation.objects.create(payment_type=payment_type, amount=request_amount, order=order, zeta=get_active_zeta())                        
            
            if request_amount > 0:
                if request_amount == total_pending:
                    total_pending = 0   
                    total_paid = order.total
                elif request_amount < total_pending:
                    total_pending -= request_amount
                    total_paid += request_amount
                else:
                    total_paid = order.total
                    
                    if payment_type == 'CASH': 
                        total_pending -= request_amount
                        _operation = Operation.objects.create(payment_type, payment_type, amount=total_pending, order=order, zeta=get_active_zeta())
                    else:
                        total_pending *= -1
                        
                                    
            print("TOTAL PAID: ", total_paid)
            print("TOTAL PENDING: ", total_pending)
                
            return render(request, "core/blocks/payment_block.html", {
                "order":order,
                "total_paid":total_paid,
                "total_pending": total_pending,
                "payment_success":payment_success,
            })  
        else:
                        # Falta que devuelva el cambio (hx-get y actualizar el importe #form-amount) 
            return render(request, "core/blocks/payment_block.html", {
                    "order": order,
                    "total_paid": total_paid,
                    "total_pending": total_pending,
                    "payment_succes": payment_success,
                })
        
    except Exception as e:
        print("ERROR: ", e)
        
        
@require_GET
def create_ticket_view(request, order_id):
    
    try:
        order = Order.objects.get(id=order_id)
        visa_amount = order.operations.filter(payment_type='VISA').aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        cash_amount = order.operations.filter(payment_type='CASH').aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        
        print("VISA AMOUNT: ", visa_amount)
        print("CASH AMOUNT: ", cash_amount)

        ticket = Ticket.objects.create(
            visa_amount=visa_amount,
            cash_amount=cash_amount, 
            total_amount=order.total,
            ticket_summary=order.get_ticket_summary(),
            order=order,
        )
        
        order.delete()
        
        print("Lo borró")
        tables = Table.objects.select_related("section", "waiter").all()
        return render(request, "core/map.html", {"tables":tables})
    
    except Exception as e:
        print("erroorooro: ", e)
        
        
@require_http_methods(["POST"])
def delete_order_view(request, order_id):

    try:
        order = get_object_or_404(Order, id=order_id)

        order.delete()

        tables = Table.objects.select_related("section", "waiter").all()

        return render(request, "core/map.html", {
            "tables": tables,
        })
    except Exception as e:
        print(e)
        return render(request, 'core/map.html',
                      {"tables": tables})


@require_http_methods(["GET"])
def divide_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_order = Order.objects.create(table=order.table)

    return render(request, "core/blocks/divide_order_block.html", {
        "order": order,
        "new_order":      new_order,
    })


@require_http_methods(["POST"])
def confirm_divided_order_view(request, order_id, new_order_id):
    order = get_object_or_404(Order, id=order_id)
    new_order = get_object_or_404(Order, id=new_order_id)

    # IDs de items que el usuario arrastró a la nueva orden
    moved_item_ids = request.POST.getlist("moved_items")

    if len(moved_item_ids) > 0:
        # Reasignar los OrderItem seleccionados a la nueva orden
        order.items.filter(id__in=moved_item_ids).update(order=new_order)

        # Si la nueva orden quedó vacía (el usuario no movió nada), borrarla
    else:
        new_order.delete()
        return render(request, "core/blocks/orders_block.html", {
            "order":  order,
        })

    # Si la orden original quedó vacía, borrarla también
    if not order.items.exists():
        order.delete()

    table  = new_order.table
    orders = table.orders.order_by("created_at")

    return render(request, "core/blocks/orders_block.html", {
           "order":  new_order,
    })
    
