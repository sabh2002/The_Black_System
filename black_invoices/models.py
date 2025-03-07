from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User


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

    nombre = models.CharField(max_length=20, verbose_name= "Nombre")
    apellido = models.CharField(max_length=20, verbose_name='Apellido')
    email = models.EmailField(max_length=254, unique=True)
    telefono = models.CharField(max_length=15, verbose_name = "Telefono")
    direccion = models.CharField(max_length=200, verbose_name = "Direccion")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['apellido','nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Producto(models.Model):

    nombre = models.CharField(max_length=20,
                               verbose_name= "Nombre",
                                 unique=True)
    
    descripcion = models.TextField(max_length=200,
                                    verbose_name='Descripcion',
                                    help_text="Describe las características del producto")
    
    precio = models.DecimalField(max_digits=10,
                                decimal_places = 2,
                                verbose_name = "Precio",
                                validators= [MinValueValidator(0.01)],
                                help_text="Precio en dólares/euros")
    
    
    stock = models.PositiveIntegerField(  # Añadimos control de inventario
        default=0,
        verbose_name="Stock disponible"
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
        verbose_name="Ultima modificacion"
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    
    def stock_available(self):
        return self.stock > 0
    
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
    
    def get_comisiones_mes(self, mes, año):
        
        return self.comision_set.filter(
            fecha_comision__month=mes,
            fecha_comision__year=año,
        ).aggregate(
            total=models.Sum('total_comision')
        )['total'] or 0

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