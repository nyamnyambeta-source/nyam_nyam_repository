from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import Order, OrderItem, Section, Table
from products.models import Category, Product
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
        payment_url = reverse("core:create_operation", args=[self.order.id])

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
        legacy_url = reverse("core:create_ticket", args=[self.order.id])

        response = self.client.post(legacy_url, {
            "amount": "15.00",
            "payment_type": "cash",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El importe no puede superar el pendiente.")
        self.assertEqual(Operation.objects.count(), 0)
        self.assertEqual(Ticket.objects.count(), 0)
