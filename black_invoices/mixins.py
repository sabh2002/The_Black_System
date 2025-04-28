# En un nuevo archivo: black_invoices/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.shortcuts import redirect

class EmpleadoRolMixin(LoginRequiredMixin):
    """
    Mixin para verificar que el usuario tenga el rol requerido.
    
    Uso:
        class MiVista(EmpleadoRolMixin, View):
            roles_permitidos = ['Administrador', 'Supervisor']
    """
    roles_permitidos = ['Administrador']  # Roles permitidos por defecto
    
    def dispatch(self, request, *args, **kwargs):
        # Primero verificar si está autenticado
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Verificar si tiene empleado asociado
        if not hasattr(request.user, 'empleado'):
            messages.error(request, 'No tienes un perfil de empleado asociado.')
            return redirect('black_invoices:inicio')
        
        # Verificar el rol del empleado
        rol_empleado = request.user.empleado.nivel_acceso.nombre
        
        if rol_empleado not in self.roles_permitidos:
            messages.error(
                request, 
                f'No tienes permisos para acceder a esta sección. Se requiere: {", ".join(self.roles_permitidos)}.'
            )
            return redirect('black_invoices:inicio')
        
        return super().dispatch(request, *args, **kwargs)