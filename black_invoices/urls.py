from django.urls import path
from . import views

app_name = 'black_invoices'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='inicio'),
    
    path('facturas/', views.FacturaListView.as_view(), name='factura_list'),
    path('facturas/<int:pk>/pdf/', views.FacturaPDFView.as_view(), name='factura_pdf'),
    path('facturas/<int:pk>/', views.FacturaDetailView.as_view(), name='factura_detail'),

    # path('facturas/crear/', views.FacturaCreateView.as_view(), name='factura_create'),
    # # Clientes
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    path('clientes/<int:pk>/', views.ClienteDetailView.as_view(), name='cliente_detail'),
    path('clientes/editar/<int:pk>/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    #Productos
    path('productos/<int:pk>/', views.ProductoDetailView.as_view(), name='producto_detail'),
    path('productos/editar/<int:pk>/', views.ProductoUpdateView.as_view(), name='producto_update'),
    path('productos/', views.ProductoListView.as_view(), name='producto_list'),
    path('productos/crear/', views.ProductoCreateView.as_view(), name='producto_create'),
    path('productos/<int:pk>/stock/', views.ProductoStockUpdateView.as_view(), name='producto_stock'),
    path('rangos-comisiones/', views.RangosComisionesListView.as_view(), name='rangos_comisiones_list'),
    path('rangos-comisiones/crear/', views.RangosComisionesCreateView.as_view(), name='rangos_comisiones_create'),
    path('rangos-comisiones/editar/<int:pk>/', views.RangosComisionesUpdateView.as_view(), name='rangos_comisiones_update'),
    path('rangos-comisiones/eliminar/<int:pk>/', views.RangosComisionesDeleteView.as_view(), name='rangos_comisiones_delete'),


    path('clientes/crear/', views.ClienteCreateView.as_view(), name='cliente_create'),
    # # Ventas
    path('ventas/', views.VentaListView.as_view(), name='venta_list'),
    path('ventas/crear/', views.VentaCreateView.as_view(), name='venta_create'),
    path('ventas/<int:pk>/', views.VentaDetailView.as_view(), name='venta_detail'),
    path('ventas/<int:pk>/cancelar/', views.cancelar_venta, name='cancelar_venta'),
    path('ventas/pendientes/', views.VentasPendientesView.as_view(), name='ventas_pendientes'),
    path('ventas/<int:pk>/pago/', views.RegistrarPagoView.as_view(), name='registrar_pago'),
    path('ventas/autorizacion/', views.VentasAutorizacionView.as_view(), name='ventas_autorizacion'),
    path('ventas/autorizar/<int:pk>/', views.AutorizarVentaView.as_view(), name='autorizar_venta'),

    # # Empleados
    path('empleados/', views.EmpleadoListView.as_view(), name='empleado_list'),
    path('empleados/crear/', views.EmpleadoCreateView.as_view(), name='empleado_create'),
    path('empleados/<int:pk>/editar/', views.EmpleadoUpdateView.as_view(), name='empleado_update'),
    path('accounts/login/', views.ingresar, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('comisiones/', views.ComisionListView.as_view(), name='comision_list'),
    path('comisiones/<int:empleado_id>/', views.comision_detail, name='comision_detail'),
    path('comisiones/<int:empleado_id>/pdf/', views.ComisionPDFView.as_view(), name='comision_pdf'),
    path('perfil/editar/', views.UserProfileUpdateView.as_view(), name='perfil_usuario_editar'),
    path('configuracion/exportar-datos/', views.export_database_view, name='exportar_datos'),
    path('configuracion/importar-datos/', views.import_database_view, name='importar_datos'),
    path('productos/mas-vendidos/', views.ProductosMasVendidosView.as_view(), name='productos_mas_vendidos'),
    path('productos/mas-vendidos/pdf', views.ProductosMasVendidosPDFView.as_view(), name='productos_mas_vendidos_pdf'),
    path('comisiones/historial/', views.HistorialComisionesView.as_view(), name='historial_comisiones'),
    path('configuracion/tasa-cambio/', views.TasaCambioListView.as_view(), name='tasa_cambio_list'),
    path('configuracion/tasa-cambio/crear/', views.TasaCambioCreateView.as_view(), name='tasa_cambio_create'),
    path('configuracion/tasa-cambio/editar/<int:pk>/', views.TasaCambioUpdateView.as_view(), name='tasa_cambio_update'),
    # ...
# URL para editar perfil

]
