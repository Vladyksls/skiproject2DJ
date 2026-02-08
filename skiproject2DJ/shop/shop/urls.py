from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("catalog/<str:category>/", views.catalog, name="catalog"),
    path("sales/", views.sales_redirect, name="sales"),
    path("arrivals/", views.arrivals_redirect, name="arrivals"),
    path("product/<int:pid>/", views.product_page, name="product_page"),

    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("remove-from-cart/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/", views.cart, name="cart"),

    path("checkout/", views.checkout, name="checkout"),

    path("login/", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"),
]
