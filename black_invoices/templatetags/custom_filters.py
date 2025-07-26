# black_invoices/templatetags/custom_filters.py
from django import template
from decimal import Decimal
from ..models import TasaCambio

register = template.Library()

@register.filter
def precio_bolivares(valor_usd):
    """
    Convierte un precio en USD a bolívares usando la tasa actual
    """
    try:
        if not valor_usd:
            return Decimal('0.00')
        
        # Convertir a Decimal si no lo es
        if not isinstance(valor_usd, Decimal):
            valor_usd = Decimal(str(valor_usd))
        
        # Obtener tasa actual
        tasa_actual = TasaCambio.get_tasa_actual()
        if tasa_actual:
            return valor_usd * tasa_actual.tasa_usd_ves
        
        return Decimal('0.00')
    except (ValueError, TypeError, AttributeError):
        return Decimal('0.00')

@register.filter
def tasa_cambio_actual(dummy=None):
    """
    Obtiene la tasa de cambio actual para usar en templates
    """
    try:
        tasa_actual = TasaCambio.get_tasa_actual()
        return tasa_actual.tasa_usd_ves if tasa_actual else 1
    except:
        return 1