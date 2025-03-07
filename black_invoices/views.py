from datetime import datetime
import json
import math as m
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import *
from .forms.producto_forms import ProductoForm
from .forms.cliente_forms import ClienteForm
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


########################        EMPLEADOS       #############
class EmpleadoListView(LoginRequiredMixin, ListView):
    model = Empleado
    template_name = 'black_invoices/empleados/empleados_list.html'
    context_object_name = 'empleados'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Lista de Empleados'
        return context
    
#######################     FACTURAS        ######################
class FacturaListView(LoginRequiredMixin, ListView):
    model = Factura
    template_name = 'black_invoices/facturas/facturas_list.html'
    context_object_name = 'facturas'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Lista de Facturas'
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

class VentaCreateView(LoginRequiredMixin, CreateView):
    model = Factura
    form_class = FacturaForm
    template_name = 'black_invoices/ventas/venta_form.html'
    success_url = reverse_lazy('black_invoices:venta_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nueva Venta'
        
        if self.request.POST:
            context['detalles_formset'] = DetalleFacturaFormSet(self.request.POST)
        else:
            context['detalles_formset'] = DetalleFacturaFormSet()
            
        # Mejorar la serialización de productos
        productos = Producto.objects.filter(activo=True).values('id', 'nombre', 'precio', 'stock')
        # Convertir Decimal a float para mejor compatibilidad con JavaScript
        productos_list = []
        for p in productos:
            p['precio'] = float(p['precio'])
            productos_list.append(p)
        
        context['productos_json'] = json.dumps(productos_list, cls=DjangoJSONEncoder)
        
        return context
    
    # def form_valid(self, form):
    #     context = self.get_context_data()
    #     formset = context['detalles_formset']
        
    #     with transaction.atomic():
    #         # Establecer el empleado basado en el usuario actual
    #         factura = form.save(commit=False)
    #         factura.empleado = self.request.user.empleado
    #         factura.save()
            
    #         # Guardar los detalles si son válidos
    #         if formset.is_valid():
    #             formset.instance = factura
    #             formset.save()
                
    #             # Crear la venta automáticamente
    #             estado = StatusVentas.objects.get(nombre="Completada")
    #             venta = Ventas.objects.create(
    #                 empleado=factura.empleado,
    #                 factura=factura,
    #                 status=estado
    #             )
                
    #             # Calcular el total de la factura
    #             factura.calcular_total()
                
    #             messages.success(self.request, f'Venta #{venta.id} creada exitosamente.')
    #             return super().form_valid(form)
    #         else:
    #             return self.form_invalid(form)
                
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['detalles_formset']
        
        try:
            with transaction.atomic():
                # Establecer el empleado basado en el usuario actual
                factura = form.save(commit=False)
                factura.empleado = self.request.user.empleado
                factura.save()
                
                # Guardar los detalles si son válidos
                if formset.is_valid():
                    detalles = formset.save(commit=False)
                    
                    # Verificar stock y calcular subtotales manualmente
                    for detalle in detalles:
                        detalle.factura = factura
                        
                        # Verificar stock
                        if detalle.producto.stock < detalle.cantidad:
                            raise ValueError(f"Stock insuficiente para {detalle.producto.nombre}. Disponible: {detalle.producto.stock}")
                        
                        # Calcular subtotal
                        detalle.sub_total = detalle.cantidad * detalle.producto.precio
                        
                        # Actualizar stock ANTES de guardar
                        detalle.producto.stock -= detalle.cantidad
                        detalle.producto.save(update_fields=['stock'])
                        
                        # Guardar detalle
                        detalle.save()
                    
                    # Procesar eliminaciones
                    for obj in formset.deleted_objects:
                        obj.delete()
                    
                    # Crear la venta automáticamente
                    estado = StatusVentas.objects.get(nombre="Completada")
                    venta = Ventas.objects.create(
                        empleado=factura.empleado,
                        factura=factura,
                        status=estado
                    )
                    
                    # Calcular el total de la factura
                    factura.calcular_total()
                    
                    messages.success(self.request, f'Venta #{venta.id} creada exitosamente.')
                    return super().form_valid(form)
                else:
                    return self.form_invalid(form)
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

class VentaListView(LoginRequiredMixin, ListView):
    model = Ventas
    template_name = 'black_invoices/ventas/ventas_list.html'
    context_object_name = 'ventas'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Lista de Ventas'
        context['create_url'] = reverse_lazy('black_invoices:venta_create')
        return context


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


######################      COMISIONES      ###############3
class ComisionListView(LoginRequiredMixin, ListView):
    model = Comision
    template_name = 'black_invoices/comisiones/comision_list.html'
    context_object_name = 'comisiones'

    def get_queryset(self):
        if hasattr(self.request.user, 'empleado'):

            if self.request.user.empleado.nivel_acceso.nombre == "Administrador":
                return Comision.objects.all()
            
            else:
                return Comision.objects.filter(empleado=self.request.user.empleado)
        
        return Comision.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Comisiones'


        #Estadisticas

        if hasattr(self.request.user, 'empleado'):
            empleado = self.request.user.empleado
            mes_actual = datetime.now().month
            anio_actual = datetime.now().year

            context['total_mes'] = empleado.get_comisiones_mes(mes_actual, anio_actual)
            context['total_año'] = sum(
                empleado.get_comisiones_mes(m, anio_actual)
                for m in range(1, mes_actual + 1)
            )
        
        return context



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
        # Obtener la factura
        try:
            factura = Factura.objects.get(pk=pk)
        except Factura.DoesNotExist:
            return HttpResponse("Factura no encontrada", status=404)
        
        # Crear el buffer y el canvas
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Encabezado
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "The Black System")
        
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 70, "Factura de Venta")
        
        # Datos de la factura
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, height - 100, f"Factura #{factura.id}")
        p.drawString(300, height - 100, f"Fecha: {factura.fecha_fac.strftime('%d/%m/%Y')}")
        
        # Datos del cliente
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, height - 130, "Datos del Cliente:")
        
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 150, f"Cliente: {factura.cliente.nombre} {factura.cliente.apellido}")
        p.drawString(50, height - 165, f"Email: {factura.cliente.email}")
        p.drawString(50, height - 180, f"Teléfono: {factura.cliente.telefono}")
        
        # Datos del vendedor
        p.setFont("Helvetica-Bold", 12)
        p.drawString(300, height - 130, "Vendedor:")
        
        p.setFont("Helvetica", 10)
        p.drawString(300, height - 150, f"{factura.empleado.nombre} {factura.empleado.apellido}")
        
        # Tabla de productos
        detalles = factura.detallefactura_set.all()
        
        data = [["Producto", "Precio", "Cantidad", "Subtotal"]]
        
        for detalle in detalles:
            data.append([
                detalle.producto.nombre,
                f"${detalle.producto.precio}",
                str(detalle.cantidad),
                f"${detalle.sub_total}"
            ])
        
        # Agregar total
        data.append(["", "", "Total:", f"${factura.total_fac}"])
        
        # Crear tabla
        table = Table(data, colWidths=[200, 100, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -2), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ]))
        
        # Dibujar tabla
        table.wrapOn(p, width, height)
        table.drawOn(p, 50, height - 300)
        
        # Pie de página
        p.setFont("Helvetica", 8)
        p.drawString(50, 30, "The Black System - Todos los derechos reservados")
        
        # Guardar PDF
        p.showPage()
        p.save()
        
        # Preparar respuesta
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="factura_{factura.id}.pdf"'
        
        return response