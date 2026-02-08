from pathlib import Path
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseNotFound
from django.views.decorators.http import require_http_methods

# local data
try:
    from .data import products
except ImportError:
    from data import products

BASE_DIR = Path(__file__).resolve().parent

# -------- Fake DB --------
users = {}
cart_store = {}


class Product:
    def __init__(self, data):
        self.__dict__.update(data)


products_obj = [Product(p) for p in products]

# -------- Helpers --------

def get_cart(request):
    user = request.session.get("user")
    if not user:
        return []
    return cart_store.get(user, [])


def cart_products(cart_ids):
    return [p for p in products if p["id"] in cart_ids]


# -------- Views --------

def home(request):
    featured = [
        p for p in products_obj
        if getattr(p, "is_new", False) or getattr(p, "is_sale", False)
    ][:4]

    if len(featured) < 4:
        featured = products_obj[:4]

    flash = request.session.pop("flash", None)

    return render(request, "shop/index.html", {
        "products": featured,
        "flash": flash,
    })


def catalog(request, category):
    q = request.GET.get("q", "").lower()
    sort = request.GET.get("sort", "default")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    brands = [b.lower() for b in request.GET.getlist("brand")]
    levels = [l.lower() for l in request.GET.getlist("level")]
    styles = [s.lower() for s in request.GET.getlist("style")]

    # category filter
    if category == "sales":
        filtered = [p for p in products_obj if getattr(p, "is_sale", False)]
    elif category == "arrivals":
        filtered = [p for p in products_obj if getattr(p, "is_new", False)]
    else:
        filtered = [p for p in products_obj if p.category == category]

    # search
    if q:
        filtered = [p for p in filtered if q in p.name.lower()]

    # checkbox filters
    if brands:
        filtered = [p for p in filtered if p.brand.lower() in brands]
    if levels:
        filtered = [p for p in filtered if p.level.lower() in levels]
    if styles:
        filtered = [p for p in filtered if p.style.lower() in styles]

    # price filters
    try:
        if min_price:
            filtered = [p for p in filtered if p.price >= float(min_price)]
        if max_price:
            filtered = [p for p in filtered if p.price <= float(max_price)]
    except ValueError:
        pass

    # sorting
    if sort == "price_asc":
        filtered.sort(key=lambda x: x.price)
    elif sort == "price_desc":
        filtered.sort(key=lambda x: -x.price)
    elif sort == "name":
        filtered.sort(key=lambda x: x.name)

    # sidebar filters
    if category == "sales":
        base_products = [p for p in products_obj if p.is_sale]
    elif category == "arrivals":
        base_products = [p for p in products_obj if p.is_new]
    else:
        base_products = [p for p in products_obj if p.category == category]

    return render(request, "shop/catalog.html", {
        "products": filtered,
        "category": category,
        "count": len(filtered),
        "filters": {
            "brands": sorted(set(p.brand for p in base_products)),
            "levels": sorted(set(p.level for p in base_products)),
            "styles": sorted(set(p.style for p in base_products)),
        },
        "selected": {
            "q": q,
            "brand": brands,
            "level": levels,
            "style": styles,
            "sort": sort,
            "min_price": min_price,
            "max_price": max_price,
        }
    })


def sales_redirect(request):
    return redirect("/catalog/sales")


def arrivals_redirect(request):
    return redirect("/catalog/arrivals")


def product_page(request, pid):
    product = next((p for p in products_obj if p.id == pid), None)
    if not product:
        return HttpResponseNotFound("Product not found")

    related = [
        p for p in products_obj
        if p.category == product.category and p.id != pid
    ][:4]

    return render(request, "shop/product.html", {
        "product": product,
        "related": related
    })


# -------- Cart --------

def add_to_cart(request, product_id):
    user = request.session.get("user")
    if not user:
        return redirect("/login")

    cart_store.setdefault(user, []).append(product_id)
    request.session["flash"] = "Товар додано у кошик"

    return redirect(request.META.get("HTTP_REFERER", "/"))


def remove_from_cart(request, product_id):
    user = request.session.get("user")
    if user in cart_store:
        cart_store[user] = [i for i in cart_store[user] if i != product_id]
    return redirect("/cart")


def cart(request):
    cart_ids = get_cart(request)
    items = cart_products(cart_ids)
    total = sum(p["price"] for p in items)

    return render(request, "shop/cart.html", {
        "products": items,
        "total": total
    })


# -------- Checkout --------

@require_http_methods(["GET", "POST"])
def checkout(request):
    if request.method == "POST":
        return redirect("/")
    return render(request, "shop/checkout.html")


# -------- Auth --------

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if users.get(email) == password:
            request.session["user"] = email
            return redirect("/")
        return render(request, "shop/login.html", {"error": "Invalid login"})

    return render(request, "shop/login.html")


@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if email in users:
            return render(request, "shop/register.html", {
                "error": "User already exists"
            })

        users[email] = password
        request.session["user"] = email
        return redirect("/")

    return render(request, "shop/register.html")


def logout_view(request):
    request.session.flush()
    return redirect("/")
