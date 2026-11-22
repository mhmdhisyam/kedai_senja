from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField("Nama kategori", max_length=60, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Kategori"
        verbose_name_plural = "Kategori"

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(
        Category,
        verbose_name="Kategori",
        on_delete=models.PROTECT,  # kategori yang masih punya menu tidak bisa dihapus
        related_name="items",
    )
    name = models.CharField("Nama menu", max_length=100)
    description = models.TextField("Deskripsi", blank=True)
    price = models.PositiveIntegerField(
        "Harga (Rp)",
        validators=[MinValueValidator(1000, "Harga minimal Rp 1.000.")],
    )
    stock = models.PositiveIntegerField("Stok porsi", default=0)
    is_available = models.BooleanField("Dijual", default=True)
    image = models.ImageField("Foto", upload_to="menu/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category__name", "name"]
        verbose_name = "Menu"
        verbose_name_plural = "Menu"
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"],
                name="uniq_menu_name_per_category",
                violation_error_message="Menu dengan nama ini sudah ada di kategori tersebut.",
            )
        ]

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.is_available and self.stock <= 5


class Order(models.Model):
    class Status(models.TextChoices):
        PAID = "paid", "Lunas"
        CANCELLED = "cancelled", "Dibatalkan"

    class Payment(models.TextChoices):
        CASH = "cash", "Tunai"
        QRIS = "qris", "QRIS"
        CARD = "card", "Kartu"

    customer_name = models.CharField("Nama / nomor meja", max_length=80, blank=True)
    payment_method = models.CharField(
        "Pembayaran", max_length=10, choices=Payment.choices, default=Payment.CASH
    )
    total = models.PositiveIntegerField(default=0)
    cash_received = models.PositiveIntegerField("Uang diterima", null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PAID)
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Kasir",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Pesanan"
        verbose_name_plural = "Pesanan"

    def __str__(self):
        return f"Pesanan {self.number}"

    @property
    def number(self):
        return f"#{self.pk:04d}"

    @property
    def change(self):
        """Kembalian untuk pembayaran tunai."""
        if self.cash_received is None:
            return None
        return self.cash_received - self.total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    # SET_NULL: menu boleh dihapus tanpa merusak riwayat pesanan
    menu_item = models.ForeignKey(
        MenuItem, null=True, blank=True, on_delete=models.SET_NULL, related_name="order_items"
    )
    # Salinan nama & harga saat transaksi, supaya riwayat tidak berubah jika menu diedit
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.quantity}x {self.name}"

    @property
    def subtotal(self):
        return self.price * self.quantity
