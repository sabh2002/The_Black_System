from django.urls import path
from . import views

app_name = 'black_invoices'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='inicio'),
    
    path('facturas/', views.FacturaListView.as_view(), name='factura_list'),
    path('facturas/<int:pk>/pdf/', views.FacturaPDFView.as_view(), name='factura_pdf'),

    # path('facturas/crear/', views.FacturaCreateView.as_view(), name='factura_create'),
    # # Clientes
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    path('productos/', views.ProductoListView.as_view(), name='producto_list'),
    path('productos/crear/', views.ProductoCreateView.as_view(), name='producto_create'),


    path('clientes/crear/', views.ClienteCreateView.as_view(), name='cliente_create'),
    # # Ventas
    path('ventas/', views.VentaListView.as_view(), name='venta_list'),
    path('ventas/crear/', views.VentaCreateView.as_view(), name='venta_create'),
    path('ventas/<int:pk>/', views.VentaDetailView.as_view(), name='venta_detail'),
    path('ventas/<int:pk>/cancelar/', views.cancelar_venta, name='cancelar_venta'),

    # # Empleados
    path('empleados/', views.EmpleadoListView.as_view(), name='empleado_list'),
    # path('empleados/crear/', views.EmpleadoCreateView.as_view(), name='empleado_create'),
    path('empleados/comisiones/', views.ComisionListView.as_view(), name='comision_list'),
    path('accounts/login/', views.ingresar, name='login'),
    path('logout/', views.logout_view, name='logout')
]
