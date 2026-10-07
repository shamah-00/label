from django.shortcuts import render, get_object_or_404
from .models import Product

def home(request):
    industry_filter = request.GET.get('industry')
    search_query = request.GET.get('q')
    
    products = Product.objects.all()
    
    if industry_filter:
        if hasattr(Product, 'industry'):
            products = products.filter(industry=industry_filter)
            
    if search_query:
        products = products.filter(name__icontains=search_query)
        
    context = {
        'products': products,
        'search_query': search_query,
        'selected_industry': industry_filter,
    }
    return render(request, "products/home.html", context)

def product_list(request):
    return home(request)

def industry_products(request, industry_name):
    request.GET = request.GET.copy()
    request.GET['industry'] = industry_name
    return home(request)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "products/product_detail.html", {'product': product})

def cart(request):
    return render(request, "products/cart.html", {})

def quote_cart(request):
    return render(request, "products/quote_cart.html", {})

def shipping(request):
    return render(request, "products/shipping.html", {})
