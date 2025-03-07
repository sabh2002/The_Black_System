from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
from django.db import transaction
from ...models import *
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Configura datos de prueba para el sistema de refacciones'

    def generate_products(self):
        # Categorías comunes de refacciones
        categories = [
            ("Motor", [
                "Pistón", "Anillos", "Biela", "Válvulas", "Bomba de aceite",
                "Cojinetes", "Árbol de levas", "Cigüeñal"
            ]),
            ("Frenos", [
                "Pastillas", "Discos", "Zapatas", "Cilindro maestro",
                "Calibradores", "Mangueras"
            ]),
            ("Suspensión", [
                "Amortiguadores", "Resortes", "Rótulas", "Brazos de control",
                "Bujes", "Terminales"
            ]),
            ("Transmisión", [
                "Embrague", "Volante motor", "Caja de cambios", "Diferencial",
                "Cardán", "Juntas homocinéticas"
            ])
        ]
        
        productos = []
        for categoria, partes in categories:
            for parte in partes:
                precio = round(random.uniform(50, 1500), 2)
                stock = random.randint(10, 100)
                descripcion = f"Refacción {parte} de alta calidad para vehículos"
                
                producto = Producto.objects.create(
                    nombre=f"{parte}",
                    descripcion=descripcion,
                    precio=precio,
                    stock=stock,
                    activo=True
                )
                productos.append(producto)
        
        return productos

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando configuración de datos de prueba...')

        try:
            # 1. Niveles de Acceso
            self.stdout.write('Creando niveles de acceso...')
            nivel_admin = NivelAcceso.objects.create(
                nombre="Administrador",
                descripcion="Acceso total al sistema"
            )
            nivel_vendedor = NivelAcceso.objects.create(
                nombre="Vendedor",
                descripcion="Acceso a ventas y facturas"
            )

            # 2. Rangos de Comisión
            self.stdout.write('Configurando rangos de comisión...')
            ConsultaComision.objects.create(
                rango_inferior=Decimal('0.00'),
                rango_superior=Decimal('1000.00'),
                porcentaje=Decimal('5.00')
            )
            ConsultaComision.objects.create(
                rango_inferior=Decimal('1001.00'),
                rango_superior=Decimal('5000.00'),
                porcentaje=Decimal('10.00')
            )
            ConsultaComision.objects.create(
                rango_inferior=Decimal('5001.00'),
                rango_superior=Decimal('999999.99'),
                porcentaje=Decimal('15.00')
            )

            # 3. Estados de Venta
            self.stdout.write('Creando estados de venta...')
            estado_completada = StatusVentas.objects.create(
                nombre="Completada"
            )
            estado_espera = StatusVentas.objects.create(
                nombre="En Espera",
                vent_espera=True
            )
            estado_cancelada = StatusVentas.objects.create(
                nombre="Cancelada",
                vent_cancelada=True
            )

            # 4. Empleados
            self.stdout.write('Creando empleados...')
            empleados = []
            nombres = [
                ("Juan", "Pérez"), ("María", "González"), 
                ("Carlos", "Rodríguez"), ("Ana", "Martínez")
            ]
            
            for i, (nombre, apellido) in enumerate(nombres):
                username = f"vendedor{i+1}"
                user = User.objects.create_user(
                    username=username,
                    password="vendedor123",
                    first_name=nombre,
                    last_name=apellido
                )
                
                empleado = Empleado.objects.create(
                    user=user,
                    nombre=nombre,
                    apellido=apellido,
                    nivel_acceso=nivel_vendedor
                )
                empleados.append(empleado)

            # 5. Clientes
            self.stdout.write('Creando clientes...')
            clientes = []
            for i in range(20):
                cliente = Cliente.objects.create(
                    nombre=f"Cliente{i+1}",
                    apellido=f"Apellido{i+1}",
                    email=f"cliente{i+1}@example.com",
                    telefono=f"555-{i:04d}",
                    direccion=f"Dirección {i+1}"
                )
                clientes.append(cliente)

            # 6. Productos
            self.stdout.write('Creando productos...')
            productos = self.generate_products()

            # 7. Tipos de Factura
            self.stdout.write('Configurando tipos de factura...')
            tipo_contado = TipoFactura.objects.create(contado_fac=True)
            tipo_credito = TipoFactura.objects.create(
                credito_fac=True,
                plazo_credito=30
            )

            # 8. Simular ventas durante el último mes
            self.stdout.write('Simulando ventas...')
            fecha_inicio = datetime.now() - timedelta(days=30)
            
            for _ in range(50):  # 50 ventas
                fecha = fecha_inicio + timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                # Crear factura
                factura = Factura.objects.create(
                    cliente=random.choice(clientes),
                    empleado=random.choice(empleados),
                    metodo_pag=random.choice(['efectivo', 'tarjeta', 'transferencia']),
                    fecha_fac=fecha
                )

                # Agregar entre 1 y 5 productos a la factura
                num_productos = random.randint(1, 5)
                productos_seleccionados = random.sample(productos, num_productos)
                
                for producto in productos_seleccionados:
                    cantidad = random.randint(1, 3)
                    DetalleFactura.objects.create(
                        factura=factura,
                        tipo_factura=tipo_contado,
                        producto=producto,
                        cantidad=cantidad
                    )

                # Crear venta (esto generará la comisión automáticamente)
                Ventas.objects.create(
                    empleado=factura.empleado,
                    factura=factura,
                    status=estado_completada,
                    fecha_venta=fecha
                )

            self.stdout.write(self.style.SUCCESS('Datos de prueba configurados exitosamente'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la configuración: {str(e)}'))
            raise e