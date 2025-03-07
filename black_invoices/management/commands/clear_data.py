from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User  # Añadimos esta importación
from black_invoices.models import *

class Command(BaseCommand):
    help = 'Limpia todos los datos de la base de datos'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Eliminando todos los datos...')
        
        try:
            # El orden correcto de eliminación basado en las dependencias
            self.stdout.write('Eliminando comisiones...')
            Comision.objects.all().delete()
            
            self.stdout.write('Eliminando detalles de factura...')
            DetalleFactura.objects.all().delete()
            
            self.stdout.write('Eliminando ventas...')
            Ventas.objects.all().delete()
            
            self.stdout.write('Eliminando facturas...')
            Factura.objects.all().delete()
            
            self.stdout.write('Eliminando tipos de factura...')
            TipoFactura.objects.all().delete()
            
            self.stdout.write('Eliminando configuraciones...')
            TablaConfig.objects.all().delete()
            
            self.stdout.write('Eliminando consultas de comisión...')
            ConsultaComision.objects.all().delete()
            
            self.stdout.write('Eliminando productos...')
            Producto.objects.all().delete()
            
            self.stdout.write('Eliminando clientes...')
            Cliente.objects.all().delete()
            
            self.stdout.write('Eliminando empleados...')
            Empleado.objects.all().delete()
            
            self.stdout.write('Eliminando niveles de acceso...')
            NivelAcceso.objects.all().delete()
            
            self.stdout.write('Eliminando estados de venta...')
            StatusVentas.objects.all().delete()

            # Añadimos la eliminación de usuarios
            self.stdout.write('Eliminando usuarios...')
            User.objects.exclude(is_superuser=True).delete()  # Mantiene al superusuario

            self.stdout.write(self.style.SUCCESS('Base de datos limpiada exitosamente'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la limpieza: {str(e)}'))
            raise e