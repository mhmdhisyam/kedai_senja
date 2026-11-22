import json
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Avg, Count, F, ProtectedError, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import CategoryForm, MenuItemForm
from .models import Category, MenuItem, Order, OrderItem


# ============================ MENU ==========================================
class MenuListView(LoginRequiredMixin, ListView):
    model = MenuItem
    template_name = "menu/menu_list.html"
    context_object_name = "items"
    paginate_by = 8

    def get_queryset(self):
        qs = MenuItem.objects.select_related("category")
        q = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "")
        status = self.request.GET.get("status", "")

        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        if category.isdigit():
            qs = qs.filter(category_id=category)
        if status == "available":
            qs = qs.filter(is_available=True)
        elif status == "unavailable":
            qs = qs.filter(is_available=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        agg = MenuItem.objects.aggregate(
            total=Count("id"),
            available=Count("id", filter=Q(is_available=True)),
            avg_price=Avg("price"),
        )
        ctx["stats"] = {
            "total": agg["total"],
            "available": agg["available"],
            "unavailable": agg["total"] - agg["available"],
            "avg_price": round(agg["avg_price"] or 0),
        }
        ctx["categories"] = Category.objects.all()

        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["query_string"] = params.urlencode()
        ctx["is_filtered"] = any(self.request.GET.get(k) for k in ("q", "category", "status"))
        ctx["f"] = {
            "q": self.request.GET.get("q", ""),
            "category": self.request.GET.get("category", ""),
            "status": self.request.GET.get("status", ""),
        }
        return ctx


class MenuCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = "menu/menu_form.html"
    success_url = reverse_lazy("menu:menu_list")
    success_message = "Menu “%(name)s” ditambahkan."


class MenuUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = "menu/menu_form.html"
    success_url = reverse_lazy("menu:menu_list")
    success_message = "Perubahan menu “%(name)s” disimpan."


class MenuDeleteView(LoginRequiredMixin, DeleteView):
    model = MenuItem
    success_url = reverse_lazy("menu:menu_list")
    http_method_names = ["post"]  # konfirmasi lewat dialog di frontend

    def form_valid(self, form):
        name = self.object.name
        if self.object.image:
            self.object.image.delete(save=False)  # bersihkan file foto
        response = super().form_valid(form)
        messages.success(self.request, f"Menu “{name}” dihapus.")
        return response


@require_POST
def toggle_availability(request, pk):
    """Ubah status dijual/habis lewat AJAX tanpa reload halaman."""
    if not request.user.is_authenticated:
        # AJAX: balas 401 (bukan redirect HTML) agar frontend bisa menampilkan pesan yang jelas
        return JsonResponse({"detail": "Sesi berakhir. Silakan masuk lagi."}, status=401)
    item = get_object_or_404(MenuItem, pk=pk)
    item.is_available = not item.is_available
    item.save(update_fields=["is_available", "updated_at"])

    available = MenuItem.objects.filter(is_available=True).count()
    total = MenuItem.objects.count()
    return JsonResponse(
        {
            "is_available": item.is_available,
            "name": item.name,
            "available_count": available,
            "unavailable_count": total - available,
        }
    )


# ============================ KATEGORI ======================================
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "menu/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.annotate(item_count=Count("items"))


class CategoryCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "menu/category_form.html"
    success_url = reverse_lazy("menu:category_list")
    success_message = "Kategori “%(name)s” ditambahkan."


class CategoryUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "menu/category_form.html"
    success_url = reverse_lazy("menu:category_list")
    success_message = "Kategori “%(name)s” diperbarui."


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy("menu:category_list")
    http_method_names = ["post"]

    def form_valid(self, form):
        name = self.object.name
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                f"Kategori “{name}” masih punya menu. Pindahkan atau hapus menunya dulu.",
            )
            return redirect("menu:category_list")
        messages.success(self.request, f"Kategori “{name}” dihapus.")
        return response


# ============================ KASIR & PESANAN ===============================
class OrderError(Exception):
    """Pesanan tidak bisa disimpan; pesan ditampilkan apa adanya ke kasir."""


class PosView(LoginRequiredMixin, View):
    template_name = "menu/pos.html"

    def get(self, request):
        items = MenuItem.objects.filter(is_available=True, stock__gt=0).select_related("category")
        categories = Category.objects.filter(
            items__is_available=True, items__stock__gt=0
        ).distinct()
        return render(
            request,
            self.template_name,
            {"items": items, "categories": categories, "payments": Order.Payment.choices},
        )

    def post(self, request):
        # 1) Baca keranjang dari frontend: [{"id": 1, "qty": 2}, ...]
        try:
            lines = {}
            for row in json.loads(request.POST.get("cart", "[]")):
                pk, qty = int(row["id"]), int(row["qty"])
                if qty < 1:
                    raise ValueError
                lines[pk] = lines.get(pk, 0) + qty
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            messages.error(request, "Keranjang tidak valid. Muat ulang halaman lalu coba lagi.")
            return redirect("menu:pos")

        if not lines:
            messages.error(request, "Pilih minimal satu menu sebelum membayar.")
            return redirect("menu:pos")

        customer = request.POST.get("customer_name", "").strip()[:80]
        payment = request.POST.get("payment_method")
        if payment not in Order.Payment.values:
            payment = Order.Payment.CASH
        cash_raw = request.POST.get("cash_received", "").strip()
        cash = int(cash_raw) if cash_raw.isdigit() else None

        # 2) Harga & stok SELALU dihitung ulang di server (jangan percaya angka dari browser)
        try:
            with transaction.atomic():
                menu = {m.pk: m for m in MenuItem.objects.select_for_update().filter(pk__in=lines)}
                total = 0
                for pk, qty in lines.items():
                    m = menu.get(pk)
                    if m is None:
                        raise OrderError("Ada menu yang sudah dihapus. Muat ulang halaman kasir.")
                    if not m.is_available:
                        raise OrderError(f"{m.name} sedang tidak dijual.")
                    if qty > m.stock:
                        raise OrderError(f"Stok {m.name} tinggal {m.stock}.")
                    total += m.price * qty

                if payment == Order.Payment.CASH and cash is not None and cash < total:
                    raise OrderError("Uang yang diterima kurang dari total pesanan.")

                order = Order.objects.create(
                    customer_name=customer,
                    payment_method=payment,
                    total=total,
                    cash_received=cash if payment == Order.Payment.CASH else None,
                    cashier=request.user,
                )
                OrderItem.objects.bulk_create(
                    [
                        OrderItem(
                            order=order,
                            menu_item=menu[pk],
                            name=menu[pk].name,
                            price=menu[pk].price,
                            quantity=qty,
                        )
                        for pk, qty in lines.items()
                    ]
                )
                for pk, qty in lines.items():
                    MenuItem.objects.filter(pk=pk).update(stock=F("stock") - qty)
        except OrderError as exc:
            messages.error(request, str(exc))
            return redirect("menu:pos")

        messages.success(request, f"Pesanan {order.number} tersimpan.")
        return redirect(f"{reverse('menu:order_detail', args=[order.pk])}?baru=1")


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "menu/order_list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_day(self):
        try:
            return date.fromisoformat(self.request.GET.get("tanggal", ""))
        except ValueError:
            return timezone.localdate()

    def get_queryset(self):
        return (
            Order.objects.filter(created_at__date=self.get_day())
            .select_related("cashier")
            .annotate(qty=Sum("items__quantity"))
            .order_by("-created_at")  # Meta.ordering diabaikan Django pada query beragregat
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        day = self.get_day()
        agg = Order.objects.filter(
            created_at__date=day, status=Order.Status.PAID
        ).aggregate(count=Count("id"), revenue=Sum("total"))
        ctx["day"] = day
        ctx["is_today"] = day == timezone.localdate()
        ctx["stats"] = {"count": agg["count"], "revenue": agg["revenue"] or 0}
        ctx["query_string"] = f"tanggal={day.isoformat()}"
        return ctx


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "menu/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.select_related("cashier").prefetch_related("items")


class OrderCancelView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        with transaction.atomic():
            order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
            if order.status != Order.Status.PAID:
                messages.info(request, f"Pesanan {order.number} sudah dibatalkan sebelumnya.")
            else:
                # Kembalikan stok setiap item yang menunya masih ada
                for item in order.items.all():
                    if item.menu_item_id:
                        MenuItem.objects.filter(pk=item.menu_item_id).update(
                            stock=F("stock") + item.quantity
                        )
                order.status = Order.Status.CANCELLED
                order.save(update_fields=["status"])
                messages.success(request, f"Pesanan {order.number} dibatalkan. Stok dikembalikan.")
        return redirect("menu:order_detail", pk=pk)
