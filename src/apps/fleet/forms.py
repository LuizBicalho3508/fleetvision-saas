from django import forms
from .models import Vehicle
from .models import DeliveryRoute, Expense, Contract

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['name', 'plate', 'model', 'year', 'fuel_type', 'traccar_device_id']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Caminhão 01'}),
            'plate': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ABC-1234'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'traccar_device_id': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    

class DeliveryRouteForm(forms.ModelForm):
    class Meta:
        model = DeliveryRoute
        fields = ['name', 'vehicle', 'driver', 'date', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['vehicle', 'category', 'description', 'amount', 'due_date', 'is_paid']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['customer_name', 'vehicle', 'value', 'due_day', 'start_date', 'status']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_day': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }