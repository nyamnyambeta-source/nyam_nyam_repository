from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from core.models import Order, OrderItem, OrderItemExtra, Section, Table
from products.models import Category, Product, ProductAllowedExtra


def render_screen(request, template_name, context=None):
    context = context or {}

    if request.headers.get("HX-Request") == "true":
        return render(request, template_name, context)

    return render(request, "core/base.html", {
        **context,
        "content_template": template_name,
    })


def get_map_context():
    return {
        "sections": Section.objects.all(),
        "tables": Table.objects.all(),
        "open_orders": list(
            Order.objects.filter(closed_at__isnull=True).values_list("table_id", flat=True)
        ),
    }


@require_GET
def config_view(request): return render_screen(request, "core/configuration_screen.html")


@require_GET
def kitchen_screen_view(request): return render_screen(request, "core/kitchen_screen.html") 


def refresh_orders_view(request):
    orders = Order.objects.filter(closed_at__isnull=True, items__isnull=False).distinct()#.prefetch_related("products")#.prefetch_related("items","items__extras")#.select_related("table").order_by("table__number").prefetch_related("items")
    
    print(orders)
    
    #for order in orders:
        #print(order.id, "; MESA: ", order.table.number, "; ITEMS: ", order.items.all(), "\n")
    for order in orders:
        print("ORDER ", order.id)
        for item in order.items.all():
            print(item.product)
        
    return render_screen(request, "core/blocks/kitchen_pass_orders_block.html", {"orders":orders})



def index(request):
    return render(request, "core/base.html")


def table_map_view(request):
    try:
        return render_screen(request, "core/map.html", get_map_context())
    except Exception as e:
        raise Http404(e)


@require_GET
def get_tables_view(request, section_id):
    try:
        tables = Table.objects.none()

        if section_id == 0:
            tables = Table.objects.all()
        else:
            tables = get_object_or_404(Section, id=section_id).tables.all()

        return render_screen(request, "core/blocks/tables_section_block.html", {
            "tables": tables,
            "open_orders": list(
                Order.objects.filter(closed_at__isnull=True).values_list("table_id", flat=True)
            ),
        })
    except Exception as e:
        print(e)
        return redirect("core:map")


def table_screen_view(request, table_id):
    try:
        table = get_object_or_404(Table, id=table_id)
        orders = Order.objects.filter(
            table_id=table.id,
            closed_at__isnull=True,
        ).order_by("created_at")

        if not orders:
            new_order = Order.objects.create(table=table)
            orders = [new_order]

        return render_screen(request, "core/table_screen.html", {
            "table": table,
            "orders": orders,
        })
    except Exception as e:
        print("ERROR: ", e)
        return redirect("core:map")


def order_screen_view(request, table_id, order_id):
    try:
        table = Table.objects.get(id=table_id)
        order = Order.objects.get(id=order_id)
        orders = Order.objects.filter(
            table=table,
            closed_at__isnull=True,
        ).order_by("created_at")
        categories = Category.objects.filter(active=True).order_by("name")
        products = Product.objects.filter(active=True).select_related("category").order_by("name")

        return render_screen(request, "core/order_screen.html", {
            "table": table,
            "order": order,
            "orders": orders,
            "categories": categories,
            "products": products,
        })
    except Exception as e:
        print("order_screen_view method: ", e)
        return redirect("core:map")


def category_products_view(request, order_id, category_id):
    try:
        order = get_object_or_404(Order, id=order_id, closed_at__isnull=True)

        if category_id == 0:
            products = Product.objects.filter(active=True).select_related("category").order_by("name")
        else:
            category = get_object_or_404(Category, id=category_id, active=True)
            products = Product.objects.filter(
                active=True,
                category=category,
            ).select_related("category").order_by("name")

        return render(request, "core/blocks/products_block.html", {
            "order": order,
            "products": products,
        })
    except Exception:
        return redirect("/error")


@require_http_methods(["GET", "POST"])
def add_product_form_view(request, order_id, product_id):
    order = get_object_or_404(Order, id=order_id, closed_at__isnull=True)
    product = get_object_or_404(Product, id=product_id, active=True)

    allowed_extras = ProductAllowedExtra.objects.filter(
        product=product,
        active=True,
        extra__active=True,
    ).select_related("extra").order_by("extra__name")

    if request.method == "POST":
        selected_extra_ids = request.POST.getlist("extras")
        observations = request.POST.get("observations", "").strip()
        quantity_orderitem = int(request.POST.get("quantity_orderitem"))

        for _ in range(quantity_orderitem):
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                observations=observations,
            )

            allowed_extras_map = {
                str(allowed_extra.id): allowed_extra
                for allowed_extra in allowed_extras
            }
            extras_to_create = []

            for extra_id in selected_extra_ids:
                allowed_extra = allowed_extras_map.get(str(extra_id))

                if not allowed_extra:
                    continue

                quantity_raw = request.POST.get(f"quantity_{extra_id}", "1")

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
                        quantity=quantity,
                    )
                )

            if extras_to_create:
                OrderItemExtra.objects.bulk_create(extras_to_create)

            order = Order.objects.prefetch_related(
                "items__product",
                "items__extras__allowed_extra__extra",
            ).get(id=order.id)

        return render(request, "core/blocks/orders_block.html", {
            "order": order,
        })

    return render(request, "core/blocks/add_product_form.html", {
        "order": order,
        "product": product,
        "allowed_extras": allowed_extras,
    })


@require_http_methods(["POST"])
def send_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.items.filter(status="P").update(status="S")

    order = Order.objects.prefetch_related(
        "items__product",
        "items__extras__allowed_extra__extra",
    ).get(id=order.id)

    return render(request, "core/blocks/orders_block.html", {
        "order": order,
    })


@require_http_methods(["POST"])
def delete_order_view(request, order_id, new_order_id):
    try:
        order = get_object_or_404(Order, id=order_id)

        if new_order_id == 0:
            order.delete()
            return render_screen(request, "core/map.html", get_map_context())

        get_object_or_404(Order, id=new_order_id).delete()
        return order_screen_view(request, order.table.id, order.id)
    except Exception as e:
        print(e)
        return render_screen(request, "core/map.html", get_map_context())

@require_http_methods(["POST"])
def delete_orderitem_view(request, item_id):
    order_item = get_object_or_404(
        OrderItem.objects.select_related("order", "product").prefetch_related(
            "extras__allowed_extra__extra"
        ),
        id=item_id,
        order__closed_at__isnull=True,
    )
    order = order_item.order

    order_item.delete()
    order = Order.objects.prefetch_related(
        "items__product",
        "items__extras__allowed_extra__extra",
    ).get(id=order.id)

    return render(request, "core/blocks/orders_block.html", {
        "order": order,
    })

@require_http_methods(["GET", "POST"])
def edit_orderitem_view(request, order_id, item_id):
    order = get_object_or_404(Order, id=order_id, closed_at__isnull=True)
    order_item = get_object_or_404(
        OrderItem.objects.select_related("product", "order").prefetch_related(
            "extras__allowed_extra__extra"
        ),
        id=item_id,
        order=order,
    )
    allowed_extras = ProductAllowedExtra.objects.filter(
        product=order_item.product,
        active=True,
        extra__active=True,
    ).select_related("extra").order_by("extra__name")

    selected_extras = {
        extra.allowed_extra_id: extra
        for extra in order_item.extras.all()
    }

    for allowed_extra in allowed_extras:
        selected_extra = selected_extras.get(allowed_extra.id)
        allowed_extra.is_selected = selected_extra is not None
        allowed_extra.selected_quantity = selected_extra.quantity if selected_extra else 1

    if request.method == "POST":
        selected_extra_ids = request.POST.getlist("extras")
        observations = request.POST.get("observations", "").strip()

        order_item.observations = observations
        order_item.save(update_fields=["observations"])
        order_item.extras.all().delete()

        allowed_extras_map = {
            str(allowed_extra.id): allowed_extra
            for allowed_extra in allowed_extras
        }
        extras_to_create = []

        for extra_id in selected_extra_ids:
            allowed_extra = allowed_extras_map.get(str(extra_id))

            if not allowed_extra:
                continue

            quantity_raw = request.POST.get(f"quantity_{extra_id}", "1")

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
                    quantity=quantity,
                )
            )

        if extras_to_create:
            OrderItemExtra.objects.bulk_create(extras_to_create)

        order = Order.objects.prefetch_related(
            "items__product",
            "items__extras__allowed_extra__extra",
        ).get(id=order.id)

        return render(request, "core/blocks/orders_block.html", {
            "order": order,
        })

    return render(request, "core/blocks/edit_orderitem_form.html", {
        "order": order,
        "order_item": order_item,
        "allowed_extras": allowed_extras,
    })
    

#def delete_orderItem_view(request, )

@require_http_methods(["GET"])
def divide_order_view(request, order_id):
    order = get_object_or_404(Order, id=int(order_id))
    new_order = Order.objects.create(table=order.table)

    return render(request, "core/blocks/divide_order_block.html", {
        "order": order,
        "new_order": new_order,
    })


@require_http_methods(["POST"])
def confirm_divided_order_view(request, order_id, new_order_id):
    order = get_object_or_404(Order, id=order_id)
    new_order = get_object_or_404(Order, id=new_order_id)
    moved_item_ids = request.POST.getlist("moved_items")

    if len(moved_item_ids) > 0:
        order.items.filter(id__in=moved_item_ids).update(order=new_order)
    else:
        new_order.delete()
        return render(request, "core/blocks/orders_block.html", {
            "order": order,
        })

    if not order.items.exists():
        order.delete()

    return render(request, "core/blocks/orders_block.html", {
        "order": new_order,
    })
