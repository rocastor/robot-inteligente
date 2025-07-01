
import requests
import json
import os
import base64

def enviar_archivos_a_robot_ai(archivos_paths, carpeta_original=None):
    """
    Envía archivos automáticamente al Robot AI
    
    Args:
        archivos_paths: Lista de rutas de archivos
        carpeta_original: Nombre de la carpeta de origen (opcional)
    """
    
    # 🔗 REEMPLAZA CON TU URL REAL DE REPLIT
    ROBOT_AI_URL = "https://tu-repl-name.replit.app"
    
    url_procesar = f"{ROBOT_AI_URL}/procesar"
    
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
        print(f"🚀 Enviando {len(files)} archivos al Robot AI...")
        print(f"🔗 URL destino: {url_procesar}")
        
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
            
            # URLs para descargar resultados
            if 'archivos_generados' in resultado:
                archivos_gen = resultado['archivos_generados']
                base_download = f"{ROBOT_AI_URL}/descargar"
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
        "documento1.pdf",
        "documento2.docx"
    ]
    
    # Enviar archivos
    resultado = enviar_archivos_a_robot_ai(
        archivos, 
        carpeta_original="Mi_Carpeta_Test"
    )
    
    if resultado:
        print("🎉 Proceso completado exitosamente!")
    else:
        print("❌ Error en el procesamiento")
