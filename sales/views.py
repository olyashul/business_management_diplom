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
from products.models import Product, StockMovement  # Добавьте StockMovement к существующему импорту

@login_required
def sales_dashboard(request):
    today = timezone.now().date()
    
    # Получаем статистику за сегодня
    today_sales = Sale.objects.filter(
        created_at__date=today,
        is_completed=True,
        is_return=False
    )
    
    today_returns = Sale.objects.filter(
        created_at__date=today,
        is_completed=True,
        is_return=True
    )
    
    total_sales_today = today_sales.count()
    total_revenue_today = today_sales.aggregate(
        total=Sum('final_amount')
    )['total'] or 0
    
    total_returns_today = today_returns.aggregate(
        total=Sum('final_amount')
    )['total'] or 0
    
    net_revenue_today = total_revenue_today - abs(total_returns_today)
    
    average_check_today = 0
    if total_sales_today > 0:
        average_check_today = net_revenue_today / total_sales_today
    
    # Статистика за предыдущий день
    yesterday = today - timedelta(days=1)
    yesterday_sales = Sale.objects.filter(
        created_at__date=yesterday,
        is_completed=True,
        is_return=False
    )
    yesterday_returns = Sale.objects.filter(
        created_at__date=yesterday,
        is_completed=True,
        is_return=True
    )
    
    total_revenue_yesterday = yesterday_sales.aggregate(
        total=Sum('final_amount')
    )['total'] or 0
    total_returns_yesterday = yesterday_returns.aggregate(
        total=Sum('final_amount')
    )['total'] or 0
    
    net_revenue_yesterday = total_revenue_yesterday + total_returns_yesterday
    
    revenue_change = 0
    if net_revenue_yesterday != 0:
        revenue_change = ((net_revenue_today - net_revenue_yesterday) / abs(net_revenue_yesterday)) * 100
    
    recent_operations = Sale.objects.filter(
        is_completed=True
    ).order_by('-created_at')[:2]
    
    popular_items_today = SaleItem.objects.filter(
        sale__created_at__date=today,
        sale__is_return=False,
        quantity__gt=0
    ).values('product__name', 'product__sku').annotate(
        total_quantity=Sum('quantity'),
        total_amount=Sum('total_price')
    ).order_by('-total_quantity')[:2]
    
    quick_form = QuickSaleForm()
    
    context = {
        'today': today,
        'total_sales_today': total_sales_today,
        'total_revenue_today': net_revenue_today,
        'average_check_today': round(average_check_today, 2),
        'revenue_change': round(revenue_change, 1),
        'recent_sales': recent_operations,
        'popular_items_today': popular_items_today,
        'quick_form': quick_form,
    }
    
    return render(request, 'sales/dashboard.html', context)

from django.db import transaction

def quick_add_sale(request):
    """Быстрая продажа (одностраничная форма)"""
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cash')
        discount = request.POST.get('discount', 0)
        notes = request.POST.get('notes', '')
        items_json = request.POST.get('items', '[]')
        
        try:
            items_data = json.loads(items_json)
            
            if not items_data:
                messages.error(request, 'Добавьте хотя бы один товар в продажу')
                return redirect('sales:quick_add_sale')
            
            from decimal import Decimal
            discount = Decimal(str(discount)) if discount else Decimal('0')
            
            with transaction.atomic():
                # Создаем продажу
                sale = Sale.objects.create(
                    created_by=request.user,
                    payment_method=payment_method,
                    discount=discount,
                    notes=notes
                )
                
                # Обрабатываем товары
                for item_data in items_data:
                    product = Product.objects.get(pk=item_data['product_id'])
                    quantity = int(item_data['quantity'])
                    price = Decimal(str(item_data['price']))
                    
                    if product.quantity < quantity:
                        raise ValueError(
                            f"Недостаточно товара '{product.name}' на складе. "
                            f"Доступно: {product.quantity}, требуется: {quantity}"
                        )
                    
                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        selling_price=price
                    )
                
                sale.update_totals()
                sale.refresh_from_db()
                
                messages.success(
                    request,
                    f'Продажа #{sale.sale_number} успешно создана! '
                    f'Сумма: {sale.final_amount} ₽'
                )
                return redirect('sales:sale_detail', pk=sale.pk)
                
        except json.JSONDecodeError as e:
            messages.error(request, f'Ошибка в данных товаров: {str(e)}')
        except Product.DoesNotExist as e:
            messages.error(request, f'Товар не найден: {str(e)}')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка при создании продажи: {str(e)}')
        
        return redirect('sales:quick_add_sale')
    
    # GET запрос - показываем форму
    form = QuickSaleForm()
    return render(request, 'sales/quick_add.html', {
        'form': form,
        'today': timezone.now().date()
    })

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
    
    # Проверка 1: Нельзя вернуть возврат
    if sale.is_return:
        messages.error(request, 'Нельзя оформить возврат на чек возврата!')
        return redirect('sales:sale_detail', pk=sale.pk)
    
    # Проверка 2: Нельзя вернуть чек, по которому уже был возврат
    existing_return = Sale.objects.filter(
        is_return=True,
        notes__icontains=f"Возврат от чека #{sale.sale_number}"
    ).exists()
    
    if existing_return:
        messages.error(request, f'По чеку #{sale.sale_number} уже был оформлен возврат!')
        return redirect('sales:sale_detail', pk=sale.pk)
    
    if request.method == 'POST':
        with transaction.atomic():
            from decimal import Decimal
            
            # Вычисляем коэффициент скидки
            if sale.total_amount > 0:
                discount_ratio = sale.final_amount / sale.total_amount
            else:
                discount_ratio = Decimal('1')
            
            # Генерируем уникальный номер чека возврата
            base_number = f"RET-{sale.sale_number}"
            if len(base_number) > 17:
                base_number = base_number[:17]
            
            return_number = base_number
            counter = 1
            
            while Sale.objects.filter(sale_number=return_number).exists():
                suffix = f"-{counter}"
                if len(base_number) + len(suffix) > 20:
                    base_number = base_number[:20 - len(suffix)]
                return_number = f"{base_number}{suffix}"
                counter += 1
                if counter > 100:
                    return_number = f"RET-{sale.id}-{counter}"
                    break
            
            # Создаем чек возврата
            return_sale = Sale.objects.create(
                sale_number=return_number,
                total_amount=0,
                discount=0,
                final_amount=0,
                payment_method=sale.payment_method,
                is_completed=True,
                is_return=True,
                created_by=request.user,
                notes=f"Возврат от чека #{sale.sale_number}"
            )
            
            # Создаем товары в чеке возврата с учетом скидки
            for item in sale.items.all():
                # Цена с учетом скидки пропорционально
                return_price = item.selling_price * discount_ratio
                return_total = return_price * item.quantity
                SaleItem.objects.create(
                    sale=return_sale,
                    product=item.product,
                    quantity=item.quantity,
                    selling_price=return_price,  # Используем цену с учетом скидки
                    purchase_price=item.purchase_price
                )
            
            # Обновляем суммы чека возврата
            return_sale.update_totals()
            return_sale.final_amount = -return_sale.final_amount
            return_sale.total_amount = -return_sale.total_amount
            return_sale.save()
            
            # Обновляем статистику
            today = timezone.now().date()
            daily_stats, created = DailyStats.objects.get_or_create(date=today)
            daily_stats.total_sales -= 1
            daily_stats.total_amount -= sale.final_amount
            daily_stats.save()
            
            messages.success(request, f'Возврат по чеку #{sale.sale_number} оформлен на сумму {sale.final_amount} ₽')
            
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