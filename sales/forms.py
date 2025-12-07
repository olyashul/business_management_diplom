from django import forms
from .models import Sale, SaleItem
from products.models import Product


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['payment_method', 'discount', 'notes']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-input'}),
            'discount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

class SaleItemForm(forms.ModelForm):
    product_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Поиск товара по названию или артикулу',
            'autocomplete': 'off'
        })
    )
    
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'selling_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-input hidden'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
        }


class QuickSaleForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=Sale.PAYMENT_METHODS,
        initial='cash',
        widget=forms.Select(attrs={'class': 'form-input'})
    )