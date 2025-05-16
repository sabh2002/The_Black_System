from datetime import datetime
from decimal import Decimal
import json
import math as m
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin

from black_invoices.forms.user_profile_form import UserProfileForm
from .models import *
from .forms.producto_forms import ProductoForm
from .forms.cliente_forms import ClienteForm
from .forms.empleado_form import EmpleadoForm
from .forms.ventas_form import FacturaForm, DetalleFacturaFormSet
from django.core.serializers.json import DjangoJSONEncoder
from django.core import serializers
from django.db.models import Sum, Count, F, Max, Avg
from django.db.models.functions import TruncMonth, TruncDay
from datetime import datetime, timedelta
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import io
from .mixins import EmpleadoRolMixin
import os
from django.conf import settings


###################     Dashboard       #################
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'black_invoices/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Dashboard'
        
        # Fechas para filtros
        hoy = datetime.now().date()
        inicio_mes = hoy.replace(day=1)
        inicio_anio = hoy.replace(month=1, day=1)
        
        # Estadísticas generales
        context['total_ventas_hoy'] = Factura.objects.filter(
            fecha_fac__date=hoy
        ).aggregate(total=Sum('total_fac'))['total'] or 0
        
        context['total_ventas_mes'] = Factura.objects.filter(
            fecha_fac__gte=inicio_mes
        ).aggregate(total=Sum('total_fac'))['total'] or 0
        
        context['total_ventas_anio'] = Factura.objects.filter(
            fecha_fac__gte=inicio_anio
        ).aggregate(total=Sum('total_fac'))['total'] or 0
        
        # Productos más vendidos
        context['productos_top'] = DetalleFactura.objects.values(
            'producto__nombre'
        ).annotate(
            total=Sum('cantidad')
        ).order_by('-total')[:5]
        
        # Ventas por empleado este mes
        context['ventas_empleados'] = Factura.objects.filter(
            fecha_fac__gte=inicio_mes
        ).values(
            'empleado__nombre', 'empleado__apellido'
        ).annotate(
            total=Sum('total_fac'),
            cantidad=Count('id')
        ).order_by('-total')
        
        # Datos para gráfico de ventas por día (últimos 15 días)
        quince_dias_atras = hoy - timedelta(days=14)
        ventas_por_dia = Factura.objects.filter(
            fecha_fac__date__gte=quince_dias_atras
        ).annotate(
            dia=TruncDay('fecha_fac')
        ).values('dia').annotate(
            total=Sum('total_fac')
        ).order_by('dia')
        
        # Formatear para Chart.js
        labels = []
        datos = []
        
        for venta in ventas_por_dia:
            labels.append(venta['dia'].strftime('%d/%m'))
            datos.append(float(venta['total']))
        
        context['chart_labels'] = labels
        context['chart_data'] = datos
        
        # Alertas de stock bajo
        context['productos_stock_bajo'] = Producto.objects.filter(
            stock__lte=5,  # Umbral configurable
            activo=True
        ).order_by('stock')
        
        return context
class BaseListView(LoginRequiredMixin, ListView):
    template_name = 'lista_generica.html'
    context_object_name = 'objetos'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = self.titulo
        return context


######################      CLIENTES        #####################3
class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'black_invoices/clientes/clientes_list.html'
    context_object_name = 'clientes'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Lista de Clientes'
        context['create_url'] = reverse_lazy('black_invoices:cliente_create')
        return context

class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'black_invoices/clientes/clientes_form.html'
    success_url = reverse_lazy('black_invoices:cliente_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registrar Cliente'
        context['action'] = 'Registrar'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Cliente registrado exitosamente.')
        return super().form_valid(form)
class ClienteDetailView(LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = 'black_invoices/clientes/cliente_detail.html'
    context_object_name = 'cliente'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = self.get_object()
        # Obtener historial de ventas/facturas del cliente
        context['facturas'] = Factura.objects.filter(cliente=cliente).order_by('-fecha_fac')
        return context
class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    template_name = 'black_invoices/clientes/cliente_form.html'
    fields = ['nombre', 'apellido', 'email', 'telefono', 'direccion']
    
    def get_success_url(self):
        return reverse_lazy('black_invoices:cliente_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado exitosamente')
        return super().form_valid(form)
    
######################      PRODUCTOS       ###############
class ProductoListView(LoginRequiredMixin, ListView):
    model = Producto
    template_name = 'black_invoices/productos/productos_list.html'
    context_object_name = 'productos'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Lista de Productos'
        context['create_url'] = reverse_lazy('black_invoices:producto_create')
        return context

class ProductoCreateView(LoginRequiredMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'black_invoices/productos/producto_form.html'
    success_url = reverse_lazy('black_invoices:producto_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Producto'
        context['action'] = 'Crear'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Producto creado exitosamente.')
        return super().form_valid(form)

class ProductoStockUpdateView(LoginRequiredMixin, UpdateView):
    model = Producto
    template_name = 'black_invoices/productos/producto_stock.html'
    fields = ['stock']
    success_url = reverse_lazy('black_invoices:producto_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Actualizar Stock: {self.object.nombre}'
        return context
    
    def form_valid(self, form):
        # Guardar stock anterior para mensaje
        stock_anterior = self.object.stock
        
        # Guardar formulario
        response = super().form_valid(form)
        
        # Mostrar mensaje con el cambio
        messages.success(
            self.request, 
            f'Stock de {self.object.nombre} actualizado de {stock_anterior} a {self.object.stock}'
        )
        
        return response
    
# En views.py, añade estas clases

class ProductoDetailView(LoginRequiredMixin, DetailView):
    model = Producto
    template_name = 'black_invoices/productos/producto_detail.html'
    context_object_name = 'producto'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Detalles del Producto: {self.object.nombre}'
        
        # Obtener historial de ventas de este producto (opcional)
        context['detalles_ventas'] = DetalleFactura.objects.filter(
            producto=self.object
        ).order_by('-factura__fecha_fac')[:10]  # Últimas 10 ventas
        
        return context

class ProductoUpdateView(LoginRequiredMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'black_invoices/productos/producto_form.html'
    
    def get_success_url(self):
        return reverse_lazy('black_invoices:producto_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Producto: {self.object.nombre}'
        context['action'] = 'Actualizar'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Producto {self.object.nombre} actualizado exitosamente.')
        return super().form_valid(form)

########################        EMPLEADOS       #############
class EmpleadoListView(EmpleadoRolMixin, ListView):
    model = Empleado
    template_name = 'black_invoices/empleados/empleados_list.html'
    context_object_name = 'empleados'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Lista de Empleados'
        return context
    
class EmpleadoCreateView(EmpleadoRolMixin, CreateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'black_invoices/empleados/empleado_form.html'
    success_url = reverse_lazy('black_invoices:empleado_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nuevo Empleado'
        context['accion'] = 'Crear'
        return context
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Crear usuario
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password'] or '12345678',  # Contraseña temporal si no se proporciona
                    first_name=form.cleaned_data['nombre'],
                    last_name=form.cleaned_data['apellido']
                )
                
                # Crear empleado
                empleado = form.save(commit=False)
                empleado.user = user
                empleado.save()
                
                messages.success(self.request, f'Empleado {empleado.nombre} creado exitosamente')
                return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f'Error al crear empleado: {str(e)}')
            return self.form_invalid(form)

class EmpleadoUpdateView(EmpleadoRolMixin, UpdateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'black_invoices/empleados/empleado_form.html'
    success_url = reverse_lazy('black_invoices:empleado_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Empleado: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        return context
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Actualizar usuario
                user = self.object.user
                user.username = form.cleaned_data['username']
                user.first_name = form.cleaned_data['nombre']
                user.last_name = form.cleaned_data['apellido']
                
                # Actualizar contraseña si se proporcionó
                if form.cleaned_data['password']:
                    user.set_password(form.cleaned_data['password'])
                    
                user.save()
                
                # Guardar cambios en empleado
                empleado = form.save()
                
                messages.success(self.request, f'Empleado {empleado.nombre} actualizado exitosamente')
                return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f'Error al actualizar empleado: {str(e)}')
            return self.form_invalid(form)
    
#######################     FACTURAS        ######################
class FacturaListView(LoginRequiredMixin, ListView):
    model = Factura
    template_name = 'black_invoices/facturas/facturas_list.html'
    context_object_name = 'facturas'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Lista de Recibos'
        return context

class FacturaDetailView(LoginRequiredMixin, DetailView):
    model = Factura
    template_name = 'black_invoices/facturas/factura_detail.html'
    context_object_name = 'factura'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        factura = self.get_object()
        # El modelo Factura tiene un método get_detalles()
        # que retorna DetalleFactura.objects.filter(factura=self)
        # Lo usamos para cargar los detalles.
        context['detalles'] = factura.get_detalles().order_by('id') 
        context['titulo'] = f'Detalle de Factura N° {factura.id}' # Título para la página
        return context

def ingresar(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('black_invoices:inicio')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'black_invoices/usuarios/login.html')



#####################       VENTAS      #######################       
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.urls import reverse_lazy
from django.contrib import messages

""" class VentaCreateView(LoginRequiredMixin, CreateView):
    model = Factura
    form_class = FacturaForm
    template_name = 'black_invoices/ventas/venta_form.html'
    success_url = reverse_lazy('black_invoices:venta_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Venta'
        
        if self.request.POST:
            context['detalles_formset'] = DetalleFacturaFormSet(self.request.POST)
        else:
            context['detalles_formset'] = DetalleFacturaFormSet()
        context['clientes'] = Cliente.objects.all() #.objects.filter(activo=True)
        context['productos'] = Producto.objects.all() #.objects.filter(activo=True)
        
        # Añadir opciones de crédito
        context['opciones_venta'] = [
            {'id': 'contado', 'nombre': 'Contado'},
            {'id': 'credito', 'nombre': 'Crédito'}
        ]
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['detalles_formset']
        
        try:
            with transaction.atomic():
                # Verificar que el usuario tenga un empleado asociado
                if not hasattr(self.request.user, 'empleado'):
                    messages.error(self.request, 'No tienes un perfil de empleado asociado.')
                    return self.form_invalid(form)
                
                # Crear la factura pero no guardarla aún
                factura = form.save(commit=False)
                factura.empleado = self.request.user.empleado
                factura.save()
                
                # Validar el formset directamente
                if formset.is_valid():
                    detalles = formset.save(commit=False)
                    
                    if not detalles:
                        # Si no hay detalles, intentar procesarlos manualmente
                        total_forms = int(self.request.POST.get('form-TOTAL_FORMS', 0))
                        
                        # Información de diagnóstico
                        print(f"Total de formularios: {total_forms}")
                        print(f"Datos POST: {self.request.POST}")
                        
                        # Crear manualmente los detalles
                        for i in range(total_forms):
                            producto_id = self.request.POST.get(f'form-{i}-producto')
                            cantidad_str = self.request.POST.get(f'form-{i}-cantidad')
                            
                            if producto_id and cantidad_str:
                                # Determinar tipo de factura basado en tipo_venta
                                es_credito = self.request.POST.get('tipo_venta') == 'credito'
                                tipo_factura = TipoFactura.objects.get(pk=2 if es_credito else 1)
                                
                                producto = Producto.objects.get(pk=producto_id)
                                cantidad = int(cantidad_str)
                                
                                # Verificar stock
                                if cantidad > producto.stock:
                                    raise ValueError(f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}")
                                
                                # Crear detalle
                                subtotal = producto.precio * cantidad
                                detalle = DetalleFactura(
                                    factura=factura,
                                    producto=producto,
                                    cantidad=cantidad,
                                    tipo_factura=tipo_factura,
                                    sub_total=subtotal
                                )
                                detalle.save()
                                
                                # Reducir stock
                                producto.stock -= cantidad
                                producto.save(update_fields=['stock'])
                                
                                # Agregar al array de detalles
                                detalles.append(detalle)
                        
                        if not detalles:
                            raise ValueError("Debe agregar al menos un producto a la venta. Verifique que seleccionó un producto y una cantidad.")
                    else:
                        # Procesar los detalles del formset
                        total_factura = 0
                        
                        for detalle in detalles:
                            detalle.factura = factura
                            
                            # Verificar stock
                            if detalle.cantidad > detalle.producto.stock:
                                raise ValueError(f"Stock insuficiente para {detalle.producto.nombre}. Disponible: {detalle.producto.stock}")
                            
                            # Calcular subtotal
                            subtotal = detalle.cantidad * detalle.producto.precio
                            detalle.sub_total = subtotal
                            detalle.save()
                            
                            # Reducir stock
                            detalle.producto.stock -= detalle.cantidad
                            detalle.producto.save(update_fields=['stock'])
                            
                            total_factura += subtotal
                    
                    # Calcular el total en cualquier caso
                    total_factura = sum(detalle.sub_total for detalle in detalles)
                    
                    # Actualizar total de factura
                    factura.total_fac = total_factura
                    factura.total_venta = total_factura
                    factura.save()
                    
                    # Crear venta
                    es_credito = self.request.POST.get('tipo_venta') == 'credito'
                    
                    if es_credito:
                        estado = StatusVentas.objects.get(nombre="Pendiente")
                    else:
                        estado = StatusVentas.objects.get(nombre="Completada")
                    
                    venta = Ventas.objects.create(
                        empleado=factura.empleado,
                        factura=factura,
                        status=estado,
                        credito=es_credito,
                        monto_pagado=0 if es_credito else factura.total_fac
                    )
                    
                    if es_credito:
                        messages.success(self.request, f'Venta a crédito #{venta.id} creada exitosamente.')
                    else:
                        messages.success(self.request, f'Venta #{venta.id} creada exitosamente.')
                    
                    # Necesario para que la vista funcione correctamente
                    self.object = factura
                    
                    return redirect('black_invoices:venta_detail', pk=venta.id)
                else:
                    # Mostrar errores específicos del formset
                    print(f"Formset inválido. Errores: {formset.errors}")
                    for i, form_errors in enumerate(formset.errors):
                        if form_errors:
                            messages.error(self.request, f"Error en producto {i+1}: {form_errors}")
                    return self.form_invalid(form)
                    
        except Exception as e:
                messages.error(self.request, f"Error: {str(e)}")
                print(f"Excepción: {type(e).__name__}: {str(e)}")
                return self.form_invalid(form) """
class VentaCreateView(LoginRequiredMixin, View):
    template_name = 'black_invoices/ventas/venta_form.html'
    
    def get(self, request):
        context = {
            'titulo': 'Crear Venta',
            'clientes': Cliente.objects.all(),
            'productos': Producto.objects.all(),
            'opciones_venta': [
                {'id': 'contado', 'nombre': 'Contado'},
                {'id': 'credito', 'nombre': 'Crédito'}
            ]
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        try:
            with transaction.atomic():
                # 1. Verificar que el usuario tenga empleado asociado
                if not hasattr(request.user, 'empleado'):
                    messages.error(request, 'No tienes un perfil de empleado asociado.')
                    return redirect('black_invoices:venta_create')
                
                # 2. Obtener cliente y método de pago
                cliente_id = request.POST.get('cliente')
                metodo_pago = request.POST.get('metodo_pag')
                
                if not cliente_id:
                    messages.error(request, 'Debe seleccionar un cliente.')
                    return redirect('black_invoices:venta_create')
                
                # 3. Recopilar detalles de productos
                productos = []
                total_forms = int(request.POST.get('form-TOTAL_FORMS', 0))
                
                for i in range(total_forms):
                    producto_id = request.POST.get(f'form-{i}-producto')
                    cantidad_str = request.POST.get(f'form-{i}-cantidad')
                    
                    if producto_id and cantidad_str and cantidad_str.isdigit():
                        productos.append({
                            'id': producto_id,
                            'cantidad': int(cantidad_str)
                        })
                
                if not productos:
                    messages.error(request, 'Debe agregar al menos un producto a la venta.')
                    return redirect('black_invoices:venta_create')
                
                # 4. Crear la factura
                cliente = Cliente.objects.get(pk=cliente_id)
                factura = Factura(
                    cliente=cliente,
                    empleado=request.user.empleado,
                    metodo_pag=metodo_pago
                )
                factura.save()
                
                # 5. Procesar los productos
                total_factura = 0
                es_credito = request.POST.get('tipo_venta') == 'credito'
                tipo_factura = TipoFactura.objects.get(credito_fac=es_credito)
                
                for prod in productos:
                    try:
                        producto = Producto.objects.get(pk=prod['id'])
                        cantidad = prod['cantidad']
                        
                        # Verificar stock
                        if cantidad > producto.stock:
                            raise ValueError(f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}")
                        
                        # Calcular subtotal
                        subtotal = producto.precio * cantidad
                        total_factura += subtotal
                        
                        # Crear detalle
                        detalle = DetalleFactura(
                            factura=factura,
                            producto=producto,
                            cantidad=cantidad,
                            tipo_factura=tipo_factura,
                            sub_total=subtotal
                        )
                        detalle.save()
                        
                        # Reducir stock
                        producto.stock -= cantidad
                        producto.save(update_fields=['stock'])
                        
                    except Producto.DoesNotExist:
                        raise ValueError(f"El producto con ID {prod['id']} no existe.")
                
                # 6. Actualizar el total de la factura
                factura.total_fac = total_factura
                factura.total_venta = total_factura
                factura.save()
                
                # 7. Crear la venta
                if es_credito:
                    estado = StatusVentas.objects.get(nombre="Pendiente")
                else:
                    estado = StatusVentas.objects.get(nombre="Completada")
                
                venta = Ventas.objects.create(
                    empleado=factura.empleado,
                    factura=factura,
                    status=estado,
                    credito=es_credito,
                    monto_pagado=0 if es_credito else factura.total_fac
                )
                
                messages.success(request, f'Venta {"a crédito " if es_credito else ""}#{venta.id} creada exitosamente.')
                return redirect('black_invoices:venta_detail', pk=venta.id)
                
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('black_invoices:venta_create')
class VentaListView(LoginRequiredMixin, ListView):
    model = Ventas
    template_name = 'black_invoices/ventas/ventas_list.html'
    context_object_name = 'ventas'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Lista de Ventas'
        context['create_url'] = reverse_lazy('black_invoices:venta_create')
        return context

class VentasPendientesView(EmpleadoRolMixin, ListView):
    model = Ventas
    template_name = 'black_invoices/ventas/ventas_pendientes.html'
    context_object_name = 'ventas'
    roles_permitidos = ['Administrador', 'Supervisor', 'Vendedor']
    
    def get_queryset(self):
        return Ventas.objects.filter(
            credito=True, 
            status__vent_cancelada=False
        ).exclude(
            monto_pagado__gte=F('factura__total_fac')
        ).order_by('-id')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Abonos (Crédito)'
        return context
    
class RegistrarPagoView(EmpleadoRolMixin, UpdateView):
    model = Ventas
    template_name = 'black_invoices/ventas/registrar_pago.html'
    fields = []  # No usamos campos del modelo directamente
    roles_permitidos = ['Administrador', 'Supervisor', 'Vendedor']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Registrar Pago - Venta #{self.object.id}'
        context['venta'] = self.object
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        try:
            monto = float(request.POST.get('monto', 0))
            
            if monto <= 0:
                messages.error(request, 'El monto debe ser mayor a cero.')
                return self.get(request, *args, **kwargs)
            
            if monto > (self.object.saldo_pendiente + Decimal(0.01)):
                messages.error(request, f'El monto excede el saldo pendiente (${self.object.saldo_pendiente}).')
                return self.get(request, *args, **kwargs)
            
            # Registrar pago
            self.object.registrar_pago(monto)
            
            if self.object.completada:
                messages.success(request, f'Pago de ${monto} registrado. La venta ha sido completada.')
            else:
                messages.success(request, f'Pago de ${monto} registrado. Saldo pendiente: ${self.object.saldo_pendiente}')
            
            return redirect('black_invoices:ventas_pendientes')
            
        except ValueError:
            messages.error(request, 'Por favor ingrese un monto válido.')
            return self.get(request, *args, **kwargs)
class VentaDetailView(LoginRequiredMixin, DetailView):
    model = Ventas
    template_name = 'black_invoices/ventas/venta_detail.html'
    context_object_name = 'venta'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Detalle de venta #{self.object.id}'

        context['detalles'] = self.object.factura.detallefactura_set.all()

        try:
            context['comision'] = self.object.comision
        except:
            context['comision'] = None
        
        return context

@login_required
def cancelar_venta(request, pk):
    try:
        venta = Ventas.objects.get(pk=pk)
        
        # Comprobar que la venta no esté ya cancelada
        if venta.status.vent_cancelada:
            messages.warning(request, 'La venta ya está cancelada.')
        else:
            venta.cancelar_venta()
            messages.success(request, f'Venta #{venta.id} cancelada exitosamente. Stock restaurado.')
    
    except Ventas.DoesNotExist:
        messages.error(request, 'Venta no encontrada.')
    
    return redirect('black_invoices:venta_list')


######################      COMISIONES      ###############
from django.db.models import Q

class RangosComisionesListView(LoginRequiredMixin, ListView):
    model = ConsultaComision
    template_name = 'black_invoices/comisiones/rangos_list.html'
    context_object_name = 'rangos'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Rangos de Comisiones'
        return context

class RangosComisionesCreateView(LoginRequiredMixin, CreateView):
    model = ConsultaComision
    template_name = 'black_invoices/comisiones/rangos_form.html'
    fields = ['rango_inferior', 'rango_superior', 'porcentaje']
    success_url = reverse_lazy('black_invoices:rangos_comisiones_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Añadir Rango de Comisión'
        context['boton'] = 'Guardar'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Rango de comisión creado exitosamente')
        return super().form_valid(form)

class RangosComisionesUpdateView(LoginRequiredMixin, UpdateView):
    model = ConsultaComision
    template_name = 'black_invoices/comisiones/rangos_form.html'
    fields = ['rango_inferior', 'rango_superior', 'porcentaje']
    success_url = reverse_lazy('black_invoices:rangos_comisiones_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Rango de Comisión'
        context['boton'] = 'Actualizar'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Rango de comisión actualizado exitosamente')
        return super().form_valid(form)

class RangosComisionesDeleteView(LoginRequiredMixin, DeleteView):
    model = ConsultaComision
    template_name = 'black_invoices/comisiones/rangos_confirm_delete.html'
    success_url = reverse_lazy('black_invoices:rangos_comisiones_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Eliminar Rango de Comisión'
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Rango de comisión eliminado exitosamente')
        return super().delete(request, *args, **kwargs)
class ComisionListView(LoginRequiredMixin, ListView):
    model = Empleado
    template_name = 'black_invoices/comisiones/comision_list.html'
    context_object_name = 'empleados'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Comisiones'
        
        if hasattr(self.request.user, 'empleado'):
            empleado = self.request.user.empleado
            mes_actual = datetime.now().month
            anio_actual = datetime.now().year
            
            # Filtrar empleados según el nivel de acceso
            es_admin = empleado.nivel_acceso.nombre == 'Administrador'
            context['es_administrador'] = es_admin
            
            if es_admin:
                empleados = Empleado.objects.filter(activo=True)
            else:
                empleados = Empleado.objects.filter(id=empleado.id)
            
            # Calcular comisiones para cada empleado
            comisiones = []
            for emp in empleados:
                # Obtener ventas completadas
                ventas_completadas = Ventas.objects.filter(
                    empleado=emp,
                    factura__fecha_fac__month=mes_actual,
                    factura__fecha_fac__year=anio_actual
                ).exclude(status__vent_cancelada=True).filter(
                    # Solo ventas completadas (contado o crédito pagado)
                    Q(credito=False) | Q(credito=True, monto_pagado__gte=F('factura__total_fac'))
                )
                
                # Calcular comisión
                total_comision = emp.get_comisiones_mes(mes_actual, anio_actual)
                
                comisiones.append({
                    'empleado': emp,
                    'ventas': ventas_completadas.count(),
                    'comision': total_comision
                })
            
            context['comisiones'] = comisiones
            
            # Cálculo para el empleado actual (para el widget)
            context['total_mes'] = empleado.get_comisiones_mes(mes_actual, anio_actual)
            context['total_anio'] = sum(
                empleado.get_comisiones_mes(m, anio_actual) 
                for m in range(1, mes_actual + 1)
            )
        
        return context
    
class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Empleado
    form_class = UserProfileForm 
    template_name = 'black_invoices/usuarios/perfil_form.html' # Nueva plantilla
    success_url = reverse_lazy('black_invoices:perfil_usuario_editar') # Redirige a la misma página

    def get_object(self, queryset=None):
        # Devuelve la instancia de Empleado asociada al usuario logueado.
        # get_object_or_404 es más seguro aquí.
        return get_object_or_404(Empleado, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Configurar Mi Perfil'
        context['action_text'] = 'Guardar Cambios'
        return context

    def form_valid(self, form):
        # El método save del UserProfileForm ya maneja la actualización de User y Empleado.
        form.save() 
        messages.success(self.request, 'Tu perfil ha sido actualizado exitosamente.')
        return super().form_valid(form) # Esto redirigirá a success_url

    def form_invalid(self, form):
        # Construir un mensaje de error más detallado para mostrar todos los errores
        error_list_html = "<ul>"
        for field, errors in form.errors.items():
            field_label = form.fields[field].label if field != '__all__' and field in form.fields else "Error general"
            for error in errors:
                error_list_html += f"<li><strong>{field_label}:</strong> {error}</li>"
        if form.non_field_errors():
             for error in form.non_field_errors():
                error_list_html += f"<li><strong>Error general:</strong> {error}</li>"
        error_list_html += "</ul>"
        
        messages.error(self.request, f"Error al actualizar el perfil. Por favor, corrija los problemas indicados:{error_list_html}", extra_tags='safe')
        return super().form_invalid(form)
    
def logout_view(request):
    logout(request)
    return redirect('black_invoices:login')


def ingresar(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('black_invoices:inicio')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'black_invoices/usuarios/login.html')

#################    PDF    ######################
class FacturaPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            factura = Factura.objects.get(pk=pk)
        except Factura.DoesNotExist:
            return HttpResponse("Factura no encontrada", status=404)

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # --- Membrete y Logo ---
        logo_path = os.path.join(settings.BASE_DIR, 'black_invoices/static/img/the_black.jpeg')
        if os.path.exists(logo_path):
            p.drawImage(logo_path, 40, height - 110, width=120, height=60, preserveAspectRatio=True, mask='auto')
        
        # Nombre de la empresa (ajustado a la izquierda)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(180, height - 50, "INDUSTRIA & HERRAMIENTA EL NEGRITO, C.A.")
        
        # RIF (ajustado para no sobreponerse)
        p.setFont("Helvetica-Bold", 11)
        p.drawString(180, height - 65, "RIF: J-406050717")
        
        # Dirección y teléfonos
        p.setFont("Helvetica", 10)
        p.drawString(180, height - 80, "CR 10 ENTRE CALLES 4 Y 5 EDIF DOÑA EDITH PISO 1 OF 2")
        p.drawString(180, height - 95, "BARRIO MATURIN GUANARE PORTUGUESA")
        p.drawString(180, height - 110, "Teléfonos: 0257-5143082 / 0257-5143082")

        # --- Datos generales ---
        p.setFont("Helvetica-Bold", 13)
        p.drawString(50, height - 130, "NOTA DE ENTREGA")
        p.setFont("Helvetica", 10)
        fecha_impresion = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        p.drawString(400, height - 130, f"Fecha impresión: {fecha_impresion}")
        p.drawString(400, height - 145, f"Nº Control: {factura.id:06d}")
        p.drawString(400, height - 160, f"Fecha: {factura.fecha_fac.strftime('%d-%m-%Y %H:%M')}")
        p.setFont("Helvetica-Bold", 10)
        p.drawString(400, height - 175, f"VENDEDOR: {factura.empleado.nombre} {factura.empleado.apellido}")
        p.setFont("Helvetica", 10)
        p.drawString(400, height - 190, f"CONDICIÓN: {factura.get_metodo_pag_display()}")

        # --- Datos del cliente ---
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, height - 160, f"CLIENTE:")
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 175, f"TLF: {factura.cliente.telefono}")
        p.drawString(50, height - 190, f"NOMBRE: {factura.cliente.nombre} {factura.cliente.apellido}")
        p.drawString(50, height - 205, f"DIRECCIÓN FISCAL: {factura.cliente.direccion}")

        # --- Tabla de productos ---
        detalles = factura.detallefactura_set.all()
        data = [["#", "Código", "Producto", "Cant.", "Garantía", "Precio", "Desc.", "Total"]]
        
        for idx, detalle in enumerate(detalles, 1):
            codigo = str(detalle.producto.id)  # Mostrar el id del producto
            data.append([
                str(idx),
                codigo,
                detalle.producto.nombre,
                str(detalle.cantidad),
                "Sí",  # Presentación (añadido según imagen)
                f"{detalle.producto.precio:,.2f}",
                "0,00",  # Descuento
                f"{detalle.sub_total:,.2f}"
            ])
        
        # Añadir solo una fila vacía para mantener el espacio
        if len(data) < 3:  # Si solo tenemos el encabezado y un producto
            data.append(["", "", "", "", "", "", "", ""])  # Solo una fila vacía
        
        # Añadir fila de totales
        data.append(["", "", "", "", "", "", "TOTAL", f"{factura.total_fac:,.2f}"])
        
        # Crear tabla con 8 columnas (añadimos Presen.)
        table = Table(data, colWidths=[25, 60, 160, 40, 50, 60, 50, 60])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.black),  # Grid para todas las filas excepto la última
            ('LINEABOVE', (6, -1), (7, -1), 0.5, colors.black),  # Línea solo arriba de "TOTAL" y su valor
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (3, 1), (7, -1), 'RIGHT'),  # Alinear a la derecha desde Cant. hasta Total
            ('FONTNAME', (6, -1), (7, -1), 'Helvetica-Bold'),  # Negrita para "TOTAL" y su valor
        ]))
        
        table.wrapOn(p, width, height)
        table.drawOn(p, 40, height - 320 - 20 * min(len(data), 6))  # Ajustar altura según número de filas

        # --- Sección de descuentos (como en la imagen 2) ---
        p.setFont("Helvetica", 8)
        p.drawString(430, 130, "DESC. POR PRODUCTOS")
        p.drawString(550, 130, "0,00 BS")
        p.drawString(430, 120, "DESC. (30.00)")
        p.drawString(550, 120, "0,00 BS")
        
        # Línea horizontal debajo de descuentos
        p.line(430, 115, 580, 115)
        
        # Total general
        p.setFont("Helvetica-Bold", 9)
        p.drawString(430, 100, "TOTAL")
        p.drawString(550, 100, f"{factura.total_fac:,.2f} BS")

        # --- Nota y pie de página ---
        # Nota completa con saltos de línea adecuados
        p.setFont("Helvetica", 8)
        nota = "NO SE ACEPTAN PAGOS DE DIVISAS EN EFECTIVO HECHOS AL ASESOR DE VENTA NI AL SUPERVISOR, ASÍ COMO TAMPOCO BS EN EFECTIVO, PAGO MÓVIL O TRANSFERENCIAS A LAS CUENTAS PERSONALES DEL ASESOR O DEL SUPERVISOR. SOLO SE RECONOCERÁN LOS PAGOS HECHOS A LAS CUENTAS DE LA EMPRESA."
        
        # Dividir nota en líneas de máximo 100 caracteres
        nota_lineas = []
        for i in range(0, len(nota), 100):
            nota_lineas.append(nota[i:i+100])
        
        # Dibujar cada línea de la nota
        for i, linea in enumerate(nota_lineas):
            p.drawString(40, 80 - (i * 10), linea)
        
        # Referencias y tasa de cambio
        # p.drawString(40, 50, f"REFERENCIA: {getattr(factura, 'referencia', '')}")
        # p.drawString(200, 50, f"T.C.: {getattr(factura, 'tasa_cambio', '---')}")
        
        # Paginación (ajustada para no sobreponerse)
        p.drawString(470, 30, f"Página 1 de 1")
        
        # Footer
        p.setFont("Helvetica", 8)
        p.drawString(40, 30, "The Black System - Todos los derechos reservados")

        p.showPage()
        p.save()
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Recibo_Venta_{factura.id}.pdf"'
        return response

def comision_detail(request, empleado_id):
    try:
        empleado = Empleado.objects.get(id=empleado_id)
        mes_actual = datetime.now().month
        anio_actual = datetime.now().year
        ventas = Ventas.objects.filter(
            empleado=empleado,
            factura__fecha_fac__month=mes_actual,
            factura__fecha_fac__year=anio_actual
        ).exclude(status__vent_cancelada=True).filter(
            Q(credito=False) | Q(credito=True, monto_pagado__gte=F('factura__total_fac'))
        )
        total_comision = Decimal('0.00')
        ventas_detalle = []
        for venta in ventas:
            total_venta = venta.factura.total_fac
            rango_comision = ConsultaComision.objects.filter(
                rango_inferior__lte=total_venta,
                rango_superior__gte=total_venta
            ).first()
            porcentaje = rango_comision.porcentaje if rango_comision else Decimal('0.00')
            comision_venta = (total_venta * porcentaje / Decimal('100.00')) if rango_comision else Decimal('0.00')
            total_comision += comision_venta
            ventas_detalle.append({
                'factura': venta.factura,
                'comision': comision_venta,
                'porcentaje': porcentaje,
                'venta_id': venta.id
            })
        porcentaje_promedio = ''
        if ventas_detalle:
            suma_porcentajes = sum([v['porcentaje'] for v in ventas_detalle])
            porcentaje_promedio = suma_porcentajes / len(ventas_detalle)
            porcentaje_promedio = f"{porcentaje_promedio:.2f}"  # String para mostrar
        comision_data = {
            'empleado': empleado,
            'ventas': ventas.count(),
            'comision': total_comision,
            'porcentaje': porcentaje_promedio
        }
        context = {
            'titulo': f'Detalle de Comisión - {empleado.nombre} {empleado.apellido}',
            'comision': comision_data,
            'ventas_detalle': ventas_detalle
        }
        return render(request, 'black_invoices/comisiones/comision_detail.html', context)
    except Empleado.DoesNotExist:
        messages.error(request, 'El empleado no existe.')
        return redirect('black_invoices:comision_list')
    except Exception as e:
        messages.error(request, f'Error al cargar el detalle de comisión: {str(e)}')
        return redirect('black_invoices:comision_list')

class ComisionPDFView(LoginRequiredMixin, View):
    def get(self, request, empleado_id):
        try:
            empleado = Empleado.objects.get(id=empleado_id)
            mes_actual = datetime.now().month
            anio_actual = datetime.now().year
            
            # Definir fecha actual
            fecha_actual = datetime.now().strftime("%d/%m/%Y")
            
            # Obtener ventas completadas
            ventas = Ventas.objects.filter(
                empleado=empleado,
                factura__fecha_fac__month=mes_actual,
                factura__fecha_fac__year=anio_actual
            ).exclude(status__vent_cancelada=True).filter(
                Q(credito=False) | Q(credito=True, monto_pagado__gte=F('factura__total_fac'))
            )
            
            # Calcular comisiones
            total_comision = Decimal('0.00')
            ventas_detalle = []
            for venta in ventas:
                total_venta = venta.factura.total_fac
                rango_comision = ConsultaComision.objects.filter(
                    rango_inferior__lte=total_venta,
                    rango_superior__gte=total_venta
                ).first()
                porcentaje = rango_comision.porcentaje if rango_comision else Decimal('0.00')
                comision_venta = (total_venta * porcentaje / Decimal('100.00')) if rango_comision else Decimal('0.00')
                total_comision += comision_venta
                ventas_detalle.append({
                    'factura': venta.factura,
                    'comision': comision_venta,
                    'porcentaje': porcentaje,
                    'venta_id': venta.id
                })

            # Crear el PDF
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # --- Membrete y Logo ---
            logo_path = os.path.join(settings.BASE_DIR, 'black_invoices/static/img/the_black.jpeg')
            if os.path.exists(logo_path):
                p.drawImage(logo_path, 40, height - 110, width=120, height=60, preserveAspectRatio=True, mask='auto')
            
            # Nombre de la empresa y RIF
            p.setFont("Helvetica-Bold", 12)
            p.drawString(180, height - 50, "INDUSTRIA & HERRAMIENTA EL NEGRITO, C.A.")
            p.setFont("Helvetica-Bold", 11)
            p.drawString(180, height - 65, "RIF: J-406050717")
            
            # Dirección y teléfonos
            p.setFont("Helvetica", 10)
            p.drawString(180, height - 80, "CR 10 ENTRE CALLES 4 Y 5 EDIF DOÑA EDITH PISO 1 OF 2")
            p.drawString(180, height - 95, "BARRIO MATURIN GUANARE PORTUGUESA")
            p.drawString(180, height - 110, "Teléfonos: 0257-5143082 / 0257-5143082")
            
            # --- Título del reporte ---
            p.setFont("Helvetica-Bold", 13)
            p.drawString(50, height - 130, "REPORTE DE COMISIÓN")
            
            # --- Datos del empleado ---
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, height - 160, "Información del Empleado:")
            p.setFont("Helvetica", 10)
            p.drawString(50, height - 180, f"Nombre: {empleado.nombre} {empleado.apellido}")
            p.drawString(50, height - 195, f"Nivel de Acceso: {empleado.nivel_acceso.nombre}")
            
            # --- Añadir información de resumen de comisión ---
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, height - 225, "Resumen de Comisión:")
            p.setFont("Helvetica", 10)
            p.drawString(50, height - 245, f"Ventas Completadas: {ventas.count()}")
            p.drawString(50, height - 260, f"Total Comisión: ${total_comision:.2f}")
            
            # --- Detalle de las ventas (tabla) ---
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, height - 290, "Detalle de Ventas:")
            
            # Definir datos para la tabla
            data = [["Fecha", "Recibo #", "Cliente", "Total Venta", "% Comisión", "Comisión"]]
            
            for venta in ventas_detalle:
                data.append([
                    venta['factura'].fecha_fac.strftime("%d/%m/%Y"),
                    f"{venta['factura'].id}",
                    f"{venta['factura'].cliente.nombre} {venta['factura'].cliente.apellido}",
                    f"${venta['factura'].total_fac:.2f}",
                    f"{venta['porcentaje']}%",
                    f"${venta['comision']:.2f}"
                ])
            
            # Si no hay ventas, añadir una fila de "Sin datos"
            if len(data) == 1:
                data.append(["Sin datos", "", "", "", "", ""])
            
            # Configurar ancho de columnas
            col_widths = [70, 60, 150, 80, 80, 80]
            
            # Crear y configurar la tabla
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('ALIGN', (3, 1), (5, -1), 'RIGHT'),  # Alinear columnas numéricas a la derecha
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            # Calcular posición de la tabla
            table_height = len(data) * 20  # Estimación aproximada
            table_y = height - 320 - table_height  # Ajustar según necesidad
            
            # Dibujar la tabla
            table.wrapOn(p, width - 100, table_height)
            table.drawOn(p, 50, max(table_y, 100))  # Mínimo 100 para evitar que se salga
            
            # --- Información adicional ---
            # Si hay espacio, añadir información de rangos de comisión
            rangos = ConsultaComision.objects.all().order_by('rango_inferior')
            if rangos.exists() and table_y > 150:
                p.setFont("Helvetica-Bold", 10)
                p.drawString(50, table_y - 30, "Rangos de Comisión:")
                
                y_pos = table_y - 50
                p.setFont("Helvetica", 9)
                for i, rango in enumerate(rangos):
                    p.drawString(50, y_pos - (i * 15), 
                                f"${rango.rango_inferior:.2f} a ${rango.rango_superior:.2f}: {rango.porcentaje}%")
            
            # --- Pie de página ---
            p.setFont("Helvetica", 8)
            p.drawString(470, 30, f"Página 1 de 1")
            p.drawString(40, 30, "The Black System - Todos los derechos reservados")
            
            # Finalizar y devolver PDF
            p.showPage()
            p.save()
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Comision_{empleado.nombre}_{empleado.apellido}_{fecha_actual}.pdf"'
            return response
        
        except Exception as e:
            messages.error(request, f'Error al generar el PDF: {str(e)}')
            return redirect('black_invoices:comision_list')
        
    
from django.http import HttpResponse, JsonResponse
from django.core.management import call_command
from django.contrib.auth.decorators import login_required, user_passes_test # Para vistas basadas en funciones
from django.utils.decorators import method_decorator
import io
import json # Para la importación, para leer el archivo temporalmente
from datetime import datetime
import os # Para manejar archivos temporales
from django.conf import settings # Para la carpeta de archivos temporales
from .forms.backup_forms import DatabaseImportForm # Importar el nuevo formulario
from django.core.files.storage import FileSystemStorage    
def export_database_view(request):
    try:
        # Usaremos un buffer en memoria para no escribir al disco innecesariamente en el servidor
        buffer = io.StringIO()
        call_command('dumpdata', 'black_invoices', indent=2, stdout=buffer) # Solo datos de black_invoices
        # Si quieres TODO: call_command('dumpdata', indent=2, stdout=buffer, exclude=['contenttypes', 'auth.Permission'])
        
        buffer.seek(0)
        
        # Crear la respuesta HTTP para descargar el archivo
        response = HttpResponse(buffer.getvalue(), content_type='application/json')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response['Content-Disposition'] = f'attachment; filename="backup_theblacksystem_{timestamp}.json"'
        
        messages.success(request, "Exportación de datos completada exitosamente.")
        return response
    except Exception as e:
        messages.error(request, f"Error durante la exportación de datos: {str(e)}")
        # Considera redirigir a una página de error o de vuelta a configuraciones
        return redirect(request.META.get('HTTP_REFERER', reverse_lazy('black_invoices:inicio')))
    
def import_database_view(request):
    if request.method == 'POST':
        form = DatabaseImportForm(request.POST, request.FILES)
        if form.is_valid():
            backup_file = request.FILES['backup_file']
            
            # Guardar el archivo temporalmente de forma segura
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_backups')) # Crea una subcarpeta 'temp_backups' en tu MEDIA_ROOT
            if not os.path.exists(fs.location):
                os.makedirs(fs.location)
            
            filename = fs.save(backup_file.name, backup_file)
            uploaded_file_path = fs.path(filename)

            try:
                # Validar que es un JSON (opcional pero recomendado)
                with open(uploaded_file_path, 'r') as f:
                    json.load(f) # Intenta parsear, si falla, no es JSON válido

                # Ejecutar loaddata
                # ¡ADVERTENCIA! loaddata puede sobreescribir datos si las PKs coinciden o causar errores.
                # Es altamente recomendable que el admin sepa lo que está haciendo.
                # Considera hacer un backup ANTES de importar.
                call_command('loaddata', uploaded_file_path)
                messages.success(request, "Importación de datos completada exitosamente.")
            except json.JSONDecodeError:
                messages.error(request, "Error: El archivo proporcionado no es un JSON válido.")
            except Exception as e:
                messages.error(request, f"Error durante la importación de datos: {str(e)}")
            finally:
                # Eliminar el archivo temporal después de usarlo
                if os.path.exists(uploaded_file_path):
                    os.remove(uploaded_file_path)
            
            return redirect('black_invoices:importar_datos') # Redirige a la misma página para ver el mensaje
    else:
        form = DatabaseImportForm()

    return render(request, 'black_invoices/configuracion/importar_datos.html', {
        'titulo': 'Importar Base de Datos',
        'form': form
    })