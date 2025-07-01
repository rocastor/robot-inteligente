
#!/usr/bin/env python3
"""
🔍 Debug Específico Google Drive - Robot AI
Herramienta de debugging profundo para Google Drive
"""

import os
import json
from datetime import datetime

def debug_google_drive_complete():
    """Debugging completo de Google Drive"""
    print("🔍 ===== DEBUG COMPLETO GOOGLE DRIVE =====\n")
    
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "recommendations": []
    }
    
    # 1. Verificar variable de entorno
    print("1️⃣ ===== VERIFICACIÓN DE CREDENCIALES =====")
    credentials_json = os.getenv('GOOGLE_CREDENTIALS')
    
    if not credentials_json:
        print("❌ GOOGLE_CREDENTIALS no configurado")
        debug_info["checks"]["credentials_env"] = {
            "status": "missing",
            "message": "Variable de entorno no encontrada"
        }
        debug_info["recommendations"].append("Configurar GOOGLE_CREDENTIALS con las credenciales del service account")
        return debug_info
    
    print(f"✅ Credenciales encontradas: {len(credentials_json)} caracteres")
    debug_info["checks"]["credentials_env"] = {
        "status": "found",
        "length": len(credentials_json)
    }
    
    # 2. Validar JSON
    print("\n2️⃣ ===== VALIDACIÓN JSON =====")
    try:
        creds_data = json.loads(credentials_json)
        print("✅ JSON válido")
        
        # Verificar tipo
        cred_type = creds_data.get('type', 'unknown')
        print(f"📋 Tipo de credencial: {cred_type}")
        
        if cred_type != 'service_account':
            print("⚠️ ADVERTENCIA: Se esperaba 'service_account'")
            debug_info["recommendations"].append("Usar credenciales de service account, no OAuth2")
        
        # Verificar campos requeridos
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'auth_uri', 'token_uri']
        missing_fields = [field for field in required_fields if field not in creds_data]
        
        if missing_fields:
            print(f"❌ Campos faltantes: {missing_fields}")
            debug_info["checks"]["json_validation"] = {
                "status": "incomplete",
                "missing_fields": missing_fields
            }
            debug_info["recommendations"].append(f"Completar campos faltantes: {missing_fields}")
        else:
            print("✅ Todos los campos requeridos presentes")
            debug_info["checks"]["json_validation"] = {
                "status": "complete",
                "service_account": creds_data.get('client_email'),
                "project_id": creds_data.get('project_id')
            }
        
        # Información del service account
        print(f"📧 Service Account: {creds_data.get('client_email', 'No especificado')}")
        print(f"📂 Project ID: {creds_data.get('project_id', 'No especificado')}")
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parseando JSON: {str(e)}")
        debug_info["checks"]["json_validation"] = {
            "status": "invalid",
            "error": str(e)
        }
        debug_info["recommendations"].append("Verificar que las credenciales JSON sean válidas")
        return debug_info
    
    # 3. Test de librerías
    print("\n3️⃣ ===== VERIFICACIÓN DE LIBRERÍAS =====")
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        print("✅ Librerías Google instaladas correctamente")
        debug_info["checks"]["libraries"] = {
            "status": "installed"
        }
    except ImportError as e:
        print(f"❌ Error importando librerías: {str(e)}")
        debug_info["checks"]["libraries"] = {
            "status": "missing",
            "error": str(e)
        }
        debug_info["recommendations"].append("Instalar: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return debug_info
    
    # 4. Test de autenticación
    print("\n4️⃣ ===== TEST DE AUTENTICACIÓN =====")
    try:
        from google.oauth2 import service_account
        
        # Crear credenciales
        credentials = service_account.Credentials.from_service_account_info(
            creds_data,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        print("✅ Credenciales creadas exitosamente")
        debug_info["checks"]["authentication"] = {
            "status": "success"
        }
        
        # Verificar si las credenciales están expiradas
        if credentials.expired:
            print("⚠️ Credenciales expiradas, intentando refresh...")
            try:
                credentials.refresh(google.auth.transport.requests.Request())
                print("✅ Credenciales renovadas")
            except Exception as refresh_error:
                print(f"❌ Error renovando credenciales: {str(refresh_error)}")
                debug_info["checks"]["authentication"]["refresh_error"] = str(refresh_error)
        
    except Exception as e:
        print(f"❌ Error creando credenciales: {str(e)}")
        debug_info["checks"]["authentication"] = {
            "status": "failed",
            "error": str(e)
        }
        debug_info["recommendations"].append("Verificar que las credenciales del service account sean válidas")
        return debug_info
    
    # 5. Test de conexión API
    print("\n5️⃣ ===== TEST DE CONEXIÓN API =====")
    try:
        from googleapiclient.discovery import build
        
        service = build('drive', 'v3', credentials=credentials)
        print("✅ Servicio Google Drive creado")
        
        # Test básico
        results = service.files().list(pageSize=1).execute()
        files = results.get('files', [])
        print(f"✅ Conexión exitosa - {len(files)} archivos accesibles")
        
        debug_info["checks"]["api_connection"] = {
            "status": "success",
            "files_accessible": len(files)
        }
        
        # Test de cuota
        try:
            about = service.about().get(fields='storageQuota').execute()
            quota = about.get('storageQuota', {})
            print(f"📊 Cuota de almacenamiento obtenida")
            debug_info["checks"]["quota"] = {
                "status": "accessible",
                "quota_info": quota
            }
        except Exception as quota_error:
            print(f"⚠️ No se pudo obtener cuota: {str(quota_error)}")
            debug_info["checks"]["quota"] = {
                "status": "inaccessible",
                "error": str(quota_error)
            }
        
    except Exception as e:
        print(f"❌ Error en conexión API: {str(e)}")
        debug_info["checks"]["api_connection"] = {
            "status": "failed",
            "error": str(e)
        }
        
        # Analizar tipo de error
        error_str = str(e).lower()
        if 'insufficient authentication scopes' in error_str:
            debug_info["recommendations"].append("Verificar que el service account tenga los scopes necesarios para Google Drive")
        elif 'forbidden' in error_str or 'access denied' in error_str:
            debug_info["recommendations"].append("Verificar que el service account tenga permisos de acceso a Google Drive")
        elif 'not found' in error_str:
            debug_info["recommendations"].append("Verificar que la API de Google Drive esté habilitada en el proyecto")
        else:
            debug_info["recommendations"].append(f"Error de API: {str(e)}")
        
        return debug_info
    
    # 6. Test de módulo interno
    print("\n6️⃣ ===== TEST DE MÓDULO INTERNO =====")
    try:
        from modules.google_drive_client import get_drive_client, test_google_drive_connection
        
        # Test del cliente interno
        drive_client = get_drive_client()
        if drive_client:
            print("✅ Cliente interno creado exitosamente")
            debug_info["checks"]["internal_module"] = {
                "status": "success"
            }
            
            # Test de función de test
            test_result = test_google_drive_connection()
            print(f"📋 Test interno: {test_result.get('message', 'Sin mensaje')}")
            debug_info["checks"]["internal_test"] = test_result
            
        else:
            print("❌ Error creando cliente interno")
            debug_info["checks"]["internal_module"] = {
                "status": "failed"
            }
    except Exception as e:
        print(f"❌ Error en módulo interno: {str(e)}")
        debug_info["checks"]["internal_module"] = {
            "status": "error",
            "error": str(e)
        }
    
    # 7. Resumen y recomendaciones
    print("\n7️⃣ ===== RESUMEN FINAL =====")
    
    issues_found = []
    for check_name, check_data in debug_info["checks"].items():
        if check_data.get("status") in ["failed", "missing", "incomplete", "invalid", "error"]:
            issues_found.append(f"{check_name}: {check_data.get('status', 'unknown')}")
    
    if not issues_found:
        print("🎉 ¡Todos los tests pasaron! Google Drive debería funcionar correctamente")
        debug_info["overall_status"] = "healthy"
    else:
        print(f"⚠️ Se encontraron {len(issues_found)} problemas:")
        for issue in issues_found:
            print(f"   • {issue}")
        debug_info["overall_status"] = "issues_found"
        debug_info["issues"] = issues_found
    
    print(f"\n📄 Recomendaciones ({len(debug_info['recommendations'])}):")
    for i, rec in enumerate(debug_info['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    # Guardar reporte
    with open('debug_google_drive_report.json', 'w', encoding='utf-8') as f:
        json.dump(debug_info, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 Reporte completo guardado en: debug_google_drive_report.json")
    
    return debug_info

if __name__ == "__main__":
    debug_google_drive_complete()
