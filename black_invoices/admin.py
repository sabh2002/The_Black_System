from django.contrib import admin

# Register your models here.
# admin.py
from django.contrib import admin
from .models import *

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'nivel_acceso', 'fecha_contratacion', 'activo')
    list_filter = ('nivel_acceso', 'activo')
    search_fields = ('nombre', 'apellido')
    date_hierarchy = 'fecha_contratacion'

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'email', 'telefono')
    search_fields = ('nombre', 'apellido', 'email')
    list_filter = ('nombre', 'apellido')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio', 'stock')

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'empleado', 'fecha_fac', 'total_fac', 'metodo_pag')
    list_filter = ('metodo_pag', 'fecha_fac')
    search_fields = ('cliente__nombre', 'empleado__nombre')
    date_hierarchy = 'fecha_fac'

@admin.register(DetalleFactura)
class DetalleFacturaAdmin(admin.ModelAdmin):
    list_display = ('factura', 'producto', 'cantidad', 'sub_total')
    list_filter = ('factura', 'producto')
    search_fields = ('factura__id', 'producto__nombre')

@admin.register(Ventas)
class VentasAdmin(admin.ModelAdmin):
    list_display = ('id', 'empleado', 'fecha_venta', 'status')
    list_filter = ('status', 'fecha_venta')
    search_fields = ('empleado__nombre',)
    date_hierarchy = 'fecha_venta'

@admin.register(Comision)
class ComisionAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'monto_venta', 'fecha_comision', 'total_comision')
    list_filter = ('fecha_comision',)
    search_fields = ('empleado__nombre',)
    date_hierarchy = 'fecha_comision'

# Registros simples para los modelos más básicos
admin.site.register(NivelAcceso)
admin.site.register(StatusVentas)
admin.site.register(TipoFactura)
admin.site.register(TablaConfig)
admin.site.register(ConsultaComision)