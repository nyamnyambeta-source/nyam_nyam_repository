from datetime import datetime, timezone
from decimal import Decimal

from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_GET, require_http_methods
from django.http import Http404
from django.db.models import Sum

from core.models import Order, OrderItem, OrderItemExtra, Table
from products.models import Category, Product, ProductAllowedExtra
from zeta.models import Ticket, Zeta


def index(request):
    return render(request, "core/base.html")


def table_map_view(request):

    try:
        tables = Table.objects.all().select_related('section')

        open_orders = Order.objects.filter(closed_at__isnull=True)

        return render(request, "core/map.html", {
            'tables': tables,
            'open_orders': open_orders,
        })
    except Exception as e:
        raise Http404(e)



def table_screen_view(request, table_id):

    print("TABLE ID ", table_id)
    try:
        table = get_object_or_404(Table, id=table_id)
        orders = Order.objects.filter(table=table, closed_at__isnull=True).order_by('created_at')

        if not orders:
            new_order = Order.objects.create(
                table=table,
                #waiter=request.user if request.user.is_authenticated else None
            )
            
            orders = [new_order]

        print("ANtes de return")

        return render(request, 'core/table_screen.html', {
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
        categories = Category.objects.filter(active=True).order_by('name')
        products = Product.objects.filter(active=True).select_related('category').order_by('name')
        
        return render(request, 'core/order_screen.html', {
            'table': table,
            'order': order,
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
    return order.tickets.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")


def get_total_pending(order):
    return order.total - get_total_paid(order)


def get_active_zeta():
    zeta = Zeta.objects.filter(closed_at__isnull=True).order_by('-opened_at').first()
    if zeta is None:
        zeta = Zeta.objects.create()
    return zeta


@require_GET
def close_order_view(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("table").prefetch_related("tickets"),
        id=order_id
    )

    total_paid = get_total_paid(order)
    total_pending = order.total - total_paid

    return render(request, "core/blocks/payment_block.html", {
        "order": order,
        "total_paid": total_paid,
        "total_pending": total_pending,
    })


@require_http_methods(["GET", "POST"])
def create_ticket_view(request, order_id):
    
    try: 
        print("ENTRO A CREAR TICKET")
        order = get_object_or_404(
            Order.objects.select_related("table").prefetch_related("tickets"),
            id=order_id
        )
        
        table = Order.objects.get(id=order.table.id)
        print(request)
        
        total_paid = get_total_paid(order)
        print("TOTAL PAID: ", total_paid)
        total_pending = order.total - total_paid
        payment_success = False
            
        if request.method == 'POST':
            
            amount_pay = Decimal(request.POST.get('amount'))
            payment_type = request.POST.get('payment_type')
            print("AMOUNT: ", amount_pay)
            
            # every "sale order" generates a new ticket
            # one order could have 3 tickets: 
                # order of 20€ -> 10€ cash; 5€ visa; 5€ cash (every ticket payed for different person)  

            ticket = Ticket.objects.create(
                payment_type=payment_type,
                ticket_datetime=datetime.now(),
                amount=amount_pay,
                #ticket_summary=order.items.toJSON(),
                order=order,
                zeta=get_active_zeta()
            )
            
            payment_success = True if ticket is not None else False
            
            print("TOTAL PAID: ", total_paid)
            print("TOTAL PENDING: ", total_pending)
        
            if total_pending - amount_pay <= 0:
                orders = table.orders
                order.delete()
                total_pending = 0
                total_paid = order.total
                
                return render(request, "core/table_screen.html", {
                    "table":table,
                    "orders":orders
                })
            else:    
                return render(request, "core/blocks/payment_block.html", {
                    "order": order,
                    "total_paid": total_paid,
                    "total_pending": total_pending,
                })
                
        else:
                        # Falta que devuelva el cambio (hx-get y actualizar el importe #form-amount) 
            return render(request, "core/blocks/payment_block.html", {
                    "order": order,
                    "total_paid": total_paid,
                    "total_pending": total_pending,
                    "payment_succes":payment_success,
                })
    except Exception as e:
        print("ERROR: ", e)
        
        
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


@require_http_methods(["POST"])
def divide_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, closed_at__isnull=True)
    order.closed_at = timezone.now()
    order.save(update_fields=['closed_at'])

    tables = Table.objects.select_related('section').all().order_by('section__name', 'number')
    active_orders = {
        order.table_id: order.id
        for order in Order.objects.filter(closed_at__isnull=True)
    }

    for table in tables:
        table.active_order = active_orders.get(table.id)

    return render(request, 'core/map.html', {
        'tables': tables,
    })


