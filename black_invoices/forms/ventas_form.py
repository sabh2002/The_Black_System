# forms/venta_forms.py
from django import forms
from django.forms import inlineformset_factory
from ..models import Factura, DetalleFactura, Producto, Cliente, TipoFactura

class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['cliente', 'metodo_pag']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control select2'}),
            'metodo_pag': forms.Select(attrs={'class': 'form-control'})
        }

# Formset para agregar múltiples productos
DetalleFacturaFormSet = inlineformset_factory(
    Factura, DetalleFactura,
    fields=['producto', 'cantidad', 'tipo_factura'],
    extra=1, can_delete=True,
    widgets={
        'producto': forms.Select(attrs={'class': 'form-control select2 producto-select'}),
        'cantidad': forms.NumberInput(attrs={'class': 'form-control cantidad', 'min': '1'}),
        'tipo_factura': forms.Select(attrs={'class': 'form-control'})
    }
)