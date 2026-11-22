from django.core.management.base import BaseCommand

from menu.models import Category, MenuItem

DATA = {
    "Kopi": [
        ("Espresso", 18000, 40, "Shot tunggal biji arabika, pekat dan bersih."),
        ("Es Kopi Susu Aren", 24000, 35, "Espresso, susu segar, dan gula aren cair."),
        ("Flat White", 28000, 25, "Double shot dengan susu microfoam tipis."),
        ("V60 Manual Brew", 30000, 12, "Biji single origin pilihan barista hari ini."),
    ],
    "Non-Kopi": [
        ("Matcha Latte", 28000, 20, "Matcha Uji dengan susu oat atau susu sapi."),
        ("Teh Tarik Hangat", 18000, 30, "Teh pekat, susu kental manis, dikocok sampai berbusa."),
        ("Cokelat Panas", 25000, 3, "Cokelat pekat 60% dengan sedikit garam laut."),
    ],
    "Makanan Berat": [
        ("Nasi Goreng Kampung", 32000, 18, "Telur ceplok, kerupuk, dan acar."),
        ("Mie Kuah Pedas", 27000, 0, "Mie telur, sawi, bakso, dan sambal rumahan."),
    ],
    "Camilan": [
        ("Pisang Goreng Keju", 20000, 22, "Pisang kepok, keju parut, susu kental manis."),
        ("Croissant Butter", 22000, 8, "Dipanggang pagi hari, renyah di luar."),
        ("Kentang Goreng", 19000, 15, "Bumbu garam rosemary dengan saus sambal."),
    ],
}


class Command(BaseCommand):
    help = "Isi database dengan contoh kategori dan menu."

    def handle(self, *args, **options):
        created = 0
        for cat_name, items in DATA.items():
            category, _ = Category.objects.get_or_create(name=cat_name)
            for name, price, stock, desc in items:
                _, was_created = MenuItem.objects.get_or_create(
                    category=category,
                    name=name,
                    defaults={
                        "price": price,
                        "stock": stock,
                        "description": desc,
                        "is_available": stock > 0,
                    },
                )
                created += was_created
        self.stdout.write(self.style.SUCCESS(f"Selesai. {created} menu baru ditambahkan."))
