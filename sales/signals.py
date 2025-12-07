from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import StockMovement, SaleItem
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SaleItem

@receiver(post_save, sender=SaleItem)
def update_stock_on_sale_item_save(sender, instance, created, **kwargs):
    if created and instance.product:
        # Создаем движение товара
        StockMovement.objects.create(
            product=instance.product,
            movement_type='outgoing',
            quantity=instance.quantity,
            previous_quantity=instance.product.quantity + instance.quantity,
            new_quantity=instance.product.quantity,
            sale_item=instance,
            comment=f"Продажа #{instance.sale.sale_number}",
            created_by=instance.sale.created_by
        )

def create_stock_movement(product, movement_type, quantity, previous_quantity, 
                         new_quantity, comment, created_by, sale_item=None):
    return StockMovement.objects.create(
        product=product,
        movement_type=movement_type,
        quantity=quantity,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        sale_item=sale_item,
        comment=comment,
        created_by=created_by
    )

@receiver([post_save, post_delete], sender=SaleItem)
def update_sale_totals(sender, instance, **kwargs):
    """Обновить сумму продажи при изменении товаров в чеке"""
    if instance.sale:
        instance.sale.update_totals()