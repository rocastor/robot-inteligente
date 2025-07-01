
from fastapi import FastAPI, HTTPException
import requests
import tempfile
import os

app = FastAPI()

@app.post("/enviar-a-robot-ai")
async def enviar_a_robot_ai(data: dict):
    """
    Endpoint para enviar archivos automáticamente al Robot AI
    """
    try:
        # URL del Robot AI (configúrala según tu deployment)
        ROBOT_AI_URL = "https://tu-repl-name.replit.app"
        
        archivos_base64 = data.get('archivos', [])
        carpeta_original = data.get('carpeta_original', 'Automatico')
        
        if not archivos_base64:
            raise HTTPException(status_code=400, detail="No se enviaron archivos")
        
        # Crear archivos temporales
        archivos_temp = []
        files_for_request = []
        
        for archivo_data in archivos_base64:
            nombre = archivo_data.get('nombre', 'archivo.pdf')
            contenido_b64 = archivo_data.get('contenido', '')
            
            # Decodificar base64
            import base64
            contenido = base64.b64decode(contenido_b64)
            
            # Crear archivo temporal
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{nombre}")
            temp_file.write(contenido)
            temp_file.close()
            
            archivos_temp.append(temp_file.name)
            files_for_request.append(
                ('archivos', (nombre, open(temp_file.name, 'rb'), 'application/octet-stream'))
            )
        
        # Enviar al Robot AI
        url_procesar = f"{ROBOT_AI_URL}/procesar"
        
        response = requests.post(
            url_procesar,
            files=files_for_request,
            data={'carpeta_original': carpeta_original},
            timeout=300
        )
        
        # Cerrar archivos
        for _, file_tuple in files_for_request:
            file_tuple[1].close()
        
        # Limpiar archivos temporales
        for temp_path in archivos_temp:
            try:
                os.unlink(temp_path)
            except:
                pass
        
        if response.status_code == 200:
            resultado = response.json()
            
            # Generar enlaces de descarga
            base_url = ROBOT_AI_URL
            archivos_gen = resultado.get('archivos_generados', {})
            
            enlaces_descarga = {
                'json': f"{base_url}/descargar/{archivos_gen.get('json', '')}",
                'pdf': f"{base_url}/descargar/{archivos_gen.get('pdf', '')}",
                'excel': f"{base_url}/descargar/{archivos_gen.get('excel', '')}",
                'zip_completo': f"{base_url}/descargar-proceso-zip/{archivos_gen.get('carpeta_proceso', '')}"
            }
            
            return {
                "status": "success",
                "message": "Archivos procesados exitosamente",
                "resultado_robot_ai": resultado,
                "enlaces_descarga": enlaces_descarga,
                "costo_openai": resultado.get('costos_openai', {}),
                "resumen": resultado.get('resumen', {})
            }
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Error del Robot AI: {response.text}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando: {str(e)}")
