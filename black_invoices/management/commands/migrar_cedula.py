from django.core.management.base import BaseCommand
from django.db import transaction
from ...models import Cliente
import random

class Command(BaseCommand):
    help = 'Migra clientes existentes asignando cédulas válidas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Modo interactivo para asignar cédulas manualmente',
        )
        parser.add_argument(
            '--auto',
            action='store_true',
            help='Asignar cédulas automáticamente (solo para testing)',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Iniciando migración de cédulas de clientes...')
        
        # Buscar clientes con cédulas temporales o inválidas
        clientes_sin_cedula = Cliente.objects.filter(
            cedula__in=['V00000000', 'E00000000', '']
        ).order_by('fecha_registro')
        
        if not clientes_sin_cedula.exists():
            self.stdout.write(
                self.style.SUCCESS('No hay clientes que requieran migración de cédula.')
            )
            return
        
        self.stdout.write(f'Encontrados {clientes_sin_cedula.count()} clientes que requieren cédula.')
        
        if options['interactive']:
            self.migrar_interactivo(clientes_sin_cedula)
        elif options['auto']:
            self.migrar_automatico(clientes_sin_cedula)
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Debe especificar --interactive o --auto. '
                    'Use --interactive para asignar cédulas manualmente.'
                )
            )
    
    def migrar_interactivo(self, clientes):
        """Migración interactiva donde el administrador asigna cédulas"""
        cedulas_usadas = set(
            Cliente.objects.exclude(
                cedula__in=['V00000000', 'E00000000', '']
            ).values_list('cedula', flat=True)
        )
        
        for cliente in clientes:
            self.stdout.write(f'\n--- Cliente: {cliente.nombre} {cliente.apellido} ---')
            self.stdout.write(f'Email: {cliente.email or "No registrado"}')
            self.stdout.write(f'Teléfono: {cliente.telefono}')
            self.stdout.write(f'Dirección: {cliente.direccion}')
            self.stdout.write(f'Cédula actual: {cliente.cedula}')
            
            while True:
                cedula = input('Ingrese la cédula (V12345678 o E12345678): ').strip().upper()
                
                if not cedula:
                    continuar = input('¿Saltar este cliente? (s/N): ').strip().lower()
                    if continuar == 's':
                        break
                    continue
                
                # Normalizar cédula
                cedula = cedula.replace('-', '')
                
                # Validar formato
                if not self.validar_cedula(cedula):
                    self.stdout.write(
                        self.style.ERROR('Formato inválido. Use V12345678 o E12345678')
                    )
                    continue
                
                # Verificar si ya existe
                if cedula in cedulas_usadas:
                    self.stdout.write(
                        self.style.ERROR('Esta cédula ya está registrada')
                    )
                    continue
                
                # Asignar cédula
                cliente.cedula = cedula
                try:
                    cliente.save()
                    cedulas_usadas.add(cedula)
                    self.stdout.write(
                        self.style.SUCCESS(f'Cédula {cedula} asignada correctamente')
                    )
                    break
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error al guardar: {str(e)}')
                    )
    
    def migrar_automatico(self, clientes):
        """Migración automática para testing (genera cédulas aleatorias)"""
        self.stdout.write(
            self.style.WARNING(
                'ADVERTENCIA: Esto generará cédulas ficticias solo para testing'
            )
        )
        
        cedulas_usadas = set(
            Cliente.objects.exclude(
                cedula__in=['V00000000', 'E00000000', '']
            ).values_list('cedula', flat=True)
        )
        
        for cliente in clientes:
            while True:
                # Generar cédula aleatoria
                tipo = random.choice(['V', 'E'])
                numero = random.randint(1000000, 99999999)
                cedula = f"{tipo}{numero}"
                
                if cedula not in cedulas_usadas:
                    cliente.cedula = cedula
                    cliente.save()
                    cedulas_usadas.add(cedula)
                    self.stdout.write(f'Cliente {cliente.nombre}: {cedula}')
                    break
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Migración automática completada para {clientes.count()} clientes'
            )
        )
    
    def validar_cedula(self, cedula):
        """Valida el formato de una cédula"""
        if len(cedula) < 7 or len(cedula) > 9:
            return False
        
        if not cedula.startswith(('V', 'E')):
            return False
        
        numero_parte = cedula[1:]
        if not numero_parte.isdigit():
            return False
        
        if len(numero_parte) < 6 or len(numero_parte) > 8:
            return False
        
        return True