import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Product, ProductImage, Category, Supplier

class ProductForm(forms.ModelForm):
    """Форма для создания/редактирования товара"""
    
    class Meta:
        model = Product
        fields = [
            'sku', 'name', 'category', 'supplier',
            'description', 'short_description',
            'purchase_price', 'selling_price',
            'quantity', 'min_quantity', 'is_active'
        ]
        widgets = {
            'sku': forms.TextInput(attrs={
                'class': 'dotted-input w-full',
                'placeholder': 'Артикул товара'
            }),
            'name': forms.TextInput(attrs={
                'class': 'dotted-input w-full',
                'placeholder': 'Название товара'
            }),
            'description': forms.Textarea(attrs={
                'class': 'dotted-input w-full',
                'rows': 4,
                'placeholder': 'Подробное описание товара'
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'dotted-input w-full',
                'rows': 2,
                'placeholder': 'Краткое описание'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'dotted-input w-full',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'dotted-input w-full',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'dotted-input w-full',
                'placeholder': '0'
            }),
            'min_quantity': forms.NumberInput(attrs={
                'class': 'dotted-input w-full',
                'placeholder': '5'
            }),
            'category': forms.Select(attrs={
                'class': 'dotted-input w-full'
            }),
            'supplier': forms.Select(attrs={
                'class': 'dotted-input w-full'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Supplier.objects.all()
        self.fields['category'].queryset = Category.objects.all()
    
    def clean(self):
        cleaned_data = super().clean()
        purchase_price = cleaned_data.get('purchase_price')
        selling_price = cleaned_data.get('selling_price')
        
        if purchase_price and selling_price and selling_price < purchase_price:
            raise ValidationError("Розничная цена не может быть ниже закупочной")
        
        return cleaned_data


class ProductImageForm(forms.ModelForm):
    """Форма для загрузки изображений товара"""
    image = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'dotted-input w-full',
            'accept': 'image/*'
        })
    )
    
    class Meta:
        model = ProductImage
        fields = ['image', 'is_main', 'order']
        widgets = {
            'order': forms.NumberInput(attrs={
                'class': 'dotted-input w-full',
                'placeholder': '0'
            }),
        }


class ProductSearchForm(forms.Form):
    """Форма поиска товаров"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'dotted-input',
            'placeholder': 'Поиск по названию или артикулу',
            'style': 'width: 300px;'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Все категории",
        widget=forms.Select(attrs={'class': 'dotted-input'})
    )
    
    min_quantity = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'dotted-input',
            'placeholder': 'От',
            'style': 'width: 100px;'
        })
    )
    
    max_quantity = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'dotted-input',
            'placeholder': 'До',
            'style': 'width: 100px;'
        })
    )
    
    in_stock_only = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'inn']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'dotted-input w-full',
                'placeholder': 'Название компании'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'dotted-input w-full',
                'placeholder': 'Контактное лицо (необязательно)'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'phone-input',
                'placeholder': '+7(___)___-____',
                'id': 'id_phone'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'dotted-input w-full',
                'placeholder': 'email@example.com (необязательно)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'dotted-input w-full',
                'rows': 3,
                'placeholder': 'Полный адрес (необязательно)'
            }),
            'inn': forms.TextInput(attrs={
                'class': 'dotted-input w-full',
                'placeholder': '10 или 12 цифр (необязательно)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем все поля кроме name необязательными
        self.fields['contact_person'].required = False
        self.fields['email'].required = False
        self.fields['address'].required = False
        self.fields['inn'].required = False
        
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if phone:
            # Очищаем телефон от форматирования
            cleaned_phone = re.sub(r'\D', '', phone)
            
            # Убираем код страны (7 или 8 в начале)
            if cleaned_phone.startswith('8'):
                cleaned_phone = cleaned_phone[1:]  # Убираем первую 8
            elif cleaned_phone.startswith('7'):
                cleaned_phone = cleaned_phone[1:]  # Убираем первую 7
            
            # Проверяем длину (должно быть 10 цифр)
            if len(cleaned_phone) != 10:
                raise ValidationError('Телефон должен содержать 10 цифр после +7')
            
            return '+7' + cleaned_phone
        return phone
    