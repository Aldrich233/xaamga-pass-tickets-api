from django.core.management.base import BaseCommand

from home.models import Order


class Command(BaseCommand):
    help = "Génère des order_id uniques pour les commandes existantes"

    def handle(self, *args, **kwargs):
        orders = Order.objects.filter(order_id__isnull=True)
        count = orders.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("Tous les orders ont déjà un order_id."))
            return

        for order in orders:
            order.order_id = order.generate_order_id()
            order.save()

        self.stdout.write(self.style.SUCCESS(f"{count} order_id générés avec succès !"))
