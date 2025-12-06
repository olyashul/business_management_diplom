from django import forms
from .models import Employee, WorkShift
from django.core.exceptions import ValidationError

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'middle_name', 'position',
            'hire_date', 'salary', 'phone', 'email', 'address',
            'passport_data', 'birth_date', 'is_active', 'notes'
        ]
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'passport_data': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class WorkShiftForm(forms.ModelForm):
    class Meta:
        model = WorkShift
        fields = ['date', 'start_time', 'end_time', 'employee', 'manager', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'manager': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Только активные сотрудники
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)
        # Очищаем обязательные поля
        self.fields['employee'].required = False
        self.fields['manager'].required = False

class QuickShiftForm(forms.ModelForm):
    class Meta:
        model = WorkShift
        fields = ['date', 'start_time', 'end_time', 'employee']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'id': 'quick-shift-date'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time', 
                'class': 'form-control',
                'value': '08:00'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time', 
                'class': 'form-control',
                'value': '16:00'
            }),
            'employee': forms.Select(attrs={
                'class': 'form-control',
                'id': 'quick-shift-employee'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)