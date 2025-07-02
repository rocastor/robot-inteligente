"""
The `/lista-procesos` endpoint is corrected to handle errors gracefully when listing local and Google Drive processes, ensuring that the endpoint returns a valid response even if some processes fail to load.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from concurrent.futures import ThreadPoolExecutor
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn
import os
import json
import re
import glob
import tempfile
import zipfile
import time
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Sistema de configuración robusto
from config import config_manager, get_openai_api_key, get_google_credentials, is_configured

# Lazy imports - Los módulos se cargarán solo cuando se necesiten
def lazy_import_document_processor():
    from modules.document_processor import process_file, chunk_text
    return process_file, chunk_text

def lazy_import_ai_analyzer():
    from modules.ai_analyzer import analyze_single_question, process_custom_questions, DEFAULT_QUESTIONS
    return analyze_single_question, process_custom_questions, DEFAULT_QUESTIONS

def lazy_import_file_generators():
    from modules.file_generators import guardar_json, guardar_pdf, guardar_excel
    return guardar_json, guardar_pdf, guardar_excel

def lazy_import_rocastor_manager():
    from modules.rocastor_manager import guardar_pdf_rocastor, cargar_pdfs_rocastor, generar_carpeta_rocastor
    return guardar_pdf_rocastor, cargar_pdfs_rocastor, generar_carpeta_rocastor

def lazy_import_analytics():
    from modules.analytics import S3CostAnalytics, FinancialAnalytics, crear_analytics_financiero
    return S3CostAnalytics, FinancialAnalytics, crear_analytics_financiero

# Google Drive es el almacenamiento principal - S3 removido completamente

# Configuración usando el sistema robusto
OPENAI_API_KEY = get_openai_api_key() or ""
GOOGLE_CREDENTIALS = get_google_credentials() or ""
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# Import Replit Object Storage para almacenamiento externo (lazy loading)
REPLIT_STORAGE_AVAILABLE = False
ReplitStorageClient = None

def init_replit_storage():
    global REPLIT_STORAGE_AVAILABLE, ReplitStorageClient
    try:
        from replit.object_storage import Client as ReplitStorageClient
        REPLIT_STORAGE_AVAILABLE = True
        print("✅ Replit Object Storage disponible")
        return True
    except ImportError:
        print("⚠️ Replit Object Storage no disponible - usando almacenamiento local")
        return False

# Inicializar solo cuando se necesite
init_replit_storage()

# Variables globales
google_drive_client = None

# Configuración de FastAPI
app = FastAPI(
    title="Robot AI - Analizador de Documentos API",
    description="API modular para análisis automático de documentos con IA",
    version="2.0.0"
)

# Añadir CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== ENDPOINTS PRINCIPALES =====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Página principal"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
        <body>
        <h1>🤖 Robot AI - API Modular v2.0</h1>
        <p>La API está funcionando correctamente</p>
        <p>Endpoints disponibles:</p>
        <ul>
            <li>GET /api - Información de la API</li>
            <li>GET /health - Estado de salud</li>
            <li>POST /procesar - Procesar documentos</li>
            <li>GET /dashboard - Dashboard principal</li>
            <li>GET /panel-filtros - Panel de gestión</li>
        </ul>
        </body>
        </html>
        """)

@app.get("/api")
async def api_info():
    """Información de la API"""
    return {
        "message": "Robot AI - Analizador de Documentos API Modular",
        "version": "2.0.0",
        "arquitectura": "modular",
        "modulos": [
            "document_processor - Extracción de texto",
            "ai_analyzer - Análisis con OpenAI", 
            "file_generators - Creación de archivos",
            "rocastor_manager - Gestión Rocastor",
            "analytics - Análisis financiero"
        ],
        "endpoints": {
            "POST /procesar": "Procesa documentos y los analiza con IA",
            "GET /health": "Verifica el estado de la API",
            "GET /lista-procesos": "Lista procesos completados",
            "GET /dashboard": "Dashboard principal",
            "GET /panel-filtros": "Panel de gestión"
        },
        "status": "funcionando"
    }

@app.get("/health")
async def health_check():
    """Estado de salud del sistema"""
    # Verificar conexión real a Google Drive
    google_drive_status = {
        "configured": bool(os.getenv('GOOGLE_CREDENTIALS')),
        "connected": False,
        "error": None,
        "status_message": "No configurado"
    }

    if google_drive_status["configured"]:
        try:
            from modules.google_drive_client import test_google_drive_connection
            result = test_google_drive_connection()
            google_drive_status["connected"] = result['success']
            google_drive_status["status_message"] = result['message']
            if not result['success']:
                google_drive_status["error"] = result['message']
        except Exception as e:
            google_drive_status["error"] = str(e)
            google_drive_status["status_message"] = f"Error: {str(e)}"
    else:
        google_drive_status["status_message"] = "Credenciales no configuradas"

    # Verificar estado real de cada módulo
    modulos_estado = {}

    # Test document_processor
    try:
        process_file, chunk_text = lazy_import_document_processor()
        modulos_estado["document_processor"] = "✅ ACTIVO"
    except Exception as e:
        modulos_estado["document_processor"] = f"❌ ERROR: {str(e)}"

    # Test ai_analyzer
    try:
        analyze_single_question, process_custom_questions, DEFAULT_QUESTIONS = lazy_import_ai_analyzer()
        modulos_estado["ai_analyzer"] = "✅ ACTIVO"
    except Exception as e:
        modulos_estado["ai_analyzer"] = f"❌ ERROR: {str(e)}"

    # Test file_generators
    try:
        guardar_json, guardar_pdf, guardar_excel = lazy_import_file_generators()
        modulos_estado["file_generators"] = "✅ ACTIVO"
    except Exception as e:
        modulos_estado["file_generators"] = f"❌ ERROR: {str(e)}"

    # Test rocastor_manager
    try:
        from modules.rocastor_manager import cargar_pdfs_rocastor
        modulos_estado["rocastor_manager"] = "✅ ACTIVO"
    except Exception as e:
        modulos_estado["rocastor_manager"] = f"❌ ERROR: {str(e)}"

    # Test analytics
    try:
        S3CostAnalytics, FinancialAnalytics, crear_analytics_financiero = lazy_import_analytics()
        modulos_estado["analytics"] = "✅ ACTIVO"
    except Exception as e:
        modulos_estado["analytics"] = f"❌ ERROR: {str(e)}"

    # Google Drive ya verificado arriba
    modulos_estado["google_drive_client"] = "✅ ACTIVO" if google_drive_status["connected"] else "⚠️ NO CONECTADO"

    # Estado de configuración del sistema robusto
    config_status = config_manager.get_configuration_status()
    
    return {
        "status": "ok",
        "version": "2.0.0",
        "arquitectura": "modular",
        "openai_configured": bool(OPENAI_API_KEY),
        "google_drive_configured": google_drive_status["configured"],
        "google_drive_connected": google_drive_status["connected"],
        "google_drive_status": google_drive_status,
        "almacenamiento_principal": "GOOGLE_DRIVE",
        "almacenamiento_secundario": "LOCAL_BACKUP",
        "s3_status": "DISABLED - Usando solo Google Drive",
        "timestamp": datetime.now().isoformat(),
        "modulos_cargados": list(modulos_estado.keys()),
        "modulos_estado": modulos_estado,
        "modulos_activos": len([m for m in modulos_estado.values() if "✅ ACTIVO" in m]),
        "modulos_total": len(modulos_estado),
        "configuracion_robusta": config_status,
        "portable": config_status["fully_configured"],
        "fuentes_configuracion": [
            "Variables de entorno",
            "Archivo config.json",
            "Archivos JSON individuales",
            "Replit Secrets (si aplica)"
        ]
    }

@app.get("/drive-links")
async def get_drive_links():
    """Obtiene todos los links directos de Google Drive"""
    try:
        print("🔗 Solicitando links de Google Drive...")

        from modules.google_drive_client import get_drive_client

        drive_client = get_drive_client()
        if not drive_client:
            raise HTTPException(status_code=500, detail="Google Drive no disponible")

        all_links = []

        # Obtener archivos de carpeta principal
        main_files = drive_client.list_files()
        for file_info in main_files:
            all_links.append({
                'name': file_info['name'],
                'id': file_info['id'],
                'size': int(file_info.get('size', 0)),
                'modified': file_info.get('modifiedTime', ''),
                'web_view_link': file_info.get('webViewLink', ''),
                'location': 'Carpeta Principal'
            })

        # Buscar en subcarpetas
        folders_query = f"'{drive_client.folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
        folders_result = drive_client.service.files().list(q=folders_query).execute()
        folders = folders_result.get('files', [])

        for folder in folders:
            folder_files = drive_client.list_files(folder['id'])
            for file_info in folder_files:
                all_links.append({
                    'name': file_info['name'],
                    'id': file_info['id'],
                    'size': int(file_info.get('size', 0)),
                    'modified': file_info.get('modifiedTime', ''),
                    'web_view_link': file_info.get('webViewLink', ''),
                    'location': f"Carpeta: {folder['name']}"
                })

            # Subcarpetas
            subfolders_query = f"'{folder['id']}' in parents and mimeType='application/vnd.google-apps.folder'"
            subfolders_result = drive_client.service.files().list(q=subfolders_query).execute()
            subfolders = subfolders_result.get('files', [])

            for subfolder in subfolders:
                subfolder_files = drive_client.list_files(subfolder['id'])
                for file_info in subfolder_files:
                    all_links.append({
                        'name': file_info['name'],
                        'id': file_info['id'],
                        'size': int(file_info.get('size', 0)),
                        'modified': file_info.get('modifiedTime', ''),
                        'web_view_link': file_info.get('webViewLink', ''),
                        'location': f"Carpeta: {folder['name']} > {subfolder['name']}"
                    })

        return {
            "success": True,
            "total_files": len(all_links),
            "drive_folder_id": drive_client.folder_id,
            "main_folder_link": f"https://drive.google.com/drive/folders/{drive_client.folder_id}",
            "files": all_links
        }

    except Exception as e:
        print(f"❌ Error obteniendo links: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo links: {str(e)}")

@app.get("/obtener-enlace-proceso/{nombre_proceso}")
async def obtener_enlace_proceso(nombre_proceso: str):
    """Obtiene el enlace específico de Google Drive para un proceso"""
    try:
        print(f"🔍 Buscando enlace de Drive para proceso: {nombre_proceso}")
        
        from modules.google_drive_client import get_drive_client
        drive_client = get_drive_client()
        
        if not drive_client:
            return {
                "success": False,
                "error": "Google Drive no disponible",
                "drive_link": "https://drive.google.com/drive/folders/1EfI2gKDlYiMmsi7dTGFsyHdtqhx9FLGi"
            }
        
        try:
            # Buscar en Drive empresarial primero
            empresa_folder_id = "1EfI2gKDlYiMmsi7dTGFsyHdtqhx9FLGi"
            
            # Buscar carpeta específica del proceso en Drive empresarial
            query = f"name='{nombre_proceso}' and mimeType='application/vnd.google-apps.folder' and '{empresa_folder_id}' in parents"
            results = drive_client.service.files().list(q=query).execute()
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
                drive_link = f"https://drive.google.com/drive/folders/{folder_id}"
                print(f"✅ Enlace específico encontrado: {drive_link}")
                
                return {
                    "success": True,
                    "drive_link": drive_link,
                    "folder_id": folder_id,
                    "proceso_nombre": nombre_proceso,
                    "ubicacion": "Drive Empresarial"
                }
            
            # Si no está en Drive empresarial, buscar en carpeta principal
            query = f"name='{nombre_proceso}' and mimeType='application/vnd.google-apps.folder' and '{drive_client.folder_id}' in parents"
            results = drive_client.service.files().list(q=query).execute()
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
                drive_link = f"https://drive.google.com/drive/folders/{folder_id}"
                print(f"✅ Enlace en carpeta principal: {drive_link}")
                
                return {
                    "success": True,
                    "drive_link": drive_link,
                    "folder_id": folder_id,
                    "proceso_nombre": nombre_proceso,
                    "ubicacion": "Drive Principal"
                }
            
            # Si no se encuentra, devolver enlace base de Drive empresarial
            print(f"⚠️ Proceso no encontrado, usando enlace base")
            return {
                "success": True,
                "drive_link": f"https://drive.google.com/drive/folders/{empresa_folder_id}",
                "folder_id": empresa_folder_id,
                "proceso_nombre": nombre_proceso,
                "ubicacion": "Drive Empresarial Base"
            }
            
        except Exception as e:
            print(f"❌ Error buscando en Drive: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "drive_link": "https://drive.google.com/drive/folders/1EfI2gKDlYiMmsi7dTGFsyHdtqhx9FLGi"
            }
        
    except Exception as e:
        print(f"❌ Error general obteniendo enlace: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "drive_link": "https://drive.google.com/drive/folders/1EfI2gKDlYiMmsi7dTGFsyHdtqhx9FLGi"
        }

@app.get("/drive-files")
async def get_drive_files():
    """Endpoint para el dashboard - información de archivos en Google Drive"""
    try:
        print("📊 Obteniendo información de Google Drive para dashboard...")

        from modules.google_drive_client import get_drive_client

        drive_client = get_drive_client()
        if not drive_client:
            return {
                "success": False,
                "total_files": 0,
                "storage_used_mb": 0,
                "storage_available_mb": 0,
                "recent_files": [],
                "quota_info": {},
                "error": "Google Drive no configurado"
            }

        # Obtener todos los archivos de forma optimizada
        all_files = []

        try:
            # Archivos principales
            main_files = drive_client.list_files()
            all_files.extend(main_files)
            print(f"   📁 Archivos principales: {len(main_files)}")

            # Buscar en subcarpetas (máximo 10 para evitar timeout)
            folders_query = f"'{drive_client.folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
            folders_result = drive_client.service.files().list(
                q=folders_query, 
                pageSize=10,
                fields="files(id,name)"
            ).execute()
            folders = folders_result.get('files', [])

            for folder in folders[:5]:  # Limitar a 5 carpetas para velocidad
                try:
                    folder_files = drive_client.list_files(folder['id'])
                    all_files.extend(folder_files)
                    print(f"   📂 Carpeta {folder['name']}: {len(folder_files)} archivos")
                except Exception as e:
                    print(f"   ⚠️ Error en carpeta {folder.get('name', 'Unknown')}: {str(e)}")
                    continue

        except Exception as e:
            print(f"   ⚠️ Error listando archivos: {str(e)}")

        # Calcular estadísticas
        total_size = 0
        files_with_size = 0

        for f in all_files:
            if f.get('size'):
                try:
                    size = int(f.get('size', 0))
                    total_size += size
                    files_with_size += 1
                except:
                    pass

        # Obtener información de cuota
        quota_info = {}
        try:
            quota_info = drive_client.get_storage_quota() or {}
        except Exception as e:
            print(f"   ⚠️ Error obteniendo cuota: {str(e)}")

        # Archivos recientes (últimos 5)
        recent_files = []
        try:
            files_with_time = [f for f in all_files if f.get('modifiedTime')]
            recent_files = sorted(
                files_with_time,
                key=lambda x: x.get('modifiedTime', ''),
                reverse=True
            )[:5]
        except Exception as e:
            print(f"   ⚠️ Error ordenando archivos recientes: {str(e)}")

        storage_mb = round(total_size / 1024 / 1024, 2)
        available_gb = quota_info.get('available_gb', 0)
        available_mb = round(available_gb * 1024, 2) if available_gb else 0

        print(f"📊 Google Drive: {len(all_files)} archivos, {storage_mb} MB usados")

        return {
            "success": True,
            "total_files": len(all_files),
            "storage_used_mb": storage_mb,
            "storage_available_mb": available_mb,
            "files_with_size": files_with_size,
            "recent_files": [
                {
                    "name": f.get('name', 'Sin nombre'),
                    "size": int(f.get('size', 0)) if f.get('size') else 0,
                    "modified": f.get('modifiedTime', ''),
                    "web_view_link": f.get('webViewLink', '')
                }
                for f in recent_files
            ],
            "quota_info": quota_info,
            "drive_folder_link": f"https://drive.google.com/drive/folders/{drive_client.folder_id}",
            "connection_status": "connected"
        }

    except Exception as e:
        print(f"❌ Error obteniendo archivos de Google Drive: {str(e)}")
        return {
            "success": False,
            "total_files": 0,
            "storage_used_mb": 0,
            "storage_available_mb": 0,
            "recent_files": [],
            "quota_info": {},
            "error": str(e),
            "connection_status": "error"
        }

@app.post("/procesar")
async def procesar_documentos(
    archivos: List[UploadFile] = File(...),
    preguntas_personalizadas: str = None,
    carpeta_original: str = None
):
    """Endpoint principal para procesar documentos"""

    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="API Key de OpenAI no configurada en el servidor"
        )

    if not archivos:
        raise HTTPException(
            status_code=400, 
            detail="No se enviaron archivos para procesar"
        )

    try:
        print(f"\n🚀 ===== PROCESAMIENTO MODULAR INICIADO =====")
        print(f"📊 Archivos recibidos: {len(archivos)}")

        # Lazy loading - Cargar módulos solo cuando se necesiten
        _, process_custom_questions, _ = lazy_import_ai_analyzer()
        process_file, chunk_text = lazy_import_document_processor()

        # Procesar preguntas personalizadas
        preguntas_finales = process_custom_questions(preguntas_personalizadas)
        print(f"❓ Preguntas a analizar: {len(preguntas_finales)}")

        # FASE 1: Extraer texto de archivos
        print(f"\n📁 ===== FASE 1: EXTRACCIÓN DE TEXTO =====")
        texto_completo = ""
        archivos_procesados = []
        errores = []

        for i, archivo in enumerate(archivos, 1):
            print(f"\n📄 [{i}/{len(archivos)}] Procesando: {archivo.filename}")
            print(f"   📋 Tipo de archivo: {archivo.content_type}")

            try:
                contenido = await archivo.read()
                print(f"   💾 Tamaño: {len(contenido)/1024:.1f} KB ({len(contenido):,} bytes)")

                # FORZAR uso de OCR y Vision AI para documentos críticos
                if not OPENAI_API_KEY:
                    print(f"   ⚠️ OPENAI_API_KEY no configurada - solo extracción básica disponible")
                else:
                    print(f"   🤖 Vision AI habilitado para máxima extracción")

                texto_extraido = process_file(
                    contenido, 
                    archivo.content_type, 
                    archivo.filename, 
                    OPENAI_API_KEY
                )

                print(f"   📊 Texto extraído: {len(texto_extraido) if texto_extraido else 0:,} caracteres")

                if texto_extraido and len(texto_extraido.strip()) > 10:
                    print(f"   ✅ ÉXITO - Texto válido extraído: {len(texto_extraido):,} caracteres")
                    texto_completo += f"\n\n=== DOCUMENTO: {archivo.filename} ===\n\n{texto_extraido}\n\n"
                    archivos_procesados.append({
                        "nombre": archivo.filename,
                        "tipo": archivo.content_type,
                        "tamaño": len(contenido),
                        "caracteres_extraidos": len(texto_extraido),
                        "procesado": True,
                        "metodo_extraccion": "OCR+Vision AI" if OPENAI_API_KEY else "Básico"
                    })
                else:
                    error_msg = f"❌ FALLO: No se extrajo texto válido de {archivo.filename}"
                    errores.append(error_msg)
                    print(f"   {error_msg}")
                    print(f"   🔍 Verificar: archivo corrupto, protegido o formato no soportado")
                    archivos_procesados.append({
                        "nombre": archivo.filename,
                        "tipo": archivo.content_type,
                        "tamaño": len(contenido),
                        "caracteres_extraidos": 0,
                        "procesado": False,
                        "error": "Sin texto extraído"
                    })

            except Exception as e:
                error_msg = f"💥 ERROR CRÍTICO procesando {archivo.filename}: {str(e)}"
                errores.append(error_msg)
                print(f"   {error_msg}")
                archivos_procesados.append({
                    "nombre": archivo.filename,
                    "tipo": archivo.content_type if hasattr(archivo, 'content_type') else "desconocido",
                    "tamaño": 0,
                    "caracteres_extraidos": 0,
                    "procesado": False,
                    "error": str(e)
                })

        archivos_exitosos = [a for a in archivos_procesados if a["procesado"]]
        print(f"\n📊 ===== RESUMEN EXTRACCIÓN =====")
        print(f"✅ Archivos exitosos: {len(archivos_exitosos)}/{len(archivos)}")
        print(f"📝 Caracteres totales: {len(texto_completo):,}")

        if not texto_completo.strip():
            raise HTTPException(
                status_code=400,
                detail="No se pudo extraer texto de ningún archivo"
            )

        # FASE 2: Fragmentar texto
        print(f"\n🔪 ===== FASE 2: FRAGMENTACIÓN =====")
        fragmentos = chunk_text(texto_completo, max_words=3000)
        print(f"📋 Fragmentos creados: {len(fragmentos)}")

        # FASE 3: Análisis con IA - PARALELO OPTIMIZADO
        print(f"\n🚀 ===== FASE 3: ANÁLISIS PARALELO CON IA =====")

        # Importar función paralela
        from modules.ai_analyzer import analyze_questions_parallel

        # Ejecutar análisis paralelo
        print(f"⚡ Procesando {len(preguntas_finales)} preguntas en paralelo...")
        inicio_analisis = datetime.now()

        # Usar asyncio para el análisis paralelo
        import asyncio
        resultados_paralelos = await analyze_questions_parallel(fragmentos, preguntas_finales, OPENAI_API_KEY)

        fin_analisis = datetime.now()
        tiempo_analisis = (fin_analisis - inicio_analisis).total_seconds()
        print(f"⏱️ Análisis completado en {tiempo_analisis:.1f} segundos")

        # Procesar resultados
        resultados = []
        costo_total_proceso = 0.0
        tokens_totales_proceso = 0

        for i, (respuesta, metricas) in enumerate(resultados_paralelos, 1):
            pregunta = preguntas_finales[i-1]
            informacion_encontrada = respuesta != "No se encontró información específica para esta pregunta"

            costo_total_proceso += metricas.get("costo_estimado", 0.0)
            tokens_totales_proceso += metricas.get("tokens_usados", 0)

            if informacion_encontrada:
                print(f"   ✅ [{i}] RESPUESTA: {respuesta[:80]}...")
            else:
                print(f"   ❌ [{i}] Sin información")

            resultados.append({
                "pregunta_numero": i,
                "pregunta": pregunta,
                "respuesta": respuesta,
                "informacion_encontrada": informacion_encontrada,
                "metricas_openai": metricas
            })

        print(f"\n📊 ===== RESUMEN ANÁLISIS =====")
        respuestas_con_info = [r for r in resultados if r["informacion_encontrada"]]
        print(f"✅ Respuestas encontradas: {len(respuestas_con_info)}")
        print(f"💰 Costo total: ${costo_total_proceso:.4f}")
        print(f"🔢 Tokens totales: {tokens_totales_proceso:,}")

        # FASE 4: Generar metadatos y estructura
        print(f"\n🔧 ===== FASE 4: GENERACIÓN DE METADATOS =====")

        # Detectar carpeta original
        carpeta_original_detectada = detectar_carpeta_original(archivos) if not carpeta_original else carpeta_original

        # Crear identificador único del proceso
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivos_nombres = "_".join([
            archivo.filename.replace('.pdf', '').replace('.docx', '').replace('.txt', '')
            .replace('.jpg', '').replace('.png', '').replace('.jpeg', '')
            .replace(' ', '-').replace('(', '').replace(')', '')
            for archivo in archivos[:3]
        ])
        archivos_nombres = re.sub(r'[^\w\-_]', '', archivos_nombres)[:40]
        nombre_proceso = f"proceso_{archivos_nombres}_{timestamp_str}"

        print(f"📁 Proceso: {nombre_proceso}")
        print(f"📂 Carpeta original: {carpeta_original_detectada}")

        # FASE 5: Validación y cálculos financieros
        print(f"\n💰 ===== FASE 5: VALIDACIÓN Y CÁLCULOS FINANCIEROS =====")
        
        # Extraer valores financieros del análisis
        valores_detectados = []
        for resultado in resultados:
            if "valor" in resultado["pregunta"].lower() or "presupuesto" in resultado["pregunta"].lower():
                if resultado["informacion_encontrada"]:
                    valores_detectados.append(resultado["respuesta"])
                    print(f"   💵 Valor detectado: {resultado['respuesta']}")
        
        # Validar calidad de extracción
        calidad_extraccion = "ALTA"
        if len(archivos_exitosos) < len(archivos):
            calidad_extraccion = "MEDIA"
        if len(texto_completo) < 1000:
            calidad_extraccion = "BAJA"
            
        print(f"   📊 Calidad de extracción: {calidad_extraccion}")
        print(f"   💰 Valores financieros detectados: {len(valores_detectados)}")
        
        # Construir respuesta final con validaciones
        respuesta_final = {
            "estado": "exitoso" if len(archivos_exitosos) > 0 else "parcial",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "arquitectura": "modular",
            "metadatos_proceso": {
                "id_unico_proceso": nombre_proceso,
                "carpeta_original_detectada": carpeta_original_detectada,
                "timestamp_creacion": timestamp_str,
                "archivos_originales": [archivo.filename for archivo in archivos],
                "hash_contenido": hash(texto_completo[:1000]) if texto_completo else None,
                "calidad_extraccion": calidad_extraccion,
                "vision_ai_usado": bool(OPENAI_API_KEY),
                "metodo_procesamiento": "Vision AI + OCR" if OPENAI_API_KEY else "Básico"
            },
            "resumen": {
                "archivos_recibidos": len(archivos),
                "archivos_procesados_exitosamente": len(archivos_exitosos),
                "caracteres_totales_extraidos": len(texto_completo),
                "fragmentos_de_texto": len(fragmentos),
                "preguntas_analizadas": len(resultados),
                "respuestas_con_informacion": len(respuestas_con_info),
                "tasa_exito_procesamiento": round((len(archivos_exitosos) / len(archivos)) * 100, 1) if len(archivos) > 0 else 0
            },
            "costos_openai": {
                "costo_total_usd": round(costo_total_proceso, 4),
                "tokens_totales_usados": tokens_totales_proceso,
                "modelo_utilizado": "gpt-4o-mini",
                "costo_promedio_por_pregunta": round(costo_total_proceso / len(resultados) if len(resultados) > 0 else 0, 4),
                "costo_por_archivo_procesado": round(costo_total_proceso / len(archivos_exitosos) if len(archivos_exitosos) > 0 else 0, 4)
            },
            "datos_financieros": {
                "valores_detectados": valores_detectados,
                "cantidad_valores": len(valores_detectados),
                "presupuesto_principal": valores_detectados[0] if valores_detectados else "No detectado"
            },
            "validacion_calidad": {
                "estado_extraccion": calidad_extraccion,
                "archivos_fallidos": len(archivos) - len(archivos_exitosos),
                "errores_criticos": len(errores),
                "requiere_revision": calidad_extraccion == "BAJA" or len(errores) > 0
            },
            "archivos": archivos_procesados,
            "errores": errores,
            "analisis": resultados,
            "texto_completo_extraido": texto_completo if len(texto_completo) < 50000 else f"{texto_completo[:50000]}... [TRUNCADO - TOTAL: {len(texto_completo)} caracteres]"
        }

        # FASE 6: Guardar archivos (Google Drive como almacenamiento principal)
        print(f"\n☁️ ===== FASE 6: GUARDADO EN GOOGLE DRIVE =====")

        # Verificar disponibilidad de Google Drive
        google_drive_available = bool(os.getenv('GOOGLE_CREDENTIALS'))

        if not google_drive_available:
            print("⚠️ Google Drive no configurado - configurar credenciales para almacenamiento")
            raise HTTPException(status_code=500, detail="Google Drive no configurado. Configura GOOGLE_CREDENTIALS para continuar.")

        print("☁️ Usando Google Drive como almacenamiento principal")

        # Obtener cliente de Google Drive
        from modules.google_drive_client import get_drive_client
        drive_client = get_drive_client()

        if not drive_client:
            print("❌ No se pudo obtener cliente de Google Drive")
            raise HTTPException(status_code=500, detail="Error inicializando Google Drive")

        # Generar archivos directamente en Google Drive usando el cliente
        archivos_generados_lista = []
        drive_info = {}

        try:
            print(f"📁 Creando carpeta para proceso: {nombre_proceso}")

            # Crear carpeta específica para este proceso
            process_folder_id = drive_client.create_or_get_folder(
                nombre_proceso, 
                drive_client.folder_id
            )

            if not process_folder_id:
                raise Exception("No se pudo crear carpeta del proceso")

            # 1. Guardar JSON directamente en Google Drive
            print(f"💾 Subiendo JSON a Google Drive...")
            json_content = json.dumps(respuesta_final, ensure_ascii=False, indent=2)
            json_filename = f"analisis_completo_{timestamp_str}.json"

            json_result = drive_client.upload_from_content(
                json_content,
                json_filename,
                process_folder_id,
                'application/json'
            )

            if json_result:
                archivos_generados_lista.append("JSON")
                drive_info['json_file'] = json_result
                print(f"✅ JSON subido: {json_result.get('web_view_link')}")
            else:
                print(f"❌ Error subiendo JSON")

            # FASE 6.1: COPIA AUTOMÁTICA A DRIVE EMPRESARIAL (INCLUYENDO ARCHIVOS ORIGINALES)
            print(f"\n🏢 ===== COPIA A DRIVE EMPRESARIAL =====")
            try:
                # Copiar también a la carpeta empresarial específica
                empresa_folder_id = "1EfI2gKDlYiMmsi7dTGFsyHdtqhx9FLGi"
                
                # Crear subcarpeta en drive empresarial con el nombre del proceso
                empresa_process_folder_id = drive_client.create_or_get_folder(
                    nombre_proceso,
                    empresa_folder_id
                )
                
                if empresa_process_folder_id:
                    # 1. Copiar JSON a drive empresarial
                    empresa_json_result = drive_client.upload_from_content(
                        json_content,
                        json_filename,
                        empresa_process_folder_id,
                        'application/json'
                    )
                    
                    if empresa_json_result:
                        print(f"✅ JSON copiado a Drive empresarial: {empresa_json_result.get('web_view_link')}")
                        drive_info['empresa_json_file'] = empresa_json_result
                        drive_info['empresa_folder_id'] = empresa_process_folder_id
                    
                    # 2. SUBIR ARCHIVOS ORIGINALES PDFs A DRIVE EMPRESARIAL
                    print(f"📁 Subiendo archivos originales a Drive empresarial...")
                    archivos_originales_subidos = []
                    
                    for i, archivo in enumerate(archivos, 1):
                        try:
                            print(f"📄 [{i}/{len(archivos)}] Subiendo original: {archivo.filename}")
                            
                            # Obtener contenido del archivo original
                            await archivo.seek(0)  # Resetear posición del archivo
                            contenido_original = await archivo.read()
                            
                            # Subir archivo original a Drive empresarial
                            original_result = drive_client.upload_from_content(
                                contenido_original,
                                archivo.filename,
                                empresa_process_folder_id,
                                archivo.content_type
                            )
                            
                            if original_result:
                                archivos_originales_subidos.append({
                                    'nombre': archivo.filename,
                                    'tipo': archivo.content_type,
                                    'drive_id': original_result['id'],
                                    'drive_link': original_result['web_view_link'],
                                    'tamaño': len(contenido_original)
                                })
                                print(f"   ✅ Original subido: {archivo.filename}")
                            else:
                                print(f"   ❌ Error subiendo: {archivo.filename}")
                                
                        except Exception as archivo_error:
                            print(f"   ❌ Error con {archivo.filename}: {str(archivo_error)}")
                            continue
                    
                    drive_info['archivos_originales_subidos'] = archivos_originales_subidos
                    print(f"✅ Archivos originales subidos: {len(archivos_originales_subidos)}/{len(archivos)}")
                    
                else:
                    print(f"⚠️ No se pudo crear carpeta en Drive empresarial")
                    
            except Exception as empresa_error:
                print(f"⚠️ Error copiando a Drive empresarial: {str(empresa_error)}")
                # No detener el proceso por este error

        except Exception as e:
            print(f"❌ Error guardando en Google Drive: {str(e)}")
            # Continuar con guardado local como fallback
            print(f"⚠️ Continuando con guardado local como respaldo...")

        # Intentar guardar archivos adicionales usando módulos
        try:
            guardar_json, guardar_pdf, guardar_excel = lazy_import_file_generators()

            # Guardar PDF en Google Drive
            pdf_result = guardar_pdf(respuesta_final, f"analisis_completo_reporte_{timestamp_str}")
            if pdf_result:
                archivos_generados_lista.append("PDF")
                print(f"✅ PDF guardado en Google Drive")

            # Guardar Excel en Google Drive  
            excel_result = guardar_excel(respuesta_final, f"analisis_completo_tablas_{timestamp_str}")
            if excel_result:
                archivos_generados_lista.append("Excel")
                print(f"✅ Excel guardado en Google Drive")

        except Exception as e:
            print(f"❌ Error módulos adicionales: {str(e)}")

        # Información de Google Drive
        drive_info.update({
            'folder_id': process_folder_id if 'process_folder_id' in locals() else drive_client.folder_id,
            'web_view_link': drive_info.get('json_file', {}).get('web_view_link', ''),
            'carpeta_completa': f"https://drive.google.com/drive/folders/{process_folder_id if 'process_folder_id' in locals() else drive_client.folder_id}"
        })

        archivos_generados = {
            "carpeta_proceso": nombre_proceso,
            "almacenamiento": "GOOGLE_DRIVE",
            "carpeta_original": carpeta_original_detectada,
            "archivos_generados": archivos_generados_lista,
            "google_drive_folder_id": drive_info.get('folder_id'),
            "google_drive_links": {
                "json": drive_info.get('web_view_link'),
                "carpeta_completa": drive_info.get('carpeta_completa')
            },
            "drive_empresarial": {
                "habilitado": drive_info.get('empresa_folder_id') is not None,
                "folder_id": drive_info.get('empresa_folder_id'),
                "json_link": drive_info.get('empresa_json_file', {}).get('web_view_link', ''),
                "carpeta_completa": f"https://drive.google.com/drive/folders/{drive_info.get('empresa_folder_id', '')}" if drive_info.get('empresa_folder_id') else "",
                "carpeta_empresarial_base": "https://drive.google.com/drive/folders/1EfI2gKDlYiMmsi7dTGFsyHdtqhx9FLGi",
                "archivos_originales": drive_info.get('archivos_originales_subidos', []),
                "total_originales_subidos": len(drive_info.get('archivos_originales_subidos', []))
            },
            "ventajas_drive": [
                "15 GB gratuitos - Más económico que S3",
                "No hay costos por transferencia", 
                "Fácil compartir y colaborar",
                "Integración nativa con Google Apps",
                "Acceso desde cualquier dispositivo",
                "Copia automática a Drive empresarial",
                "Archivos originales PDFs incluidos"
            ],
            "timestamp": timestamp_str,
            "drive_upload_status": "SUCCESS" if len(archivos_generados_lista) > 0 else "PARTIAL"
        }

        respuesta_final["archivos_generados"] = archivos_generados

        print("✅ Robot AI v2.0 - Procesamiento modular exitoso!\n")

        return JSONResponse(content=respuesta_final)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

# Función de inicialización del cliente Google Drive

@app.on_event("startup")
async def startup_event():
    """Inicializar servicios al arrancar"""
    global google_drive_client
    try:
        if os.getenv('GOOGLE_CREDENTIALS'):
            from modules.google_drive_client import get_drive_client
            google_drive_client = get_drive_client()
            if google_drive_client:
                print("✅ Google Drive inicializado correctamente")
        else:
            print("⚠️ Google Drive no configurado")
    except Exception as e:
        print(f"⚠️ Error inicializando Google Drive: {str(e)}")
        google_drive_client = None

def detectar_carpeta_original(archivos):
    """Detecta automáticamente el nombre de la carpeta original"""
    print(f"🔍 Detectando carpeta original...")

    archivos_paths = []
    for archivo in archivos:
        filename = archivo.filename
        if '/' in filename or '\\' in filename:
            path_parts = filename.replace('\\', '/').split('/')
            if len(path_parts) > 1:
                carpeta_directa = path_parts[-2]
                archivos_paths.append(carpeta_directa)

    if archivos_paths:
        from collections import Counter
        contador = Counter(archivos_paths)
        carpeta_mas_comun = contador.most_common(1)[0][0]
        print(f"✅ Carpeta detectada: {carpeta_mas_comun}")
        return carpeta_mas_comun

    # Fallback: usar nombres de archivos
    archivos_nombres = "_".join([
        archivo.filename.replace('.pdf', '').replace('.docx', '')
        .replace(' ', '-').replace('(', '').replace(')', '')        for archivo in archivos[:2]
    ])
    carpeta_fallback = re.sub(r'[^\w\-_]', '', archivos_nombres)[:30]
    print(f"⚠️ Usando fallback: {carpeta_fallback}")
    return carpeta_fallback

# ===================== ENDPOINTS DE PÁGINAS =====================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Dashboard principal"""
    try:
        with open("dashboard.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard no encontrado")

@app.get("/panel-filtros", response_class=HTMLResponse)
async def panel_filtros():
    """Sirve el panel de filtros"""
    try:
        with open("panel_filtros.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        return HTMLResponse(content=f"Error cargando panel de filtros: {e}", status_code=500)

@app.get("/resultados_analisis/{nombre_proceso}/analisis_completo.json")
async def obtener_analisis_completo(nombre_proceso: str):
    """Sirve el archivo de análisis completo de un proceso específico"""
    try:
        archivo_path = f"resultados_analisis/{nombre_proceso}/analisis_completo.json"

        if not os.path.exists(archivo_path):
            raise HTTPException(status_code=404, detail="Archivo de análisis no encontrado")

        with open(archivo_path, "r", encoding="utf-8") as f:
            datos = json.load(f)

        return JSONResponse(content=datos)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo de análisis no encontrado")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error leyendo archivo de análisis")
    except Exception as e:
        print(f"❌ Error sirviendo análisis completo para {nombre_proceso}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/documentos-rocastor", response_class=HTMLResponse)
async def documentos_rocastor():
    """Gestión de documentos Rocastor"""
    try:
        with open("documentos_rocastor.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Documentos Rocastor no encontrado")

@app.get("/panel-s3", response_class=HTMLResponse)
async def panel_s3():
    """Panel de monitoreo S3"""
    try:
        with open("panel_s3.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Panel S3 no encontrado")

# ===================== ENDPOINTS ROCASTOR =====================

@app.post("/guardar-pdf-rocastor")
async def guardar_pdf_rocastor_endpoint(pdf_data: dict):
    """Guarda PDF en Rocastor"""
    try:
        return guardar_pdf_rocastor(pdf_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando PDF: {str(e)}")

@app.get("/cargar-pdfs-rocastor")
async def cargar_pdfs_rocastor_endpoint():
    """Carga PDFs de Rocastor con estadísticas para dashboard"""
    try:
        print("📄 Cargando datos Rocastor para dashboard...")

        # Importar la función desde el módulo - corregir el await
        from modules.rocastor_manager import cargar_pdfs_rocastor
        result = await cargar_pdfs_rocastor()

        # Calcular estadísticas adicionales para el dashboard
        pdfs = result.get("pdfs", [])

        # Contar plantillas y procesos
        plantillas_generales = 0
        plantillas_especificas = 0
        procesos_documentados = set()

        # Analizar estructura de carpetas
        storage_path = "rocastor_storage"

        if os.path.exists(os.path.join(storage_path, "templates")):
            plantillas_generales = len(os.listdir(os.path.join(storage_path, "templates")))

        if os.path.exists(os.path.join(storage_path, "specific_templates")):
            specific_path = os.path.join(storage_path, "specific_templates")
            for proceso_folder in os.listdir(specific_path):
                if os.path.isdir(os.path.join(specific_path, proceso_folder)):
                    procesos_documentados.add(proceso_folder)
                    plantillas_especificas += len(os.listdir(os.path.join(specific_path, proceso_folder)))

        # Agregar estadísticas al resultado
        result.update({
            "plantillas_generales": plantillas_generales,
            "plantillas_especificas": plantillas_especificas,
            "procesos_documentados": len(procesos_documentados),
            "procesos_documentados_lista": list(procesos_documentados),
            "dashboard_stats": {
                "total_pdfs": len(pdfs),
                "plantillas_total": plantillas_generales + plantillas_especificas,
                "storage_folders": {
                    "pdfs": len(pdfs),
                    "templates": plantillas_generales,
                    "specific_templates": plantillas_especificas
                }
            }
        })

        print(f"📊 Rocastor: {len(pdfs)} PDFs, {plantillas_generales} plantillas generales, {plantillas_especificas} específicas")

        return result

    except Exception as e:
        print(f"❌ Error cargando PDFs Rocastor: {str(e)}")
        # Fallback: devolver datos vacíos pero válidos para el dashboard
        return {
            "pdfs": [],
            "total": 0,
            "plantillas_generales": 0,
            "plantillas_especificas": 0,
            "procesos_documentados": 0,
            "mensaje": f"Error cargando PDFs: {str(e)}",
            "error": True,
            "dashboard_stats": {
                "total_pdfs": 0,
                "plantillas_total": 0,
                "storage_folders": {
                    "pdfs": 0,
                    "templates": 0,
                    "specific_templates": 0
                }
            }
        }

@app.get("/cargar-plantillas-rocastor")
async def cargar_plantillas_rocastor_endpoint():
    """Carga plantillas generales de Rocastor"""
    try:
        from modules.rocastor_manager import cargar_plantillas_rocastor
        result = await cargar_plantillas_rocastor()
        return result
    except Exception as e:
        print(f"❌ Error cargando plantillas: {str(e)}")
        return {
            "templates": [],
            "total": 0,
            "mensaje": f"Error cargando plantillas: {str(e)}",
            "error": True
        }

@app.post("/guardar-plantilla-rocastor")
async def guardar_plantilla_rocastor_endpoint(template_data: dict):
    """Guarda plantilla general en Rocastor"""
    try:
        from modules.rocastor_manager import guardar_plantilla_rocastor
        return guardar_plantilla_rocastor(template_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando plantilla: {str(e)}")

@app.delete("/eliminar-plantilla-rocastor/{template_id}")
async def eliminar_plantilla_rocastor_endpoint(template_id: str):
    """Elimina plantilla general de Rocastor"""
    try:
        from modules.rocastor_manager import eliminar_plantilla_rocastor
        return eliminar_plantilla_rocastor(template_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando plantilla: {str(e)}")

@app.get("/cargar-plantillas-especificas-rocastor/{process_name}")
async def cargar_plantillas_especificas_rocastor_endpoint(process_name: str):
    """Carga plantillas específicas de un proceso"""
    try:
        from modules.rocastor_manager import cargar_plantillas_especificas_rocastor
        result = await cargar_plantillas_especificas_rocastor(process_name)
        return result
    except Exception as e:
        print(f"❌ Error cargando plantillas específicas: {str(e)}")
        return {
            "templates": [],
            "total": 0,
            "mensaje": f"Error cargando plantillas específicas: {str(e)}",
            "error": True
        }

@app.post("/guardar-plantilla-especifica-rocastor")
async def guardar_plantilla_especifica_rocastor_endpoint(template_data: dict):
    """Guarda plantilla específica de proceso en Rocastor"""
    try:
        from modules.rocastor_manager import guardar_plantilla_especifica_rocastor
        return guardar_plantilla_especifica_rocastor(template_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando plantilla específica: {str(e)}")

@app.delete("/eliminar-plantilla-especifica-rocastor/{process_name}/{template_id}")
async def eliminar_plantilla_especifica_rocastor_endpoint(process_name: str, template_id: str):
    """Elimina plantilla específica de proceso"""
    try:
        from modules.rocastor_manager import eliminar_plantilla_especifica_rocastor
        return eliminar_plantilla_especifica_rocastor(process_name, template_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando plantilla específica: {str(e)}")

@app.delete("/eliminar-pdf-rocastor/{pdf_id}")
async def eliminar_pdf_rocastor_endpoint(pdf_id: str):
    """Elimina PDF de Rocastor"""
    try:
        from modules.rocastor_manager import eliminar_pdf_rocastor
        return eliminar_pdf_rocastor(pdf_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando PDF: {str(e)}")

@app.post("/generar-carpeta-rocastor")
async def generar_carpeta_rocastor_endpoint(folder_data: dict):
    """Genera carpeta completa Rocastor"""
    try:
        # Importar la función desde el módulo
        from modules.rocastor_manager import generar_carpeta_rocastor

        zip_path, zip_filename = generar_carpeta_rocastor(folder_data)

        if not os.path.exists(zip_path):
            raise HTTPException(status_code=500, detail="Error creando archivo ZIP")

        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type="application/zip"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando carpeta: {str(e)}")

# ===================== APPS INDIVIDUALES POR PROCESO =====================

def lazy_import_app_generator():
    try:
        from process_app_generator import app_generator
        return app_generator
    except ImportError:
        print("⚠️ process_app_generator no disponible")
        return None

@app.post("/generar-app-proceso/{nombre_proceso}")
async def generar_app_proceso(nombre_proceso: str):
    """Genera una app FastAPI completa para un proceso específico"""
    try:
        print(f"🚀 Generando app individual para: {nombre_proceso}")

        # Buscar datos del proceso en Google Drive
        process_data = await fetch_process_data_from_drive(nombre_proceso)

        if not process_data:
            raise HTTPException(status_code=404, detail=f"Proceso {nombre_proceso} no encontrado")

        # Generar la app
        app_generator = lazy_import_app_generator()
        if not app_generator:
            raise HTTPException(status_code=500, detail="Generador de apps no disponible")

        zip_path = app_generator.generate_app_for_process(process_data)

        if not os.path.exists(zip_path):
            raise HTTPException(status_code=500, detail="Error generando la app")

        # Retornar el ZIP
        zip_filename = f"app_{nombre_proceso}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generando app: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando app: {str(e)}")

@app.get("/apps-disponibles")
async def listar_apps_disponibles():
    """Lista todos los procesos disponibles para generar apps"""
    try:
        # Obtener lista de procesos
        response_data = await lista_procesos()
        procesos = response_data.get('procesos', [])

        apps_info = []
        for proceso in procesos:
            app_info = {
                'nombre_proceso': proceso['nombre_proceso'],
                'id_unico': proceso.get('id_unico', proceso['nombre_proceso']),
                'carpeta_original': proceso.get('carpeta_original', 'No detectada'),
                'timestamp': proceso.get('timestamp', ''),
                'archivos_totales': proceso.get('archivos_totales', 0),
                'costo_openai': proceso.get('costo_openai_usd', 0),
                'respuestas_encontradas': proceso.get('respuestas_encontradas', 0),
                'url_generar_app': f"/generar-app-proceso/{proceso['nombre_proceso']}",
                'descripcion_app': f"App dedicada para el proceso {proceso['carpeta_original']}",
                'caracteristicas': [
                    "🏠 Página principal personalizada",
                    "📊 Dashboard interactivo",
                    "📋 API REST completa",
                    "📱 Interfaz responsive",
                    "⬇️ Descarga de datos",
                    "🚀 Deploy en un click"
                ]
            }
            apps_info.append(app_info)

        return {
            "total_apps_disponibles": len(apps_info),
            "apps": apps_info,
            "instrucciones": {
                "generar_app": "POST /generar-app-proceso/{nombre_proceso}",
                "deploy_replit": [
                    "1. Descarga el ZIP de la app",
                    "2. Crea un nuevo Repl en Replit",
                    "3. Sube el archivo ZIP",
                    "4. Extrae los archivos",
                    "5. Presiona Run",
                    "6. ¡Tu app estará funcionando!"
                ]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando apps: {str(e)}")

@app.get("/app-generator", response_class=HTMLResponse)
async def app_generator_page():
    """Página para generar apps individuales"""
    try:
        html_content = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Generador de Apps por Proceso - Robot AI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 20px auto;
            background: rgba(255, 255, 255, 0.9);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            text-align: center;
        }
        h1 {
            color: #553c9a;
            margin-bottom: 20px;
        }
        p {
            color: #333;
            font-size: 1.1em;
            line-height: 1.6;
            margin-bottom: 25px;
        }
        .features {
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            margin-top: 30px;
        }
        .feature {
            flex: 1 1 30%;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
            margin: 10px;
            text-align: left;
            transition: background-color 0.3s ease;
        }
        .feature:hover {
            background-color: #f0f0f0;
        }
        .feature h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .feature p {
            font-size: 0.95em;
            color: #666;
        }
        .cta-button {
            display: inline-block;
            padding: 12px 24px;
            background-color: #764ba2;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 20px;
            transition: background-color 0.3s ease;
        }
        .cta-button:hover {
            background-color: #553c9a;
        }
        .footer {
            margin-top: 50px;
            color: #eee;
            text-align: center;
        }
        .footer a {
            color: #fff;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Generador de Apps por Proceso</h1>
        <p>
            Convierte los análisis de tus documentos en aplicaciones web interactivas y fáciles de usar.
            Selecciona un proceso existente y genera una app personalizada con dashboard, API y descarga de datos.
        </p>

        <div class="features">
            <div class="feature">
                <h3>🏠 Página Principal Personalizada</h3>
                <p>
                    Cada app generada incluye una página de inicio única con información relevante del proceso.
                </p>
            </div>
            <div class="feature">
                <h3>📊 Dashboard Interactivo</h3>
                <p>
                    Visualiza los datos clave del análisis en un dashboard intuitivo y fácil de entender.
                </p>
            </div>
            <div class="feature">
                <h3>📋 API REST Completa</h3>
                <p>
                    Accede a los datos del proceso a través de una API REST para integrar con otros sistemas.
                </p>
            </div>
            <div class="feature">
                <h3>📱 Interfaz Responsive</h3>
                <p>
                    Las apps generadas se adaptan a cualquier dispositivo, desde computadoras de escritorio hasta teléfonos móviles.
                </p>
            </div>
            <div class="feature">
                <h3>⬇️ Descarga de Datos</h3>
                <p>
                    Descarga los datos del proceso en formato JSON para análisis offline.
                </p>
            </div>
            <div class="feature">
                <h3>🚀 Deploy en Un Click</h3>
                <p>
                    Despliega tu app en Replit en cuestión de segundos y compártela con el mundo.
                </p>
            </div>
        </div>

        <a href="/apps-disponibles" class="cta-button">
            Explorar Apps Disponibles
        </a>

        <div class="footer">
            <p>
                Hecho con 💜 por <a href="https://github.com/rocastor" target="_blank">Robot AI</a>
            </p>
        </div>
    </div>
</body>
</html>
"""
        return HTMLResponse(content=html_content)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando página: {str(e)}"
        )

# ===================== FUNCIONES AUXILIARES =====================

async def fetch_process_data_from_drive(process_name: str):
    """Obtiene datos de un proceso desde Google Drive"""
    try:
        print(f"🔍 Buscando proceso {process_name} en Google Drive...")

        from modules.google_drive_client import get_drive_client
        drive_client = get_drive_client()
        
        if not drive_client:
            print("❌ Google Drive no disponible")
            return None

        # Buscar archivo JSON del proceso en Google Drive
        try:
            # Buscar carpeta del proceso
            query = f"name='{process_name}' and mimeType='application/vnd.google-apps.folder' and '{drive_client.folder_id}' in parents"
            results = drive_client.service.files().list(q=query).execute()
            folders = results.get('files', [])
            
            if not folders:
                print(f"❌ Carpeta {process_name} no encontrada en Google Drive")
                return None
            
            folder_id = folders[0]['id']
            
            # Buscar archivo JSON en la carpeta
            json_query = f"name contains 'analisis_completo' and name contains '.json' and '{folder_id}' in parents"
            json_results = drive_client.service.files().list(q=json_query).execute()
            json_files = json_results.get('files', [])
            
            if not json_files:
                print(f"❌ Archivo JSON no encontrado para proceso {process_name}")
                return None
            
            # Obtener contenido del archivo
            file_id = json_files[0]['id']
            content = drive_client.get_file_content(file_id)
            
            if content:
                process_data = json.loads(content.decode('utf-8'))
                print(f"✅ Proceso {process_name} encontrado en Google Drive")
                return process_data
            else:
                return None
                
        except Exception as e:
            print(f"❌ Proceso {process_name} no encontrado en Google Drive: {str(e)}")
            return None

    except Exception as e:
        print(f"❌ Error buscando proceso en Google Drive: {str(e)}")
        return None

# ===================== GOOGLE DRIVE COMO ALMACENAMIENTO PRINCIPAL =====================
# S3 removido - usando solo Google Drive

# The following code block replaces the original `/lista-procesos` endpoint with a corrected version that includes the complete analysis data.
@app.get("/lista-procesos")
async def lista_procesos():
    """📊 Lista todos los procesos analizados - LOCAL + GOOGLE DRIVE"""
    try:
        procesos = []

        # PARTE 1: Buscar en almacenamiento local (resultados_analisis)
        print("📁 Buscando procesos en almacenamiento local...")
        if os.path.exists("resultados_analisis"):
            for carpeta in os.listdir("resultados_analisis"):
                carpeta_path = os.path.join("resultados_analisis", carpeta)
                if os.path.isdir(carpeta_path):
                    # Buscar analisis_completo.json
                    analisis_path = os.path.join(carpeta_path, "analisis_completo.json")
                    if os.path.exists(analisis_path):
                        try:
                            with open(analisis_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)

                            # Extraer análisis completo
                            analisis_completo = data.get("analisis", [])

                            # También incluir respuestas en formato simple para compatibilidad
                            respuestas_simples = []
                            if isinstance(analisis_completo, list):
                                for item in analisis_completo:
                                    if isinstance(item, dict) and "respuesta" in item:
                                        respuestas_simples.append(item["respuesta"])

                            # Extraer datos del resumen y costos
                            resumen = data.get("resumen", {})
                            costos = data.get("costos_openai", {})
                            metadatos = data.get("metadatos_proceso", {})
                            
                            proceso = {
                                "nombre_proceso": carpeta,
                                "carpeta_original": metadatos.get("carpeta_original_detectada") or data.get("carpeta_original", carpeta),
                                "timestamp": data.get("timestamp", ""),
                                "archivos_procesados": resumen.get("archivos_procesados_exitosamente", 0),
                                "caracteres_extraidos": resumen.get("caracteres_totales_extraidos", 0),
                                "costo_openai_usd": costos.get("costo_total_usd", 0),
                                "storage_type": "LOCAL",
                                "respuestas_encontradas": resumen.get("respuestas_con_informacion", 0),
                                "analisis_completo": analisis_completo,  # Formato completo con preguntas
                                "respuestas_openai": respuestas_simples,   # Formato simple para compatibilidad
                                "resumen": resumen,
                                "costos": costos
                            }
                            procesos.append(proceso)
                            print(f"✅ Proceso LOCAL cargado: {carpeta} con {len(analisis_completo)} análisis")

                        except Exception as e:
                            print(f"❌ Error procesando proceso local {carpeta}: {e}")

        # PARTE 2: Buscar en Google Drive
        print("☁️ Buscando procesos en Google Drive...")
        try:
            from modules.google_drive_client import get_drive_client
            drive_client = get_drive_client()
            
            if drive_client:
                # Buscar carpetas de procesos en Google Drive
                folders_query = f"'{drive_client.folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and name contains 'proceso_'"
                folders_result = drive_client.service.files().list(q=folders_query).execute()
                drive_folders = folders_result.get('files', [])
                
                print(f"☁️ Encontradas {len(drive_folders)} carpetas de proceso en Google Drive")
                
                for folder in drive_folders:
                    folder_name = folder['name']
                    folder_id = folder['id']
                    
                    # Verificar si ya existe en procesos locales
                    exists_locally = any(p['nombre_proceso'] == folder_name for p in procesos)
                    if exists_locally:
                        print(f"⚠️ Proceso {folder_name} ya existe localmente - omitiendo duplicado")
                        continue
                    
                    try:
                        # Buscar archivo JSON en la carpeta
                        json_query = f"name contains 'analisis_completo' and name contains '.json' and '{folder_id}' in parents"
                        json_results = drive_client.service.files().list(q=json_query).execute()
                        json_files = json_results.get('files', [])
                        
                        if json_files:
                            # Obtener contenido del archivo JSON
                            file_id = json_files[0]['id']
                            content = drive_client.get_file_content(file_id)
                            
                            if content:
                                data = json.loads(content.decode('utf-8'))
                                
                                # Extraer análisis completo
                                analisis_completo = data.get("analisis", [])
                                
                                # También incluir respuestas en formato simple para compatibilidad
                                respuestas_simples = []
                                if isinstance(analisis_completo, list):
                                    for item in analisis_completo:
                                        if isinstance(item, dict) and "respuesta" in item:
                                            respuestas_simples.append(item["respuesta"])

                                # Extraer datos del resumen y costos
                                resumen = data.get("resumen", {})
                                costos = data.get("costos_openai", {})
                                metadatos = data.get("metadatos_proceso", {})
                                
                                proceso = {
                                    "nombre_proceso": folder_name,
                                    "carpeta_original": metadatos.get("carpeta_original_detectada") or data.get("carpeta_original", folder_name),
                                    "timestamp": data.get("timestamp", ""),
                                    "archivos_procesados": resumen.get("archivos_procesados_exitosamente", 0),
                                    "caracteres_extraidos": resumen.get("caracteres_totales_extraidos", 0),
                                    "costo_openai_usd": costos.get("costo_total_usd", 0),
                                    "storage_type": "GOOGLE_DRIVE",
                                    "respuestas_encontradas": resumen.get("respuestas_con_informacion", 0),
                                    "analisis_completo": analisis_completo,
                                    "respuestas_openai": respuestas_simples,
                                    "resumen": resumen,
                                    "costos": costos,
                                    "drive_folder_id": folder_id,
                                    "drive_link": f"https://drive.google.com/drive/folders/{folder_id}"
                                }
                                procesos.append(proceso)
                                print(f"✅ Proceso GOOGLE DRIVE cargado: {folder_name} con {len(analisis_completo)} análisis")
                            else:
                                print(f"⚠️ No se pudo obtener contenido del archivo JSON para {folder_name}")
                        else:
                            print(f"⚠️ No se encontró archivo JSON para {folder_name}")
                            
                    except Exception as e:
                        print(f"❌ Error procesando proceso Google Drive {folder_name}: {e}")
                        continue
                        
            else:
                print("⚠️ Google Drive no disponible")
                
        except Exception as e:
            print(f"❌ Error accediendo a Google Drive: {e}")

        # Ordenar procesos por timestamp (más recientes primero)
        procesos.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        print(f"📊 Total procesos encontrados: {len(procesos)} (LOCAL + GOOGLE DRIVE)")
        
        # Calcular estadísticas
        procesos_locales = len([p for p in procesos if p.get('storage_type') == 'LOCAL'])
        procesos_drive = len([p for p in procesos if p.get('storage_type') == 'GOOGLE_DRIVE'])
        
        return {
            "success": True, 
            "procesos": procesos,
            "total_procesos": len(procesos),
            "estadisticas": {
                "procesos_locales": procesos_locales,
                "procesos_google_drive": procesos_drive,
                "total_costo_usd": sum(p.get('costo_openai_usd', 0) for p in procesos),
                "total_respuestas": sum(p.get('respuestas_encontradas', 0) for p in procesos)
            }
        }

    except Exception as e:
        print(f"❌ Error en lista-procesos: {e}")
        return {"success": False, "error": str(e)}

# ===================== CONFIGURACIÓN DEL SERVIDOR =====================

if __name__ == "__main__":
    print("🤖 Iniciando Robot AI v2.0 - Arquitectura Modular")
    print("🔧 Configurando servidor...")

    # Verificar configuración
    if not OPENAI_API_KEY:
        print("⚠️ ADVERTENCIA: OPENAI_API_KEY no configurada")
    else:
        print("✅ OpenAI API Key configurada")

    if not os.getenv('GOOGLE_DRIVE_CREDENTIALS'):
        print("⚠️ ADVERTENCIA: Google Drive no configurado")
    else:
        print("✅ Google Drive configurado")

    print("🚀 Servidor iniciando en puerto 5000...")
    uvicorn.run(app, host="0.0.0.0", port=5000)
