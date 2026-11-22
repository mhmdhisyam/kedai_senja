from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

app_name = "menu"

urlpatterns = [
    # Autentikasi
    path(
        "masuk/",
        auth_views.LoginView.as_view(
            template_name="menu/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("keluar/", auth_views.LogoutView.as_view(), name="logout"),  # POST saja (Django 5)
    # Kasir & pesanan
    path("kasir/", views.PosView.as_view(), name="pos"),
    path("pesanan/", views.OrderListView.as_view(), name="order_list"),
    path("pesanan/<int:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("pesanan/<int:pk>/batal/", views.OrderCancelView.as_view(), name="order_cancel"),
    # Menu
    path("", views.MenuListView.as_view(), name="menu_list"),
    path("menu/tambah/", views.MenuCreateView.as_view(), name="menu_create"),
    path("menu/<int:pk>/ubah/", views.MenuUpdateView.as_view(), name="menu_update"),
    path("menu/<int:pk>/hapus/", views.MenuDeleteView.as_view(), name="menu_delete"),
    path("menu/<int:pk>/toggle/", views.toggle_availability, name="menu_toggle"),
    # Kategori
    path("kategori/", views.CategoryListView.as_view(), name="category_list"),
    path("kategori/tambah/", views.CategoryCreateView.as_view(), name="category_create"),
    path("kategori/<int:pk>/ubah/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("kategori/<int:pk>/hapus/", views.CategoryDeleteView.as_view(), name="category_delete"),
]
