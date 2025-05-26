from django.utils import timezone
from django.db import models
from django.core.validators import MinValueValidator, RegexValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# Create your models here.
class NivelAcceso(models.Model):
    nombre = models.CharField(max_length=20)
    descripcion = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Nivel de Acceso"
        verbose_name_plural = "Niveles de Acceso"

    def __str__(self):
        return self.nombre
    

class Cliente(models.Model):
    # Validador para cédula venezolana (V o E seguido de 6-8 dígitos)
    cedula_validator = RegexValidator(
        regex=r'^[VE]-?\d{6,8}$',
        message='La cédula debe tener el formato V12345678 o E12345678'
    )
    
    cedula = models.CharField(
        max_length=12, 
        unique=True,
        validators=[cedula_validator],
        verbose_name="Cédula",
        help_text="Formato: V12345678 o E12345678"
    )
    nombre = models.CharField(max_length=20, verbose_name="Nombre")
    apellido = models.CharField(max_length=20, verbose_name='Apellido')
    
    # Hacer email opcional y no único
    email = models.EmailField(
        max_length=254, 
        blank=True, 
        null=True,
        verbose_name="Correo Electrónico (Opcional)"
    )
    
    telefono = models.CharField(max_length=15, verbose_name="Teléfono")
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    
    # Campos de auditoría
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.cedula} - {self.nombre} {self.apellido}"
    
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Normalizar cédula (remover guiones y convertir a mayúsculas)
        if self.cedula:
            self.cedula = self.cedula.replace('-', '').upper()
            
            # Validar que tenga el formato correcto después de normalizar
            if not self.cedula.startswith(('V', 'E')):
                raise ValidationError({'cedula': 'La cédula debe comenzar con V o E'})
            
            # Validar que después de V o E solo haya números
            numero_parte = self.cedula[1:]
            if not numero_parte.isdigit():
                raise ValidationError({'cedula': 'Después de V o E solo debe haber números'})
            
            # Validar longitud de la parte numérica
            if len(numero_parte) < 6 or len(numero_parte) > 8:
                raise ValidationError({'cedula': 'La cédula debe tener entre 6 y 8 dígitos después de V o E'})
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Ejecutar validaciones antes de guardar
        super().save(*args, **kwargs)
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del cliente"""
        return f"{self.nombre} {self.apellido}"
    
    @property
    def cedula_formateada(self):
        """Retorna la cédula con formato legible"""
        if self.cedula and len(self.cedula) > 1:
            return f"{self.cedula[0]}-{self.cedula[1:]}"
        return self.cedula

class Producto(models.Model):
    # Constantes para validaciones
    PRECIO_MINIMO = 0.01
    PRECIO_MAXIMO = 5000.00
    STOCK_MINIMO = 0
    STOCK_MAXIMO = 100000

    nombre = models.CharField(
        max_length=20,
        verbose_name="Nombre",
        unique=True
    )
    
    descripcion = models.TextField(
        max_length=200,
        verbose_name='Descripción',
        help_text="Describe las características del producto"
    )
    
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio",
        validators=[
            MinValueValidator(PRECIO_MINIMO, message=f"El precio no puede ser menor a ${PRECIO_MINIMO}"),
            MaxValueValidator(PRECIO_MAXIMO, message=f"El precio no puede ser mayor a ${PRECIO_MAXIMO:,.2f}")
        ],
        help_text=f"Precio en dólares (Máximo: ${PRECIO_MAXIMO:,.2f})"
    )
    
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock disponible",
        validators=[
            MaxValueValidator(STOCK_MAXIMO, message=f"El stock no puede ser mayor a {STOCK_MAXIMO:,} unidades")
        ],
        help_text=f"Cantidad disponible (Máximo: {STOCK_MAXIMO:,} unidades)"
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Producto activo"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última modificación"
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    
    def clean(self):
        """Validaciones personalizadas del modelo"""
        super().clean()
        
        # Validación de precio
        if self.precio is not None:
            if self.precio < self.PRECIO_MINIMO:
                raise ValidationError({
                    'precio': f'El precio no puede ser menor a ${self.PRECIO_MINIMO}'
                })
            elif self.precio > self.PRECIO_MAXIMO:
                raise ValidationError({
                    'precio': f'El precio no puede ser mayor a ${self.PRECIO_MAXIMO:,.2f}'
                })
        
        # Validación de stock
        if self.stock is not None:
            if self.stock < self.STOCK_MINIMO:
                raise ValidationError({
                    'stock': f'El stock no puede ser menor a {self.STOCK_MINIMO}'
                })
            elif self.stock > self.STOCK_MAXIMO:
                raise ValidationError({
                    'stock': f'El stock no puede ser mayor a {self.STOCK_MAXIMO:,} unidades'
                })
    
    def save(self, *args, **kwargs):
        """Ejecutar validaciones antes de guardar"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def stock_available(self):
        """Verifica si hay stock disponible"""
        return self.stock > 0
    
    def is_low_stock(self, threshold=5):
        """Verifica si el stock está bajo"""
        return self.stock <= threshold
    
    def get_stock_status(self):
        """Retorna el estado del stock"""
        if self.stock <= 0:
            return 'sin_stock'
        elif self.stock <= 5:
            return 'stock_bajo'
        elif self.stock <= 20:
            return 'stock_medio'
        else:
            return 'stock_alto'
    
    def get_stock_badge_class(self):
        """Retorna la clase CSS para el badge de stock"""
        status = self.get_stock_status()
        return {
            'sin_stock': 'badge-danger',
            'stock_bajo': 'badge-warning',
            'stock_medio': 'badge-info',
            'stock_alto': 'badge-success'
        }.get(status, 'badge-secondary')
    
    def precio_en_rango_permitido(self):
        """Verifica si el precio está en el rango permitido"""
        return self.PRECIO_MINIMO <= self.precio <= self.PRECIO_MAXIMO
    
    def stock_en_rango_permitido(self):
        """Verifica si el stock está en el rango permitido"""
        return self.STOCK_MINIMO <= self.stock <= self.STOCK_MAXIMO
    
    @classmethod
    def get_productos_precio_alto(cls):
        """Retorna productos con precio cercano al límite (>$4000)"""
        return cls.objects.filter(precio__gte=4000, activo=True)
    
    @classmethod
    def get_productos_stock_alto(cls):
        """Retorna productos con stock alto (>50000)"""
        return cls.objects.filter(stock__gte=50000, activo=True)
    
    @classmethod
    def get_limites_validacion(cls):
        """Retorna los límites de validación para uso en formularios/templates"""
        return {
            'precio_minimo': cls.PRECIO_MINIMO,
            'precio_maximo': cls.PRECIO_MAXIMO,
            'stock_minimo': cls.STOCK_MINIMO,
            'stock_maximo': cls.STOCK_MAXIMO
        }
class Empleado(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Usuario')
    nombre = models.CharField(max_length=20, verbose_name= "Nombre")
    apellido = models.CharField(max_length=20, verbose_name='Apellido')
    nivel_acceso = models.ForeignKey(NivelAcceso, on_delete=models.PROTECT)
    fecha_contratacion = models.DateField(auto_now_add=True, verbose_name='Fecha de contratación')
    activo =  models.BooleanField(default=True, verbose_name='Activo')


    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    def get_comisiones_mes(self, mes, anio):
        """Calcular comisiones solo de ventas completadas"""
        from decimal import Decimal
        
        total = Decimal('0.00')
        # Obtener ventas del mes donde el empleado fue vendedor
        ventas = Ventas.objects.filter(
            empleado=self,
            factura__fecha_fac__month=mes,
            factura__fecha_fac__year=anio
        ).exclude(
            status__vent_cancelada=True
        )
        
        for venta in ventas:
            # Solo calcular comisión si la venta está completada
            completada = False
            if hasattr(venta, 'completada'):
                completada = venta.completada
            else:
                # Verificar manualmente si la venta está completada
                completada = not venta.credito or venta.monto_pagado >= venta.factura.total_fac
            
            if completada:
                # Buscar el porcentaje en la tabla de rangos de comisión
                total_factura = venta.factura.total_fac
                rango_comision = ConsultaComision.objects.filter(
                    rango_inferior__lte=total_factura,
                    rango_superior__gte=total_factura
                ).first()
                
                if rango_comision:
                    # Calcular comisión basada en el monto de la venta
                    comision = total_factura * rango_comision.porcentaje / Decimal('100.00')
                    total += comision
        
        return total
class ConsultaComision(models.Model):
    rango_inferior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Rango Inferior"
    )
    rango_superior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Rango Superior"
    )
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Porcentaje de Comisión"
    )

    class Meta:
        verbose_name = "Rango de Comisión"
        verbose_name_plural = "Rangos de Comisiones"
        ordering = ['rango_inferior']

    def __str__(self):
        return f"{self.porcentaje}% para ventas entre ${self.rango_inferior} y ${self.rango_superior}"
    
    def calcular_comision(self, monto_venta):
        """Calcula la comisión para un monto de venta"""
        if self.rango_inferior <= monto_venta <= self.rango_superior:
            return (monto_venta * self.porcentaje) / 100
        return 0
    
class Comision(models.Model):
    empleado = models.ForeignKey(
        'Empleado',
        on_delete=models.PROTECT,
        verbose_name="Empleado"
    )
    monto_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto de venta"
    )
    fecha_comision = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Comisión"
    )
    venta = models.OneToOneField(
        'Ventas',
        on_delete=models.PROTECT,
        verbose_name="Venta Asociada"
    )
    total_comision = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total de Comisión",
        editable=False  # No se puede editar manualmente
    )
    

    class Meta:
        verbose_name = "Comisión"
        verbose_name_plural = "Comisiones"
        ordering = ['-fecha_comision']  # Ordenar por fecha descendente (más reciente primero)

    def __str__(self):
        return f"Comisión de {self.empleado} - ${self.total_comision}"

    def save(self, *args, **kwargs):
        """
        Sobrescribimos el método save para calcular automáticamente 
        la comisión antes de guardar
        """
        if not self.total_comision:
        # Obtenemos el total de la factura en lugar del total_venta de la venta
            monto_venta = self.venta.factura.total_venta
            
            rango = ConsultaComision.objects.filter(
                rango_inferior__lte=monto_venta,
                rango_superior__gte=monto_venta
            ).first()
            
            if rango:
                self.total_comision = rango.calcular_comision(monto_venta)
            else:
                self.total_comision = 0

        super().save(*args, **kwargs)

    def get_mes_actual(self):
        """
        Obtiene el total de comisiones del mes actual para este empleado
        """
        mes_actual = self.fecha_comision.month
        año_actual = self.fecha_comision.year
        return Comision.objects.filter(
            empleado=self.empleado,
            fecha_comision__month=mes_actual,
            fecha_comision__year=año_actual
        ).aggregate(
            total=models.Sum('total_comision')
        )['total'] or 0
    
    
class Ventas(models.Model):
    empleado = models.ForeignKey(
        'Empleado',
        on_delete=models.PROTECT,
        verbose_name="Empleado"
    )
    factura = models.OneToOneField(
        'Factura',
        on_delete=models.PROTECT,
        verbose_name="Factura"
    )
    status = models.ForeignKey(
        'StatusVentas',
        on_delete=models.PROTECT,
        verbose_name="Estado de la Venta"
    )
    fecha_venta = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Venta"
    )
    credito = models.BooleanField(default=False, verbose_name="Venta a Crédito")
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monto Pagado")
    
    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha_venta']

    def __str__(self):
        return f"Venta {self.id} - {self.empleado}"

    def calcular_total(self):
        """Calcula el total de la venta basado en la factura"""
        return self.factura.total_venta if self.factura else 0

    @property
    def total_venta(self):
        """Propiedad para acceder fácilmente al total de la venta"""
        return self.calcular_total()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not hasattr(self, 'comision'):
            Comision.objects.create(
                empleado=self.empleado,
                venta=self,
                monto_venta = self.factura.total_venta
            )
    def cancelar_venta(self):
        """Cancela la venta y restaura el stock"""
        if not self.status.vent_cancelada:
            # Obtener el estado "Cancelada"
            estado_cancelado = StatusVentas.objects.get(vent_cancelada=True)
            
            # Restaurar stock
            detalles = self.factura.detallefactura_set.all()
            for detalle in detalles:
                detalle.producto.stock += detalle.cantidad
                detalle.producto.save(update_fields=['stock'])
            
            # Cambiar estado
            self.status = estado_cancelado
            self.save(update_fields=['status'])
            
            return True
        return False
    @property
    def saldo_pendiente(self):
        """Retorna el saldo pendiente por pagar"""
        return self.factura.total_fac - self.monto_pagado
    
    @property
    def completada(self):
        """Retorna True si la venta está completamente pagada"""
        return self.saldo_pendiente <= 0 or not self.credito
    
    def registrar_pago(self, monto):
        from decimal import Decimal
        """Registra un pago parcial"""
        if monto <= 0:
            return False
        
        # Convertir monto a Decimal para evitar error de tipo de datos
        if not isinstance(monto, Decimal):
            monto = Decimal(str(monto))
        
        self.monto_pagado += monto
        
        # Cambiar estado si se completó el pago
        if self.completada and self.credito:
            estado_completado = StatusVentas.objects.get(nombre="Completada")
            self.status = estado_completado
            
        self.save(update_fields=['monto_pagado', 'status'])
        
        # Crear registro de pago
        PagoVenta.objects.create(
            venta=self,
            monto=monto,
            fecha=timezone.now()
        )
        
        return True
class PagoVenta(models.Model):
    venta = models.ForeignKey(Ventas, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto Pagado")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Pago")
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Pago #{self.id} de Venta #{self.venta.id}"
class StatusVentas(models.Model):
    
    nombre = models.CharField(  # Añadimos un nombre descriptivo
        max_length=50,
        verbose_name="Nombre del Estado"
    )
    vent_cancelada = models.BooleanField(
        default=False,
        verbose_name="Venta Cancelada"
    )
    vent_espera = models.BooleanField(
        default=False,
        verbose_name="Venta en Espera"
    )
    
    class Meta:
        verbose_name = "Estado de Venta"
        verbose_name_plural = "Estados de Venta"
        
    def __str__(self):
        if self.vent_cancelada:
            return "Cancelada"
        elif self.vent_espera:
            return "En Espera"
        return "Completada"
    
    def get_estado(self):
        """Retorna el estado actual de la venta"""
        if self.vent_cancelada:
            return "CANCELADA"
        elif self.vent_espera:
            return "EN ESPERA"
        return "COMPLETADA"
    
class Factura(models.Model):
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('credito', 'Crédito'),
        ('otro', 'Otro')
    ]
    
    fecha_fac = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Facturación"
    )
    
    total_fac = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Total Factura",
        default=0
    )
    
    metodo_pag = models.CharField(  # Corregido: CharField con choices
        max_length=20,
        choices=METODO_PAGO_CHOICES,
        default='efectivo',
        verbose_name="Método de Pago"
    )
    
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.PROTECT,  # Protege contra eliminación
        verbose_name="Cliente",
        related_name='facturas'  # Permite cliente.facturas.all()
    )
    
    empleado = models.ForeignKey(
        'Empleado',
        on_delete=models.PROTECT,
        verbose_name="Empleado",
        related_name='facturas_generadas'
    )
    
    total_venta = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Total de Venta",
        default=0
    )

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-fecha_fac']  # Ordena por fecha descendente
    
    def __str__(self):
        return f"Factura #{self.id} - Cliente: {self.cliente.nombre}"
    
    def calcular_total(self):
        """
        Calcula el total de la factura basado en sus detalles
        """
        total = self.detallefactura_set.aggregate(
            total=models.Sum(models.F('cantidad') * models.F('producto__precio'))
        )['total'] or 0
        
        self.total_fac = total
        self.total_venta = total
        self.save()
        return total
    
    def get_detalles(self):
        """
        Retorna todos los detalles de la factura
        """
        return self.detallefactura_set.all()
    
    def agregar_detalle(self, producto, cantidad):
        """
        Agrega un nuevo detalle a la factura
        """
        from decimal import Decimal
        
        detalle = self.detallefactura_set.create(
            producto=producto,
            cantidad=cantidad,
            # Cambiar esto:
            # sub_total=Decimal(str(producto.precio_pro)) * Decimal(str(cantidad))
            
            # Por esto:
            sub_total=Decimal(str(producto.precio)) * Decimal(str(cantidad))
        )
        self.calcular_total()
        return detalle
    
class DetalleFactura(models.Model):
    factura = models.ForeignKey(
        'Factura',
        on_delete=models.PROTECT,
        verbose_name="Factura"
    )
    tipo_factura = models.ForeignKey(
        'TipoFactura',
        on_delete=models.PROTECT,
        verbose_name="Tipo de Factura"
    )
    producto = models.ForeignKey(
        'Producto',
        on_delete=models.PROTECT,
        verbose_name="Producto"
    )
    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad",
        validators=[MinValueValidator(1)]
    )
    sub_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Sub-Total",
        editable=False  # Se calcula automáticamente
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )

    class Meta:
        verbose_name = "Detalle de Factura"
        verbose_name_plural = "Detalles de Factura"
        ordering = ['-factura', 'producto']

    def __str__(self):
        return f"Detalle #{self.id} - Factura #{self.factura.id}"

    def save(self, *args, **kwargs):
        # Calcula el subtotal antes de guardar
        self.sub_total = self.calcular_subtotal()
        super().save(*args, **kwargs)
        # Actualiza el total de la factura
        self.factura.calcular_total()
    
    """ def save(self, *args, **kwargs):
        # Verificar si es un nuevo registro
        es_nuevo = self.pk is None
        
        # Si es nuevo, verificar stock antes de guardar
        if es_nuevo:
            if not self.validar_stock():
                raise ValueError(f"Stock insuficiente para {self.producto.nombre}. Disponible: {self.producto.stock}")
        
        # Calcula el subtotal antes de guardar
        self.sub_total = self.calcular_subtotal()
        
        # Guardar el detalle
        super().save(*args, **kwargs)
        
        # Actualizar stock si es un nuevo registro
        if es_nuevo:
            # Reducir el stock del producto
            self.producto.stock -= self.cantidad
            self.producto.save(update_fields=['stock'])
        
        # Actualiza el total de la factura
        self.factura.calcular_total() """

    def validar_stock(self):
        """Valida si hay suficiente stock"""
        return self.producto.stock >= self.cantidad

    def calcular_subtotal(self):
        """Calcula el subtotal del detalle"""
        return self.cantidad * self.producto.precio

    def validar_stock(self):
        """Valida si hay suficiente stock"""
        return self.producto.stock >= self.cantidad


class TipoFactura(models.Model):
    PLAZO_CHOICES = [
        (30, '30 días'),
        (60, '60 días'),
        (90, '90 días')
    ]

    credito_fac = models.BooleanField(
        default=False,
        verbose_name="Factura a Crédito"
    )
    contado_fac = models.BooleanField(
        default=True,
        verbose_name="Factura de Contado"
    )
    plazo_credito = models.IntegerField(
        choices=PLAZO_CHOICES,
        null=True,
        blank=True,
        verbose_name="Plazo de Crédito"
    )

    class Meta:
        verbose_name = "Tipo de Factura"
        verbose_name_plural = "Tipos de Factura"

    def __str__(self):
        if self.credito_fac:
            return f"Crédito - {self.get_plazo_credito_display()}"
        return "Contado"
    
class TablaConfig(models.Model):
    empleado = models.ForeignKey(
        'Empleado',
        on_delete=models.PROTECT,
        verbose_name="Empleado"
    )
    monto_fact = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto Factura"
    )
    porcent_comis = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Porcentaje Comisión"
    )
    fecha_config = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Configuración"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Configuración Activa"
    )

    class Meta:
        verbose_name = "Configuración"
        verbose_name_plural = "Configuraciones"
        ordering = ['-fecha_config']

    def __str__(self):
        return f"Config {self.empleado} - {self.porcent_comis}%"

    def aplicar_comision(self, monto_venta):
        """Calcula la comisión según la configuración"""
        if monto_venta >= self.monto_fact:
            return (monto_venta * self.porcent_comis) / 100
        return 0