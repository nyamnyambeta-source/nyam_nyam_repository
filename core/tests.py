from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import Order, OrderItem, OrderItemExtra, Section, Table
from products.models import Category, Extra, Product, ProductAllowedExtra
from zeta.models import Operation, Ticket


class PaymentFlowTests(TestCase):
    def setUp(self):
        self.section = Section.objects.create(name="Sala")
        self.table = Table.objects.create(number=7, section=self.section)
        self.category = Category.objects.create(name="Cafeteria")
        self.product = Product.objects.create(
            name="Tostada",
            price=Decimal("10.00"),
            category=self.category,
        )
        self.order = Order.objects.create(table=self.table)
        OrderItem.objects.create(order=self.order, product=self.product)

    def test_partial_and_final_payment_create_operations_and_final_ticket(self):
        payment_url = reverse("zeta:create_operation", args=[self.order.id])

        first_response = self.client.post(payment_url, {
            "request_amount": "4.00",
            "payment_type": "C",
        })
        self.assertEqual(first_response.status_code, 200)

        self.order.refresh_from_db()
        self.assertIsNone(self.order.closed_at)
        self.assertEqual(Operation.objects.filter(order=self.order).count(), 1)
        self.assertFalse(Ticket.objects.filter(order=self.order).exists())

        first_operation = Operation.objects.get(order=self.order)
        self.assertEqual(first_operation.payment_type, "C")
        self.assertEqual(first_operation.amount, Decimal("4.00"))

        second_response = self.client.post(payment_url, {
            "request_amount": "6.00",
            "payment_type": "V",
        })
        self.assertEqual(second_response.status_code, 200)

        self.order.refresh_from_db()
        self.assertIsNotNone(self.order.closed_at)
        self.assertEqual(Operation.objects.filter(order=self.order).count(), 2)

        ticket = Ticket.objects.get(order=self.order)
        self.assertEqual(ticket.cash_amount, Decimal("4.00"))
        self.assertEqual(ticket.visa_amount, Decimal("6.00"))
        self.assertEqual(ticket.total_amount, Decimal("10.00"))
        self.assertEqual(ticket.ticket_summary["table_number"], self.table.number)
        self.assertEqual(len(ticket.ticket_summary["items"]), 1)
        self.assertEqual(len(ticket.ticket_summary["payments"]), 2)

        open_orders = Order.objects.filter(table=self.table, closed_at__isnull=True)
        self.assertEqual(open_orders.count(), 1)
        self.assertNotEqual(open_orders.first().id, self.order.id)

    def test_alias_route_accepts_legacy_payload_and_rejects_overpayment(self):
        legacy_url = reverse("zeta:create_ticket", args=[self.order.id])

        response = self.client.post(legacy_url, {
            "amount": "15.00",
            "payment_type": "cash",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El importe no puede superar el pendiente.")
        self.assertEqual(Operation.objects.count(), 0)
        self.assertEqual(Ticket.objects.count(), 0)


class EditOrderItemViewTests(TestCase):
    def setUp(self):
        self.section = Section.objects.create(name="Sala")
        self.table = Table.objects.create(number=3, section=self.section)
        self.category = Category.objects.create(name="Bocadillos")
        self.product = Product.objects.create(
            name="Bocadillo bacon y queso",
            price=Decimal("3.50"),
            category=self.category,
        )
        self.extra_bacon = Extra.objects.create(name="Bacon", price=Decimal("1.50"))
        self.extra_queso = Extra.objects.create(name="Queso", price=Decimal("1.00"))
        self.allowed_bacon = ProductAllowedExtra.objects.create(
            product=self.product,
            extra=self.extra_bacon,
            max_quantity=3,
        )
        self.allowed_queso = ProductAllowedExtra.objects.create(
            product=self.product,
            extra=self.extra_queso,
            max_quantity=2,
        )
        self.order = Order.objects.create(table=self.table)
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            observations="Sin cambios",
        )
        OrderItemExtra.objects.create(
            order_item=self.order_item,
            allowed_extra=self.allowed_bacon,
            quantity=1,
        )

    def test_get_edit_orderitem_view_returns_prefilled_form(self):
        response = self.client.get(
            reverse("core:edit_orderitem", args=[self.order.id, self.order_item.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar Bocadillo bacon y queso")
        self.assertContains(response, 'value="1"')
        self.assertContains(response, "Sin cambios")

    def test_post_edit_orderitem_updates_extras_and_observations(self):
        response = self.client.post(
            reverse("core:edit_orderitem", args=[self.order.id, self.order_item.id]),
            {
                "observations": "Sin tomate",
                "extras": [str(self.allowed_queso.id)],
                f"quantity_{self.allowed_queso.id}": "2",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.observations, "Sin tomate")

        extras = list(
            self.order_item.extras.select_related("allowed_extra__extra").order_by(
                "allowed_extra__extra__name"
            )
        )
        self.assertEqual(len(extras), 1)
        self.assertEqual(extras[0].allowed_extra_id, self.allowed_queso.id)
        self.assertEqual(extras[0].quantity, 2)


class DeleteOrderItemViewTests(TestCase):
    def setUp(self):
        self.section = Section.objects.create(name="Terraza")
        self.table = Table.objects.create(number=5, section=self.section)
        self.category = Category.objects.create(name="Bebidas")
        self.product = Product.objects.create(
            name="Cafe con leche",
            price=Decimal("1.80"),
            category=self.category,
        )
        self.extra = Extra.objects.create(name="Leche fria", price=Decimal("0.20"))
        self.allowed_extra = ProductAllowedExtra.objects.create(
            product=self.product,
            extra=self.extra,
            max_quantity=2,
        )
        self.order = Order.objects.create(table=self.table)
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            observations="Templado",
        )
        OrderItemExtra.objects.create(
            order_item=self.order_item,
            allowed_extra=self.allowed_extra,
            quantity=1,
        )

    def test_post_delete_orderitem_removes_item_and_returns_order_panel(self):
        response = self.client.post(
            reverse("core:delete_orderitem", args=[self.order_item.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(OrderItem.objects.filter(id=self.order_item.id).exists())
        self.assertContains(response, "No hay productos")
