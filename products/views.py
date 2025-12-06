from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from accounts.models import ManagementUser
from .models import Product, Category, ProductImage, Supplier
from .forms import ProductForm, ProductImageForm, ProductSearchForm, SupplierForm
import json

@login_required
def catalog_dashboard(request):
    """Главная страница каталога"""
    # Статистика
    total_products = Product.objects.count()
    
    # Исправляем расчет общей стоимости
    total_value = 0
    products_with_value = Product.objects.all()
    for product in products_with_value:
        total_value += product.quantity * product.purchase_price
    
    low_stock_products = Product.objects.filter(
        quantity__lte=F('min_quantity')  # Теперь F импортирован
    ).count()
    
    # Последние добавленные товары
    recent_products = Product.objects.select_related('category').order_by('-created_at')[:10]
    
    context = {
        'total_products': total_products,
        'total_value': total_value,
        'low_stock_products': low_stock_products,
        'recent_products': recent_products,
    }
    return render(request, 'products/catalog_dashboard.html', context)

@login_required
def product_list(request):
    """Список товаров с фильтрацией"""
    form = ProductSearchForm(request.GET or None)
    products = Product.objects.all().select_related('category', 'supplier')
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        category = form.cleaned_data.get('category')
        min_quantity = form.cleaned_data.get('min_quantity')
        max_quantity = form.cleaned_data.get('max_quantity')
        in_stock_only = form.cleaned_data.get('in_stock_only')
        
        if search:
            products = products.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(description__icontains=search)
            )
        
        if category:
            products = products.filter(category=category)
        
        if min_quantity is not None:
            products = products.filter(quantity__gte=min_quantity)
        
        if max_quantity is not None:
            products = products.filter(quantity__lte=max_quantity)
        
        if in_stock_only:
            products = products.filter(quantity__gt=0)
    
    # Пагинация
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Категории для фильтра
    categories = Category.objects.annotate(product_count=Count('products'))
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'categories': categories,
        'total_products': products.count(),
    }
    return render(request, 'products/product_list.html', context)


@login_required
def product_create(request):
    """Создание нового товара"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            
            # Обработка изображений
            images = request.FILES.getlist('images')
            for i, image in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_main=(i == 0),
                    order=i
                )
            
            messages.success(request, f'Товар "{product.name}" успешно создан!')
            return redirect('products:product_detail', pk=product.pk)
    else:
        form = ProductForm()
    
    return render(request, 'products/product_form.html', {
        'form': form,
        'title': 'Добавить товар',
        'categories': Category.objects.all(),
        'suppliers': Supplier.objects.all()
    })


@login_required
def product_detail(request, pk):
    """Детальная информация о товаре"""
    product = get_object_or_404(
        Product.objects.select_related('category', 'supplier', 'created_by')
        .prefetch_related('images', 'attributes'),
        pk=pk
    )
    
    # Движения товара
    movements = product.movements.order_by('-created_at')[:20]
    
    context = {
        'product': product,
        'movements': movements,
    }
    return render(request, 'products/product_detail.html', context)


@login_required
def product_update(request, pk):
    """Редактирование товара"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Товар "{product.name}" успешно обновлен!')
            return redirect('products:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'title': 'Редактировать товар',
        'categories': Category.objects.all(),
        'suppliers': Supplier.objects.all()
    }
    return render(request, 'products/product_form.html', context)


@login_required
def product_delete(request, pk):
    """Удаление товара"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Товар "{product_name}" успешно удален!')
        return redirect('products:product_list')
    
    return render(request, 'products/product_confirm_delete.html', {'product': product})


@login_required
def update_stock(request, pk):
    """Обновление остатков товара"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_quantity = int(data.get('quantity', 0))
            comment = data.get('comment', '')
            
            if new_quantity < 0:
                return JsonResponse({'error': 'Количество не может быть отрицательным'}, status=400)
            
            old_quantity = product.quantity
            movement_type = 'incoming' if new_quantity > old_quantity else 'outgoing'
            
            # Создаем запись в истории
            StockMovement.objects.create(
                product=product,
                movement_type=movement_type,
                quantity=abs(new_quantity - old_quantity),
                previous_quantity=old_quantity,
                new_quantity=new_quantity,
                comment=comment,
                created_by=request.user
            )
            
            # Обновляем остаток
            product.quantity = new_quantity
            product.save()
            
            return JsonResponse({
                'success': True,
                'new_quantity': product.quantity,
                'total_value': float(product.total_value),
                'is_low_stock': product.is_low_stock
            })
            
        except (ValueError, json.JSONDecodeError) as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Метод не разрешен'}, status=405)


@login_required
def category_list(request):
    """Список категорий"""
    categories = Category.objects.annotate(
        product_count=Count('products')
    ).order_by('name')
    
    return render(request, 'products/category_list.html', {
        'categories': categories
    })

# products/views.py - добавляем в конец файла

from .forms import SupplierForm

@login_required
def supplier_create(request):
    """Создание нового поставщика"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Поставщик "{supplier.name}" успешно добавлен!')
            return redirect('products:catalog_dashboard')
    else:
        form = SupplierForm()
    
    return render(request, 'products/supplier_form.html', {
        'form': form,
        'title': 'Добавить поставщика'
    })
