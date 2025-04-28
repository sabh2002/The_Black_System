// Esperar a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    // Función para formatear números como moneda
    function formatCurrency(value) {
        return '$' + parseFloat(value).toFixed(2);
    }
    
    // Función para actualizar el precio cuando se selecciona un producto
    function actualizarPrecio(fila) {
        const select = fila.querySelector('.producto-select');
        const precioCell = fila.querySelector('.precio');
        const cantidadInput = fila.querySelector('.cantidad');
        const subtotalCell = fila.querySelector('.subtotal');
        
        if (select.selectedIndex > 0) {
            const option = select.options[select.selectedIndex];
            const precio = parseFloat(option.dataset.precio);
            const stock = parseInt(option.dataset.stock);
            
            // Actualizar celda de precio
            precioCell.textContent = formatCurrency(precio);
            
            // Limitar cantidad al stock disponible
            cantidadInput.max = stock;
            
            // Si la cantidad es mayor que el stock, ajustarla
            if (parseInt(cantidadInput.value) > stock) {
                cantidadInput.value = stock;
            }
            
            // Actualizar subtotal
            actualizarSubtotal(fila);
        } else {
            precioCell.textContent = '$0.00';
            subtotalCell.textContent = '$0.00';
        }
        
        // Actualizar el total de la venta
        calcularTotal();
    }
    
    // Función para actualizar el subtotal según cantidad y precio
    function actualizarSubtotal(fila) {
        const precioCell = fila.querySelector('.precio');
        const cantidadInput = fila.querySelector('.cantidad');
        const subtotalCell = fila.querySelector('.subtotal');
        
        // Extraer el precio (quitar el símbolo $ y convertir a número)
        const precio = parseFloat(precioCell.textContent.replace('$', ''));
        const cantidad = parseInt(cantidadInput.value);
        
        if (!isNaN(precio) && !isNaN(cantidad)) {
            const subtotal = precio * cantidad;
            subtotalCell.textContent = formatCurrency(subtotal);
        } else {
            subtotalCell.textContent = '$0.00';
        }
        
        // Actualizar total
        calcularTotal();
    }
    
    // Función para calcular el total de todos los productos
    function calcularTotal() {
        const subtotales = document.querySelectorAll('#tablaProductos .subtotal');
        let total = 0;
        
        subtotales.forEach(function(cell) {
            total += parseFloat(cell.textContent.replace('$', '')) || 0;
        });
        
        document.getElementById('total').textContent = formatCurrency(total);
    }
    
    // Función para agregar una nueva fila de producto
    function agregarFilaProducto() {
        const tbody = document.querySelector('#tablaProductos tbody');
        const primeraFila = document.querySelector('.fila-producto');
        const nuevaFila = primeraFila.cloneNode(true);
        
        // Resetear valores en la nueva fila
        nuevaFila.querySelector('.producto-select').selectedIndex = 0;
        nuevaFila.querySelector('.precio').textContent = '$0.00';
        nuevaFila.querySelector('.cantidad').value = 1;
        nuevaFila.querySelector('.subtotal').textContent = '$0.00';
        
        // Añadir event listeners a la nueva fila
        configurarEventListeners(nuevaFila);
        
        // Añadir nueva fila a la tabla
        tbody.appendChild(nuevaFila);
    }
    
    // Función para eliminar una fila
    function eliminarFila(event) {
        const boton = event.target.closest('.eliminar-fila');
        if (!boton) return;
        
        const filas = document.querySelectorAll('.fila-producto');
        
        // Solo eliminar si hay más de una fila
        if (filas.length > 1) {
            const fila = boton.closest('.fila-producto');
            fila.remove();
            calcularTotal();
        } else {
            alert('Debe haber al menos un producto en la venta.');
        }
    }
    
    // Función para configurar event listeners en una fila
    function configurarEventListeners(fila) {
        // Para select de producto
        const select = fila.querySelector('.producto-select');
        select.addEventListener('change', function() {
            actualizarPrecio(fila);
        });
        
        // Para input de cantidad
        const cantidad = fila.querySelector('.cantidad');
        cantidad.addEventListener('input', function() {
            // Asegurar que cantidad sea al menos 1
            if (parseInt(this.value) < 1 || isNaN(parseInt(this.value))) {
                this.value = 1;
            }
            
            // Actualizar subtotal
            actualizarSubtotal(fila);
        });
        
        // Para botón eliminar
        const btnEliminar = fila.querySelector('.eliminar-fila');
        btnEliminar.addEventListener('click', eliminarFila);
    }
    
    // Configurar event listeners iniciales
    document.querySelectorAll('.fila-producto').forEach(function(fila) {
        configurarEventListeners(fila);
    });
    
    // Evento para el botón "Agregar Producto"
    const btnAgregarProducto = document.getElementById('agregarProducto');
    if (btnAgregarProducto) {
        btnAgregarProducto.addEventListener('click', agregarFilaProducto);
    }
    
    // Sincronizar método de pago con tipo de venta
    const metodoPago = document.getElementById('metodoPago');
    const radioContado = document.getElementById('contado');
    const radioCredito = document.getElementById('credito');
    
    if (metodoPago && radioContado && radioCredito) {
        metodoPago.addEventListener('change', function() {
            if (this.value === 'credito') {
                radioCredito.checked = true;
            } else {
                radioContado.checked = true;
            }
        });
        
        // Sincronización inversa
        radioContado.addEventListener('change', function() {
            if (this.checked && metodoPago.value === 'credito') {
                metodoPago.value = 'efectivo';
            }
        });
        
        radioCredito.addEventListener('change', function() {
            if (this.checked) {
                metodoPago.value = 'credito';
            }
        });
    }
});