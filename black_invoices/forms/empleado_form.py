from django import forms
from django.contrib.auth.models import User
from ..models import Empleado

class EmpleadoForm(forms.ModelForm):
    username = forms.CharField(label='Nombre de usuario')
    password = forms.CharField(widget=forms.PasswordInput(), required=False, label='Contraseña')
    
    class Meta:
        model = Empleado
        fields = ['nombre', 'apellido', 'nivel_acceso', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'nivel_acceso': forms.Select(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Si es edición, cargar el usuario
            self.initial['username'] = self.instance.user.username