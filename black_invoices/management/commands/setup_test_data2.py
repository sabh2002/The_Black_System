# black_invoices/management/commands/test_data_2.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
from black_invoices.models import *
from django.db import transaction
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Configura datos de prueba alternativos para el sistema'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando configuración de datos de prueba alternativos...')

        try:
            # 1. Niveles de Acceso
            nivel_gerente = NivelAcceso.objects.create(
                nombre="Gerente",
                descripcion="Acceso a reportes y configuraciones"
            )
            nivel_cajero = NivelAcceso.objects.create(
                nombre="Cajero",
                descripcion="Acceso a ventas y facturas básicas"
            )

            # 2. Rangos de Comisión más detallados
            rangos = [
                (0, 100, 5),
                (101, 500, 7),
                (501, 1000, 10),
                (1001, 5000, 12),
                (5001, 10000, 15)
            ]

            for inf, sup, porc in rangos:
                ConsultaComision.objects.create(
                    rango_inferior=Decimal(str(inf)),
                    rango_superior=Decimal(str(sup)),
                    porcentaje=Decimal(str(porc))
                )

            # 3. Estados de Venta
            estado_completada = StatusVentas.objects.create(nombre="Completada")
            estado_espera = StatusVentas.objects.create(
                nombre="En Espera",
                vent_espera=True
            )
            estado_cancelada = StatusVentas.objects.create(
                nombre="Cancelada",
                vent_cancelada=True
            )

            # 4. Empleados
            # Crear gerente
            user_gerente = User.objects.create_user(
                username='gerente',
                password='gerente123',
                first_name='Carlos',
                last_name='Rodríguez'
            )
            
            gerente = Empleado.objects.create(
                user=user_gerente,
                nombre='Carlos',
                apellido='Rodríguez',
                nivel_acceso=nivel_gerente
            )

            # Crear cajero
            user_cajero = User.objects.create_user(
                username='cajero',
                password='cajero123',
                first_name='Ana',
                last_name='López'
            )
            
            cajero = Empleado.objects.create(
                user=user_cajero,
                nombre='Ana',
                apellido='López',
                nivel_acceso=nivel_cajero
            )

            # 5. Clientes
            clientes = [
                Cliente.objects.create(
                    nombre='Pedro',
                    apellido='Martínez',
                    email='pedro@example.com',
                    telefono='1234567890',
                    direccion='Av. Principal 123'
                ),
                Cliente.objects.create(
                    nombre='Laura',
                    apellido='Sánchez',
                    email='laura@example.com',
                    telefono='0987654321',
                    direccion='Calle Secundaria 456'
                )
            ]

            # 6. Productos más variados
            productos = [
                Producto.objects.create(
                    nombre='Smartphone X',
                    descripcion='Último modelo',
                    precio=Decimal('799.99'),
                    stock=15
                ),
                Producto.objects.create(
                    nombre='Tablet Pro',
                    descripcion='10 pulgadas',
                    precio=Decimal('499.99'),
                    stock=20
                ),
                Producto.objects.create(
                    nombre='Auriculares BT',
                    descripcion='Bluetooth 5.0',
                    precio=Decimal('89.99'),
                    stock=30
                )
            ]

            # 7. Tipos de Factura
            tipo_contado = TipoFactura.objects.create(contado_fac=True)
            tipo_credito = TipoFactura.objects.create(
                credito_fac=True,
                plazo_credito=30
            )

            # 8. Simular múltiples ventas
            for cliente in clientes:
                factura = Factura.objects.create(
                    cliente=cliente,
                    empleado=cajero,
                    metodo_pag='efectivo'
                )

                # Agregar productos aleatorios
                DetalleFactura.objects.create(
                    factura=factura,
                    tipo_factura=tipo_contado,
                    producto=productos[0],
                    cantidad=1
                )
                
                DetalleFactura.objects.create(
                    factura=factura,
                    tipo_factura=tipo_contado,
                    producto=productos[1],
                    cantidad=1
                )

                venta = Ventas.objects.create(
                    empleado=cajero,
                    factura=factura,
                    status=estado_completada
                )

                Comision.objects.create(
                    empleado=cajero,
                    venta=venta,
                    monto_comision=factura.total_venta
                )

            self.stdout.write(self.style.SUCCESS('Datos de prueba alternativos configurados exitosamente'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la configuración: {str(e)}'))
            raise e