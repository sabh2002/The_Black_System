// Script mejorado para actualización dinámica de precios
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM cargado, iniciando script");
    
    // Obtener datos de productos del contexto
    let productosMap = {};
    try {
        const productosData = JSON.parse(document.getElementById('productos-json').textContent);
        productosData.forEach(p => {
            productosMap[p.id] = p;
        });
        console.log("Datos de productos cargados:", productosMap);
    } catch (error) {
        console.error("Error al cargar datos de productos:", error);
    }
    
    // Configurar formset
    const formsetPrefix = document.querySelector('input[name$="-TOTAL_FORMS"]').name.split('-')[0];
    let formCount = parseInt(document.querySelector(`#id_${formsetPrefix}-TOTAL_FORMS`).value);
    
    // Función para actualizar una fila
    function updateRow(row) {
        // Obtener elementos
        const productoSelect = row.querySelector('select[id*="producto"]');
        const cantidadInput = row.querySelector('input[id*="cantidad"]');
        const precioCell = row.querySelector('.precio');
        const subtotalCell = row.querySelector('.subtotal');
        
        if (!productoSelect || !cantidadInput || !precioCell || !subtotalCell) {
            console.error("No se encontraron todos los elementos necesarios");
            return;
        }
        
        const productoId = productoSelect.value;
        const cantidad = parseInt(cantidadInput.value) || 0;
        
        if (productoId && productosMap[productoId]) {
            const producto = productosMap[productoId];
            
            // Actualizar precio
            precioCell.textContent = "$" + producto.precio.toFixed(2);
            
            // Calcular subtotal
            const subtotal = producto.precio * cantidad;
            subtotalCell.textContent = "$" + subtotal.toFixed(2);
            
            console.log(`Actualizado: Producto ${producto.nombre}, Precio ${producto.precio}, Cantidad ${cantidad}, Subtotal ${subtotal}`);
        } else {
            precioCell.textContent = "$0.00";
            subtotalCell.textContent = "$0.00";
        }
    }
    
    // Función para actualizar total
    function updateTotal() {
        const subtotalCells = document.querySelectorAll('.subtotal');
        let total = 0;
        
        subtotalCells.forEach(cell => {
            const value = parseFloat(cell.textContent.replace('$', '')) || 0;
            total += value;
        });
        
        const totalElement = document.getElementById('total-venta');
        if (totalElement) {
            totalElement.textContent = "$" + total.toFixed(2);
            console.log("Total actualizado:", total);
        }
    }
    
    // Función para configurar eventos en una fila
    function setupRowEvents(row) {
        const productoSelect = row.querySelector('select[id*="producto"]');
        const cantidadInput = row.querySelector('input[id*="cantidad"]');
        
        if (productoSelect) {
            productoSelect.addEventListener('change', function() {
                console.log("Cambio en select de producto:", this.value);
                updateRow(row);
                updateTotal();
            });
            
            // Trigger inicial si ya tiene un valor seleccionado
            if (productoSelect.value) {
                updateRow(row);
            }
        }
        
        if (cantidadInput) {
            cantidadInput.addEventListener('input', function() {
                console.log("Cambio en input de cantidad:", this.value);
                updateRow(row);
                updateTotal();
            });
        }
    }
    
    // Configurar eventos en filas existentes
    document.querySelectorAll('tr.detalle-form').forEach(row => {
        setupRowEvents(row);
    });
    
    // Configurar botón de agregar producto
    const btnAgregar = document.getElementById('agregar-producto');
    if (btnAgregar) {
        btnAgregar.addEventListener('click', function() {
            console.log("Agregando nueva fila de producto");
            
            // Clonar primera fila
            const firstRow = document.querySelector('tr.detalle-form');
            const newRow = firstRow.cloneNode(true);
            
            // Actualizar IDs y nombres
            newRow.querySelectorAll(':input').forEach(input => {
                const name = input.name;
                if (name) {
                    const newName = name.replace(
                        new RegExp(`${formsetPrefix}-(\\d+)-`), 
                        `${formsetPrefix}-${formCount}-`
                    );
                    input.name = newName;
                    input.id = input.id.replace(
                        new RegExp(`${formsetPrefix}-(\\d+)-`), 
                        `${formsetPrefix}-${formCount}-`
                    );
                    input.value = '';
                }
            });
            
            // Limpiar celdas de precio y subtotal
            newRow.querySelector('.precio').textContent = '$0.00';
            newRow.querySelector('.subtotal').textContent = '$0.00';
            
            // Agregar a la tabla
            document.querySelector('#detalles-table tbody').appendChild(newRow);
            
            // Actualizar conteo
            formCount++;
            document.querySelector(`#id_${formsetPrefix}-TOTAL_FORMS`).value = formCount;
            
            // Configurar eventos en la nueva fila
            setupRowEvents(newRow);
            updateTotal();
        });
    }
    
    // Configurar botones de eliminar fila
    document.querySelectorAll('.eliminar-fila').forEach(btn => {
        btn.addEventListener('click', function() {
            const rows = document.querySelectorAll('tr.detalle-form');
            if (rows.length > 1) {
                this.closest('tr').remove();
                formCount--;
                document.querySelector(`#id_${formsetPrefix}-TOTAL_FORMS`).value = formCount;
                updateTotal();
            } else {
                alert('Debe haber al menos un producto');
            }
        });
    });
    
    // Inicializar cálculos
    document.querySelectorAll('tr.detalle-form').forEach(updateRow);
    updateTotal();
});