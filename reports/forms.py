from django import forms
from .models import Report
from products.models import Category
from staff.models import Employee

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_type', 'start_date', 'end_date', 'category', 'employee']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'id': 'start-date'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'id': 'end-date'
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'report-type'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'id': 'report-category'
            }),
            'employee': forms.Select(attrs={
                'class': 'form-control',
                'id': 'report-employee'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True).order_by('last_name')
        self.fields['category'].required = False
        self.fields['employee'].required = False
        
        # Устанавливаем значения по умолчанию
        today = forms.DateField().to_python(None)
        if not self.instance.pk:
            self.fields['start_date'].initial = today
            self.fields['end_date'].initial = today