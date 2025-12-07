from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import datetime, date, timedelta
import json
from .models import Sale, SaleItem, DailyStats
from .forms import SaleForm, SaleItemForm, QuickSaleForm
from products.models import Product


@login_required
def sales_dashboard(request):
    today = timezone.now().date()
    
    # Получаем статистику за сегодня
    today_sales = Sale.objects.filter(
        created_at__date=today,
        is_completed=True,
        is_return=False
    )
    
    # Расчет статистики
    total_sales_today = today_sales.count()
    total_revenue_today = today_sales.aggregate(
        total=Sum('final_amount')
    )['total'] or 0
    
    average_check_today = 0
    if total_sales_today > 0:
        average_check_today = total_revenue_today / total_sales_today
    
    # Статистика за предыдущий день для сравнения
    yesterday = today - timedelta(days=1)
    yesterday_sales = Sale.objects.filter(
        created_at__date=yesterday,
        is_completed=True,
        is_return=False
    )
    total_revenue_yesterday = yesterday_sales.aggregate(
        total=Sum('final_amount')
    )['total'] or 0
    
    # Изменение выручки в процентах
    revenue_change = 0
    if total_revenue_yesterday > 0:
        revenue_change = ((total_revenue_today - total_revenue_yesterday) / total_revenue_yesterday) * 100
    
    # Последние продажи (10 последних)
    recent_sales = Sale.objects.filter(
        is_completed=True,
        is_return=False
    ).order_by('-created_at')[:10]
    
    # Популярные товары сегодня
    popular_items_today = SaleItem.objects.filter(
        sale__created_at__date=today,
        sale__is_return=False
    ).values('product__name', 'product__sku').annotate(
        total_quantity=Sum('quantity'),
        total_amount=Sum('total_price')
    ).order_by('-total_quantity')[:5]
    
    # Форма для быстрой продажи
    quick_form = QuickSaleForm()
    
    context = {
        'today': today,
        'total_sales_today': total_sales_today,
        'total_revenue_today': total_revenue_today,
        'average_check_today': round(average_check_today, 2),
        'revenue_change': round(revenue_change, 1),
        'recent_sales': recent_sales,
        'popular_items_today': popular_items_today,
        'quick_form': quick_form,
    }
    
    return render(request, 'sales/dashboard.html', context)

from django.db import transaction

@login_required
def quick_add_sale(request):
    """Быстрая продажа (одностраничная форма)"""
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cash')
        
        try:
            with transaction.atomic():  # Все операции в одной транзакции
                # Создаем продажу
                sale = Sale.objects.create(
                    created_by=request.user,
                    payment_method=payment_method
                )
                
                # Обрабатываем товары
                items_data = json.loads(request.POST.get('items', '[]'))
                
                for item_data in items_data:
                    product = Product.objects.get(pk=item_data['product_id'])
                    
                    # Проверяем наличие товара
                    if product.quantity < item_data['quantity']:
                        raise ValueError(
                            f"Недостаточно товара '{product.name}' на складе. "
                            f"Доступно: {product.quantity}, требуется: {item_data['quantity']}"
                        )
                    
                    # Создаем SaleItem
                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=item_data['quantity'],
                        selling_price=item_data['price']
                    )
                
                # После создания всех товаров обновляем сумму чека
                sale.update_totals()
                
                # Обновляем объект из базы
                sale.refresh_from_db()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'sale_id': sale.id,
                        'sale_number': sale.sale_number,
                        'total_amount': float(sale.total_amount),
                        'final_amount': float(sale.final_amount)
                    })
                
                messages.success(request, f'Продажа #{sale.sale_number} успешно создана! Сумма: {sale.final_amount} ₽')
                return redirect('sales:sale_detail', pk=sale.pk)
            
        except Product.DoesNotExist:
            error_msg = "Товар не найден"
        except ValueError as e:
            error_msg = str(e)
        except Exception as e:
            error_msg = f"Ошибка при создании продажи: {str(e)}"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': error_msg
            })
        
        messages.error(request, error_msg)
        return redirect('sales:quick_add_sale')
    
    # GET запрос
    form = QuickSaleForm()
    return render(request, 'sales/quick_add.html', {'form': form, 'today': timezone.now().date()})


@login_required
def sale_list(request):
    sales = Sale.objects.filter(is_completed=True).order_by('-created_at')
    
    # Фильтрация
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    payment_method = request.GET.get('payment_method', '')
    
    if search_query:
        sales = sales.filter(
            Q(sale_number__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
    
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)
    
    if payment_method:
        sales = sales.filter(payment_method=payment_method)
    
    # Пагинация
    paginator = Paginator(sales, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_sales': sales.count(),
        'total_amount': sales.aggregate(total=Sum('final_amount'))['total'] or 0,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
        'payment_method': payment_method,
        'payment_methods': Sale.PAYMENT_METHODS,
    }
    
    return render(request, 'sales/sale_list.html', context)


@login_required
def sale_detail(request, pk):
    """Детали продажи"""
    sale = get_object_or_404(Sale, pk=pk)
    
    context = {
        'sale': sale,
        'items': sale.items.all(),
    }
    
    return render(request, 'sales/sale_detail.html', context)


@login_required
def sale_return(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    
    if request.method == 'POST':
        return_sale = Sale.objects.create(
            sale_number=f"RETURN-{sale.sale_number}",
            total_amount=sale.total_amount,
            discount=sale.discount,
            final_amount=sale.final_amount,
            payment_method=sale.payment_method,
            is_completed=True,
            is_return=True,
            created_by=request.user,
            notes=f"Возврат от чека #{sale.sale_number}" + (f"\n{request.POST.get('notes', '')}" if request.POST.get('notes') else '')
        )
        for item in sale.items.all():
            sale_item = SaleItem.objects.create(
                sale=return_sale,
                product=item.product,
                quantity=item.quantity,
                selling_price=item.selling_price,
                purchase_price=item.purchase_price
            )
        messages.success(request, f'Возврат по чеку #{sale.sale_number} оформлен. Товары возвращены на склад.')
        return redirect('sales:sale_detail', pk=return_sale.pk)
    
    return render(request, 'sales/sale_return.html', {'sale': sale})


@login_required
def delete_sale(request, pk):
    """Удаление продажи"""
    sale = get_object_or_404(Sale, pk=pk)
    
    if request.method == 'POST':
        sale_number = sale.sale_number
        sale.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Продажа #{sale_number} удалена'
            })
        
        messages.success(request, f'Продажа #{sale_number} удалена')
        return redirect('sales:sale_list')
    
    return render(request, 'sales/delete_sale.html', {'sale': sale})


@login_required
def search_product_api(request):
    """API для поиска товаров"""
    query = request.GET.get('q', '')
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(sku__icontains=query),
            is_active=True,
            quantity__gt=0
        )[:10]
        
        results = []
        for product in products:
            results.append({
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'price': float(product.selling_price),
                'quantity': product.quantity,
                'image': product.images.first().image.url if product.images.first() else ''
            })
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})