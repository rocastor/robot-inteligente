
// Ejemplo de cómo enviar archivos con nombre de carpeta desde JavaScript

async function enviarArchivosConCarpeta(archivos, nombreCarpeta) {
    const formData = new FormData();
    
    // Agregar archivos
    archivos.forEach(archivo => {
        formData.append('archivos', archivo);
    });
    
    // Agregar nombre de carpeta original
    if (nombreCarpeta) {
        formData.append('carpeta_original', nombreCarpeta);
    }
    
    try {
        const response = await fetch('/procesar', {
            method: 'POST',
            body: formData
        });
        
        const resultado = await response.json();
        console.log('Proceso completado:', resultado);
        
        return resultado;
    } catch (error) {
        console.error('Error:', error);
    }
}

// Ejemplo de uso:
// enviarArchivosConCarpeta(misArchivos, '413-MC-023-2025');
