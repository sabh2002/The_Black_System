from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.contrib.auth.models import User
from ...models import *

class Command(BaseCommand):
    help = 'Limpia todos los datos del sistema, excepto el superusuario'

    def table_exists(self, table_name):
        """Verifica si una tabla existe en la base de datos"""
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)
            return table_name in tables

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando limpieza de datos...')
        
        try:
            # Preservar superusuarios
            superusers = list(User.objects.filter(is_superuser=True).values_list('id', flat=True))
            
            # Verificar y eliminar pagos de ventas solo si existe la tabla
            if self.table_exists('black_invoices_pagoventa'):
                self.stdout.write('Eliminando pagos de ventas...')
                # Verificamos si la clase existe en el modelo actual
                if 'PagoVenta' in globals():
                    PagoVenta.objects.all().delete()
                else:
                    self.stdout.write('Modelo PagoVenta no definido, omitiendo...')
            else:
                self.stdout.write('La tabla de pagos de ventas no existe, omitiendo...')
            
            self.stdout.write('Eliminando ventas...')
            Ventas.objects.all().delete()
            
            self.stdout.write('Eliminando detalles de facturas...')
            DetalleFactura.objects.all().delete()
            
            self.stdout.write('Eliminando facturas...')
            Factura.objects.all().delete()
            
            self.stdout.write('Eliminando productos...')
            Producto.objects.all().delete()
            
            self.stdout.write('Eliminando clientes...')
            Cliente.objects.all().delete()
            
            # Eliminar empleados pero preservar superusuarios
            self.stdout.write('Eliminando empleados (excepto administradores principales)...')
            empleados = Empleado.objects.exclude(user__id__in=superusers)
            empleados.delete()
            
            # Eliminar usuarios normales (no superusuarios)
            self.stdout.write('Eliminando usuarios (excepto superusuarios)...')
            User.objects.exclude(id__in=superusers).delete()
            
            self.stdout.write('Eliminando estados de venta...')
            StatusVentas.objects.all().delete()
            
            self.stdout.write('Eliminando rangos de comisión...')
            ConsultaComision.objects.all().delete()
            
            self.stdout.write('Eliminando niveles de acceso...')
            NivelAcceso.objects.all().delete()
            
            self.stdout.write(self.style.SUCCESS('Todos los datos han sido eliminados exitosamente'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la limpieza: {str(e)}'))
            raise e