from django.contrib import admin

from .models import Category, MenuItem, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_available")
    list_filter = ("category", "is_available")
    search_fields = ("name", "description")
    list_editable = ("is_available",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("menu_item", "name", "price", "quantity")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "created_at", "customer_name", "payment_method", "total", "status", "cashier")
    list_filter = ("status", "payment_method")
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]
