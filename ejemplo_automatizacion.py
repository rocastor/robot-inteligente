
import requests
import json
import os

def enviar_archivos_a_robot(archivos_paths, carpeta_original=None, url_robot="https://tu-repl-name.replit.app"):
    """
    Envía archivos automáticamente al Robot AI
    
    Args:
        archivos_paths: Lista de rutas de archivos
        carpeta_original: Nombre de la carpeta de origen (opcional)
        url_robot: URL del robot destino
    """
    
    url_procesar = f"{url_robot}/procesar"
    
    # Preparar archivos para envío
    files = []
    for archivo_path in archivos_paths:
        if os.path.exists(archivo_path):
            files.append(
                ('archivos', (
                    os.path.basename(archivo_path),
                    open(archivo_path, 'rb'),
                    'application/octet-stream'
                ))
            )
    
    # Datos adicionales
    data = {}
    if carpeta_original:
        data['carpeta_original'] = carpeta_original
    
    try:
        print(f"🚀 Enviando {len(files)} archivos al robot...")
        
        response = requests.post(
            url_procesar,
            files=files,
            data=data,
            timeout=300  # 5 minutos timeout
        )
        
        # Cerrar archivos
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code == 200:
            resultado = response.json()
            print(f"✅ Procesamiento exitoso!")
            print(f"📊 Archivos procesados: {resultado['resumen']['archivos_procesados_exitosamente']}")
            print(f"💰 Costo: ${resultado['costos_openai']['costo_total_usd']}")
            
            # Obtener información de archivos generados
            if 'archivos_generados' in resultado:
                archivos_gen = resultado['archivos_generados']
                print(f"📁 Proceso: {archivos_gen['carpeta_proceso']}")
                
                # URLs para descargar resultados
                base_download = f"{url_robot}/descargar"
                print(f"🔗 Descargar JSON: {base_download}/{archivos_gen['json']}")
                print(f"🔗 Descargar PDF: {base_download}/{archivos_gen['pdf']}")
                print(f"🔗 Descargar Excel: {base_download}/{archivos_gen['excel']}")
            
            return resultado
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error enviando archivos: {str(e)}")
        return None

# Ejemplo de uso
if __name__ == "__main__":
    # Lista de archivos a procesar
    archivos = [
        "/ruta/a/documento1.pdf",
        "/ruta/a/documento2.docx"
    ]
    
    # URL de tu robot (reemplaza con la URL real)
    url_robot = "https://tu-repl-name.replit.app"
    
    # Enviar archivos
    resultado = enviar_archivos_a_robot(
        archivos, 
        carpeta_original="Mi_Carpeta_Origen",
        url_robot=url_robot
    )
    
    if resultado:
        print("🎉 Proceso completado exitosamente!")
