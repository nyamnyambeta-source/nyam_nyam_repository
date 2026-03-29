from django.shortcuts import get_object_or_404, render

from core.models import Order, OrderItem, OrderItemExtra, Table
from products.models import Category, Product, ProductAllowedExtra


def index(request):
    return render(request, "core/base.html")


def table_map_view(request):
    tables = Table.objects.all().select_related('section')

    open_orders = Order.objects.filter(closed_at__isnull=True)

    return render(request, "core/tables_map.html", {
        'tables': tables,
        'open_orders': open_orders,
    })


def order_panel_view(request, table_id):
    table = get_object_or_404(Table, id=table_id)

    order = Order.objects.filter(table=table, closed_at__isnull=True).first()
    if not order:
        order = Order.objects.create(
            table=table,
            waiter=request.user if request.user.is_authenticated else None
        )

    categories = Category.objects.filter(is_active=True).order_by('name')
    products = Product.objects.filter(is_active=True).select_related('category').order_by('name')

    return render(request, 'core/order_panel.html', {
        'table': table,
        'order': order,
        'categories': categories,
        'products': products,
    })


def category_products_view(request, order_id, category_id):
    order = get_object_or_404(Order, id=order_id, closed_at__isnull=True)

    if category_id == 0:
        products = Product.objects.filter(is_active=True).select_related('category').order_by('name')
    else:
        category = get_object_or_404(Category, id=category_id, is_active=True)
        products = Product.objects.filter(
            is_active=True,
            category=category
        ).select_related('category').order_by('name')

    return render(request, 'core/blocks/products_block.html', {
        'order': order,
        'products': products,
    })


@require_http_methods(["GET", "POST"])
def add_product_form_view(request, order_id, product_id):
    order = get_object_or_404(Order, id=order_id, closed_at__isnull=True)
    product = get_object_or_404(Product, id=product_id, is_active=True)

    allowed_extras = ProductAllowedExtra.objects.filter(
        product=product,
        is_active=True,
        extra__is_active=True
    ).select_related('extra').order_by('extra__name')

    if request.method == 'POST':
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            sended=False
        )

        selected_extra_ids = request.POST.getlist('extras')

        for allowed_extra in allowed_extras:
            if str(allowed_extra.id) in selected_extra_ids:
                OrderItemExtra.objects.create(
                    order_item=order_item,
                    allowed_extra=allowed_extra,
                    quantity=1
                )

        order = Order.objects.prefetch_related(
            'items__product',
            'items__selected_extras__allowed_extra__extra'
        ).get(id=order.id)

        return render(request, 'core/blocks/orders_block.html', {
            'order': order,
        })

    return render(request, 'core/blocks/_add_product_modal.html', {
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
        'items__selected_extras__allowed_extra__extra'
    ).get(id=order.id)

    return render(request, 'core/partials/_order_panel.html', {
        'order': order,
    })


@require_http_methods(["POST"])
def close_order_view(request, order_id):
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

    return render(request, 'core/table_map.html', {
        'tables': tables,
    })
