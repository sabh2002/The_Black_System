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
                precio = Decimal(str(round(random.uniform(20, 300), 2)))

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
            # 1. Niveles de Acceso (ahora con porcentaje de comisión)
            self.stdout.write('Creando niveles de acceso...')
            nivel_admin = NivelAcceso.objects.create(
                nombre="Administrador",
                descripcion="Acceso total al sistema",

            )
            nivel_vendedor = NivelAcceso.objects.create(
                nombre="Vendedor",
                descripcion="Acceso a ventas y facturas",

            )
            nivel_supervisor = NivelAcceso.objects.create(
                nombre="Supervisor",
                descripcion="Supervisión de vendedores y reportes",

            )

            # 2. Rangos de Comisión (mantener por compatibilidad)
            self.stdout.write('Configurando rangos de comisión...')
            ConsultaComision.objects.create(
                rango_inferior=Decimal('0.00'),
                rango_superior=Decimal('100.00'),
                porcentaje=Decimal('5.00')
            )
            ConsultaComision.objects.create(
                rango_inferior=Decimal('101.00'),
                rango_superior=Decimal('500.00'),
                porcentaje=Decimal('10.00')
            )
            ConsultaComision.objects.create(
                rango_inferior=Decimal('501.00'),
                rango_superior=Decimal('999999.99'),
                porcentaje=Decimal('15.00')
            )

            # 3. Estados de Venta
            self.stdout.write('Creando estados de venta...')
            estado_completada = StatusVentas.objects.create(
                nombre="Completada"
            )
            estado_pendiente = StatusVentas.objects.create(
                nombre="Pendiente",
                vent_espera=True
            )
            estado_cancelada = StatusVentas.objects.create(
                nombre="Cancelada",
                vent_cancelada=True
            )
            self.stdout.write('Creando tipos de factura...')
            tipo_contado = TipoFactura.objects.create(contado_fac=True)
            tipo_credito = TipoFactura.objects.create(
                credito_fac=True,
                plazo_credito=30
            )
            # 4. Empleados
            self.stdout.write('Creando empleados...')
            empleados = []
            nombres = [
                ("Juan", "Pérez", nivel_vendedor),
                ("María", "González", nivel_vendedor),
                ("Carlos", "Rodríguez", nivel_supervisor),
                ("Ana", "Martínez", nivel_admin)
            ]

            for i, (nombre, apellido, nivel) in enumerate(nombres):
                username = f"empleado{i+1}"
                user = User.objects.create_user(
                    username=username,
                    password="empleado123",
                    first_name=nombre,
                    last_name=apellido
                )

                empleado = Empleado.objects.create(
                    user=user,
                    nombre=nombre,
                    apellido=apellido,
                    nivel_acceso=nivel
                )
                empleados.append(empleado)

            # 5. Clientes - ACTUALIZADO CON CÉDULAS
            self.stdout.write('Creando clientes...')
            clientes_data = [
                {
                    "cedula": "V12345678",
                    "nombre": "Maria",
                    "apellido": "Garcia",
                    "email": "mariagarcia@gmail.com",
                    "telefono": "04163354478",
                    "direccion": "Urb Sol del este, Calle 3, Casa #12"
                },
                {
                    "cedula": "V23456789",
                    "nombre": "Jose",
                    "apellido": "Rodriguez",
                    "email": "joserodriguez@outlook.com",
                    "telefono": "04263352234",
                    "direccion": "Barrio Santa Maria, Calle Principal"
                },
                {
                    "cedula": "V34567890",
                    "nombre": "Carlos",
                    "apellido": "Hernandez",
                    "email": "carloshernandez@gmail.com",
                    "telefono": "04123356689",
                    "direccion": "Urb Juan Pablo, Edificio A, Piso 2"
                },
                {
                    "cedula": "V45678901",
                    "nombre": "Ana",
                    "apellido": "Martinez",
                    "email": "anamartinez@outlook.com",
                    "telefono": "04243351123",
                    "direccion": "Barrio la Arenosa, Sector 2"
                },
                {
                    "cedula": "V56789012",
                    "nombre": "Luis",
                    "apellido": "Gonzalez",
                    "email": "luisgonzalez@gmail.com",
                    "telefono": "04143357745",
                    "direccion": "Barrio los Cortijos, Calle 5"
                },
                {
                    "cedula": "V67890123",
                    "nombre": "Carmen",
                    "apellido": "Lopez",
                    "email": "carmenlopez@outlook.com",
                    "telefono": "04163358896",
                    "direccion": "Urb El Placer, Casa #34"
                },
                {
                    "cedula": "V78901234",
                    "nombre": "Juan",
                    "apellido": "Perez",
                    "email": "juanperez@gmail.com",
                    "telefono": "04263351234",
                    "direccion": "Barrio Los proceres, Calle 8"
                },
                {
                    "cedula": "V89012345",
                    "nombre": "Sofia",
                    "apellido": "Diaz",
                    "email": "sofiadiaz@outlook.com",
                    "telefono": "04123354567",
                    "direccion": "Barrio La Pastora, Sector Central"
                },
                {
                    "cedula": "V90123456",
                    "nombre": "Pedro",
                    "apellido": "Sanchez",
                    "email": "pedrosanchez@gmail.com",
                    "telefono": "04243357890",
                    "direccion": "Barrio el Progreso, Calle 10"
                },
                {
                    "cedula": "V11223344",
                    "nombre": "Isabel",
                    "apellido": "Ramirez",
                    "email": "isabelramirez@outlook.com",
                    "telefono": "04143352345",
                    "direccion": "Urb La Granja, Casa #7"
                },
                {
                    "cedula": "V22334455",
                    "nombre": "Miguel",
                    "apellido": "Torres",
                    "email": "migueltorres@gmail.com",
                    "telefono": "04163355678",
                    "direccion": "Ubr Villa Guanare, Bloque 4"
                },
                {
                    "cedula": "E33445566",
                    "nombre": "Elena",
                    "apellido": "Flores",
                    "email": "elenaflores@outlook.com",
                    "telefono": "04263353456",
                    "direccion": "Urb Sol del este, Calle 7"
                },
                {
                    "cedula": "V44556677",
                    "nombre": "Ricardo",
                    "apellido": "Vargas",
                    "email": "ricardovargas@gmail.com",
                    "telefono": "04123356789",
                    "direccion": "Barrio Santa Maria, Sector 3"
                },
                {
                    "cedula": "V55667788",
                    "nombre": "Patricia",
                    "apellido": "Rojas",
                    "email": "patriciarojas@outlook.com",
                    "telefono": "04243350123",
                    "direccion": "Urb Juan Pablo, Edificio B"
                },
                {
                    "cedula": "V66778899",
                    "nombre": "Fernando",
                    "apellido": "Mendoza",
                    "email": "fernandomendoza@gmail.com",
                    "telefono": "04143354456",
                    "direccion": "Barrio la Arenosa, Calle 12"
                },
                {
                    "cedula": "V77889900",
                    "nombre": "Adriana",
                    "apellido": "Castillo",
                    "email": "adrianacastillo@outlook.com",
                    "telefono": "04163358901",
                    "direccion": "Barrio los Cortijos, Sector Norte"
                },
                {
                    "cedula": "E88990011",
                    "nombre": "Jorge",
                    "apellido": "Nunez",
                    "email": "jorgenunez@gmail.com",
                    "telefono": "04263351234",
                    "direccion": "Urb El Placer, Casa #21"
                },
                {
                    "cedula": "V99001122",
                    "nombre": "Gabriela",
                    "apellido": "Silva",
                    "email": "gabrielasilva@outlook.com",
                    "telefono": "04123354567",
                    "direccion": "Barrio Los proceres, Calle 15"
                },
                {
                    "cedula": "V10112233",
                    "nombre": "Raul",
                    "apellido": "Molina",
                    "email": "raulmolina@gmail.com",
                    "telefono": "04243357890",
                    "direccion": "Barrio La Pastora, Sector Este"
                },
                {
                    "cedula": "V21223344",
                    "nombre": "Daniela",
                    "apellido": "Reyes",
                    "email": "danielareyes@outlook.com",
                    "telefono": "04143352345",
                    "direccion": "Barrio el Progreso, Calle 8"
                }
            ]

            clientes = []
            for data in clientes_data:
                cliente = Cliente.objects.create(
                    cedula=data["cedula"],
                    nombre=data["nombre"],
                    apellido=data["apellido"],
                    email=data["email"],
                    telefono=data["telefono"],
                    direccion=data["direccion"]
                )
                clientes.append(cliente)
                self.stdout.write(f'Cliente creado: {cliente.cedula} - {cliente.nombre_completo}')

            # 6. Productos
            self.stdout.write('Creando productos...')
            productos = self.generate_products()

            # 7. Simulación de ventas
            self.stdout.write('Simulando ventas...')
            fecha_inicio = datetime.now() - timedelta(days=30)

            # Crear 50 ventas (70% contado, 30% crédito)
            for i in range(50):
                fecha = fecha_inicio + timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )

                # Determinar si es una venta a crédito (30% de probabilidad)
                es_credito = random.random() < 0.3

                # Crear factura
                factura = Factura.objects.create(
                    cliente=random.choice(clientes),
                    empleado=random.choice(empleados),
                    metodo_pag=random.choice(['efectivo', 'tarjeta', 'transferencia']) if not es_credito else 'credito',
                    fecha_fac=fecha
                )

                # Agregar entre 1 y 5 productos a la factura
                num_productos = random.randint(1, 5)
                productos_seleccionados = random.sample(productos, num_productos)

                # Calcular total para almacenar en la factura
                total_factura = 0

                for producto in productos_seleccionados:
                    cantidad = random.randint(1, 3)
                    subtotal = producto.precio * cantidad
                    total_factura += subtotal

                    # Reducir stock
                    if producto.stock >= cantidad:
                        producto.stock -= cantidad
                        producto.save()
                    else:
                        # Puedes manejar el caso de stock insuficiente
                        # Por ejemplo, reducir la cantidad a lo disponible
                        cantidad = producto.stock
                        producto.stock = 0
                        producto.save()

                    DetalleFactura.objects.create(
                        factura=factura,
                        tipo_factura=tipo_credito if es_credito else tipo_contado,
                        producto=producto,
                        cantidad=cantidad,
                        sub_total=subtotal
                    )

                # Actualizar total de factura
                factura.total_fac = total_factura
                factura.save()

                # Crear venta según tipo (contado o crédito)
                if es_credito:
                    # Es una venta a crédito
                    monto_pagado = 0

                    # Decidir si tiene pagos parciales (50% de probabilidad)
                    tiene_pagos = random.random() < 0.5
                    if tiene_pagos:
                        # Pagar entre 10% y 90% de la factura
                        porcentaje_pago = random.uniform(0.1, 0.9)
                        monto_pagado = Decimal(str(total_factura)) * Decimal(porcentaje_pago)


                    # Determinar estado según si está completamente pagado
                    estado = estado_completada if monto_pagado >= total_factura else estado_pendiente

                    venta = Ventas.objects.create(
                        empleado=factura.empleado,
                        factura=factura,
                        status=estado,
                        credito=True,
                        monto_pagado=monto_pagado
                    )

                    # Si tiene pagos parciales, crear registros de pago
                    if tiene_pagos and monto_pagado > 0:
                        # Entre 1 y 3 pagos
                        num_pagos = random.randint(1, 3)
                        monto_por_pago = monto_pagado / num_pagos

                        for _ in range(num_pagos):
                            fecha_pago = fecha + timedelta(days=random.randint(1, 15))
                            PagoVenta.objects.create(
                                venta=venta,
                                monto=monto_por_pago,
                                fecha=fecha_pago
                            )
                else:
                    # Es una venta al contado (completada)
                    Ventas.objects.create(
                        empleado=factura.empleado,
                        factura=factura,
                        status=estado_completada,
                        credito=False,
                        monto_pagado=total_factura
                    )

            self.stdout.write(self.style.SUCCESS('Datos de prueba configurados exitosamente'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la configuración: {str(e)}'))
            raise e
