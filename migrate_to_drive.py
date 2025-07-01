
#!/usr/bin/env python3
"""
🚀 Migración de Procesos Existentes a Google Drive
Sube todos los procesos locales existentes a Google Drive
"""

import os
import json
import glob
from datetime import datetime
from modules.google_drive_client import get_drive_client

def migrate_existing_processes():
    """Migra todos los procesos existentes de local a Google Drive"""
    print("🚀 ===== MIGRACIÓN A GOOGLE DRIVE =====\n")
    
    # Verificar conexión a Google Drive
    drive_client = get_drive_client()
    if not drive_client:
        print("❌ Google Drive no disponible - no se puede migrar")
        return False
    
    print("✅ Google Drive conectado correctamente")
    print(f"📁 Carpeta principal ID: {drive_client.folder_id}")
    
    # Buscar procesos locales
    procesos_locales = glob.glob("resultados_analisis/proceso_*")
    print(f"📂 Encontrados {len(procesos_locales)} procesos locales para migrar\n")
    
    migrados_exitosos = 0
    errores = []
    
    for i, carpeta_proceso in enumerate(procesos_locales, 1):
        if not os.path.isdir(carpeta_proceso):
            continue
            
        nombre_proceso = os.path.basename(carpeta_proceso)
        print(f"📤 [{i}/{len(procesos_locales)}] Migrando: {nombre_proceso}")
        
        try:
            # Buscar archivo JSON principal
            json_files = glob.glob(os.path.join(carpeta_proceso, "analisis_completo.json"))
            if not json_files:
                print(f"   ⚠️ No se encontró analisis_completo.json - saltando")
                continue
                
            json_path = json_files[0]
            
            # Leer datos del proceso
            with open(json_path, 'r', encoding='utf-8') as f:
                proceso_data = json.load(f)
            
            metadatos = proceso_data.get('metadatos_proceso', {})
            carpeta_original = metadatos.get('carpeta_original_detectada', 'Sin_Carpeta')
            
            print(f"   📁 Carpeta original: {carpeta_original}")
            
            # Preparar archivos para subir
            archivos_para_subir = []
            
            # Listar todos los archivos en la carpeta
            for archivo in os.listdir(carpeta_proceso):
                archivo_path = os.path.join(carpeta_proceso, archivo)
                if os.path.isfile(archivo_path):
                    archivos_para_subir.append({
                        'file_path': archivo_path,
                        'filename': archivo,
                        'metadata': {
                            'tipo': 'migracion_automatica',
                            'proceso_original': nombre_proceso,
                            'timestamp_migracion': datetime.now().isoformat()
                        }
                    })
            
            print(f"   📄 Archivos a subir: {len(archivos_para_subir)}")
            
            # Subir proceso completo a Google Drive
            resultado = drive_client.upload_process_folder(
                process_name=nombre_proceso,
                files_data=archivos_para_subir,
                original_folder=carpeta_original
            )
            
            if resultado and resultado.get('success'):
                migrados_exitosos += 1
                archivos_subidos = len(resultado.get('uploaded_files', []))
                folder_id = resultado.get('process_folder_id')
                
                print(f"   ✅ Migrado exitosamente: {archivos_subidos} archivos")
                print(f"   🔗 Carpeta ID: {folder_id}")
                print(f"   🌐 Link: https://drive.google.com/drive/folders/{folder_id}")
                
                # Actualizar el JSON local con información de Drive
                proceso_data['google_drive_info'] = {
                    'migrated': True,
                    'migration_date': datetime.now().isoformat(),
                    'folder_id': folder_id,
                    'uploaded_files': archivos_subidos,
                    'web_view_link': f"https://drive.google.com/drive/folders/{folder_id}"
                }
                
                # Guardar JSON actualizado
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(proceso_data, f, ensure_ascii=False, indent=2)
                
            else:
                error_msg = resultado.get('error', 'Error desconocido') if resultado else 'No se pudo subir'
                print(f"   ❌ Error: {error_msg}")
                errores.append(f"{nombre_proceso}: {error_msg}")
                
        except Exception as e:
            error_msg = f"Error procesando {nombre_proceso}: {str(e)}"
            print(f"   ❌ {error_msg}")
            errores.append(error_msg)
        
        print()  # Línea en blanco entre procesos
    
    # Resumen final
    print("📊 ===== RESUMEN DE MIGRACIÓN =====")
    print(f"✅ Procesos migrados exitosamente: {migrados_exitosos}")
    print(f"❌ Errores: {len(errores)}")
    print(f"📁 Total procesos procesados: {len(procesos_locales)}")
    
    if errores:
        print(f"\n⚠️ Errores encontrados:")
        for error in errores:
            print(f"   • {error}")
    
    if migrados_exitosos > 0:
        print(f"\n🎉 ¡Migración completada!")
        print(f"🔗 Carpeta principal Google Drive:")
        print(f"   https://drive.google.com/drive/folders/{drive_client.folder_id}")
    
    return migrados_exitosos > 0

def verificar_archivos_drive():
    """Verifica qué archivos están ahora en Google Drive"""
    print("\n🔍 ===== VERIFICACIÓN POST-MIGRACIÓN =====")
    
    drive_client = get_drive_client()
    if not drive_client:
        print("❌ No se puede verificar - Google Drive no disponible")
        return
    
    try:
        # Listar archivos en carpeta principal
        main_files = drive_client.list_files()
        print(f"📁 Archivos en carpeta principal: {len(main_files)}")
        
        # Buscar subcarpetas (carpetas originales)
        folders_query = f"'{drive_client.folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
        folders_result = drive_client.service.files().list(q=folders_query).execute()
        folders = folders_result.get('files', [])
        
        print(f"📂 Subcarpetas (carpetas originales): {len(folders)}")
        
        total_archivos_procesos = 0
        for folder in folders:
            print(f"   📁 {folder['name']}")
            
            # Buscar procesos en esta carpeta
            subfolders_query = f"'{folder['id']}' in parents and mimeType='application/vnd.google-apps.folder'"
            subfolders_result = drive_client.service.files().list(q=subfolders_query).execute()
            subfolders = subfolders_result.get('files', [])
            
            for subfolder in subfolders:
                # Contar archivos en cada proceso
                process_files = drive_client.list_files(subfolder['id'])
                total_archivos_procesos += len(process_files)
                print(f"      📂 {subfolder['name']}: {len(process_files)} archivos")
        
        print(f"\n📊 RESUMEN VERIFICACIÓN:")
        print(f"   📁 Total carpetas originales: {len(folders)}")
        print(f"   📄 Total archivos de procesos: {total_archivos_procesos}")
        print(f"   🔗 Link directo: https://drive.google.com/drive/folders/{drive_client.folder_id}")
        
    except Exception as e:
        print(f"❌ Error verificando: {str(e)}")

if __name__ == "__main__":
    print("🚀 Robot AI - Migración a Google Drive")
    print("=====================================\n")
    
    # Ejecutar migración
    success = migrate_existing_processes()
    
    if success:
        # Verificar resultados
        verificar_archivos_drive()
    
    print("\n✅ Proceso completado")
#!/usr/bin/env python3
"""
🚀 Migración de Procesos Existentes a Google Drive
Sube todos los procesos locales existentes a Google Drive
"""

import os
import json
import glob
from datetime import datetime
from modules.google_drive_client import get_drive_client

def migrate_existing_processes():
    """Migra todos los procesos existentes de local a Google Drive"""
    print("🚀 ===== MIGRACIÓN A GOOGLE DRIVE =====\n")
    
    # Verificar conexión a Google Drive
    drive_client = get_drive_client()
    if not drive_client:
        print("❌ Google Drive no disponible - no se puede migrar")
        return False
    
    print("✅ Google Drive conectado correctamente")
    print(f"📁 Carpeta principal ID: {drive_client.folder_id}")
    
    # Buscar procesos locales
    procesos_locales = glob.glob("resultados_analisis/proceso_*")
    print(f"📂 Encontrados {len(procesos_locales)} procesos locales para migrar\n")
    
    migrados_exitosos = 0
    errores = []
    
    for i, carpeta_proceso in enumerate(procesos_locales, 1):
        if not os.path.isdir(carpeta_proceso):
            continue
            
        nombre_proceso = os.path.basename(carpeta_proceso)
        print(f"📤 [{i}/{len(procesos_locales)}] Migrando: {nombre_proceso}")
        
        try:
            # Buscar archivo JSON principal
            json_files = glob.glob(os.path.join(carpeta_proceso, "analisis_completo.json"))
            if not json_files:
                print(f"   ⚠️ No se encontró analisis_completo.json - saltando")
                continue
                
            json_path = json_files[0]
            
            # Leer datos del proceso
            with open(json_path, 'r', encoding='utf-8') as f:
                proceso_data = json.load(f)
            
            metadatos = proceso_data.get('metadatos_proceso', {})
            carpeta_original = metadatos.get('carpeta_original_detectada', 'Sin_Carpeta')
            
            print(f"   📁 Carpeta original: {carpeta_original}")
            
            # Preparar archivos para subir
            archivos_para_subir = []
            
            # Listar todos los archivos en la carpeta
            for archivo in os.listdir(carpeta_proceso):
                archivo_path = os.path.join(carpeta_proceso, archivo)
                if os.path.isfile(archivo_path):
                    archivos_para_subir.append({
                        'file_path': archivo_path,
                        'filename': archivo,
                        'metadata': {
                            'tipo': 'migracion_automatica',
                            'proceso_original': nombre_proceso,
                            'timestamp_migracion': datetime.now().isoformat()
                        }
                    })
            
            print(f"   📄 Archivos a subir: {len(archivos_para_subir)}")
            
            # Subir proceso completo a Google Drive
            resultado = drive_client.upload_process_folder(
                process_name=nombre_proceso,
                files_data=archivos_para_subir,
                original_folder=carpeta_original
            )
            
            if resultado and resultado.get('success'):
                migrados_exitosos += 1
                archivos_subidos = len(resultado.get('uploaded_files', []))
                folder_id = resultado.get('process_folder_id')
                
                print(f"   ✅ Migrado exitosamente: {archivos_subidos} archivos")
                print(f"   🔗 Carpeta ID: {folder_id}")
                print(f"   🌐 Link: https://drive.google.com/drive/folders/{folder_id}")
                
                # Actualizar el JSON local con información de Drive
                proceso_data['google_drive_info'] = {
                    'migrated': True,
                    'migration_date': datetime.now().isoformat(),
                    'folder_id': folder_id,
                    'uploaded_files': archivos_subidos,
                    'web_view_link': f"https://drive.google.com/drive/folders/{folder_id}"
                }
                
                # Guardar JSON actualizado
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(proceso_data, f, ensure_ascii=False, indent=2)
                
            else:
                error_msg = resultado.get('error', 'Error desconocido') if resultado else 'No se pudo subir'
                print(f"   ❌ Error: {error_msg}")
                errores.append(f"{nombre_proceso}: {error_msg}")
                
        except Exception as e:
            error_msg = f"Error procesando {nombre_proceso}: {str(e)}"
            print(f"   ❌ {error_msg}")
            errores.append(error_msg)
        
        print()  # Línea en blanco entre procesos
    
    # Resumen final
    print("📊 ===== RESUMEN DE MIGRACIÓN =====")
    print(f"✅ Procesos migrados exitosamente: {migrados_exitosos}")
    print(f"❌ Errores: {len(errores)}")
    print(f"📁 Total procesos procesados: {len(procesos_locales)}")
    
    if errores:
        print(f"\n⚠️ Errores encontrados:")
        for error in errores:
            print(f"   • {error}")
    
    if migrados_exitosos > 0:
        print(f"\n🎉 ¡Migración completada!")
        print(f"🔗 Carpeta principal Google Drive:")
        print(f"   https://drive.google.com/drive/folders/{drive_client.folder_id}")
    
    return migrados_exitosos > 0

def verificar_archivos_drive():
    """Verifica qué archivos están ahora en Google Drive"""
    print("\n🔍 ===== VERIFICACIÓN POST-MIGRACIÓN =====")
    
    drive_client = get_drive_client()
    if not drive_client:
        print("❌ No se puede verificar - Google Drive no disponible")
        return
    
    try:
        # Listar archivos en carpeta principal
        main_files = drive_client.list_files()
        print(f"📁 Archivos en carpeta principal: {len(main_files)}")
        
        # Buscar subcarpetas (carpetas originales)
        folders_query = f"'{drive_client.folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
        folders_result = drive_client.service.files().list(q=folders_query).execute()
        folders = folders_result.get('files', [])
        
        print(f"📂 Subcarpetas (carpetas originales): {len(folders)}")
        
        total_archivos_procesos = 0
        for folder in folders:
            print(f"   📁 {folder['name']}")
            
            # Buscar procesos en esta carpeta
            subfolders_query = f"'{folder['id']}' in parents and mimeType='application/vnd.google-apps.folder'"
            subfolders_result = drive_client.service.files().list(q=subfolders_query).execute()
            subfolders = subfolders_result.get('files', [])
            
            for subfolder in subfolders:
                # Contar archivos en cada proceso
                process_files = drive_client.list_files(subfolder['id'])
                total_archivos_procesos += len(process_files)
                print(f"      📂 {subfolder['name']}: {len(process_files)} archivos")
        
        print(f"\n📊 RESUMEN VERIFICACIÓN:")
        print(f"   📁 Total carpetas originales: {len(folders)}")
        print(f"   📄 Total archivos de procesos: {total_archivos_procesos}")
        print(f"   🔗 Link directo: https://drive.google.com/drive/folders/{drive_client.folder_id}")
        
    except Exception as e:
        print(f"❌ Error verificando: {str(e)}")

if __name__ == "__main__":
    print("🚀 Robot AI - Migración a Google Drive")
    print("=====================================\n")
    
    # Ejecutar migración
    success = migrate_existing_processes()
    
    if success:
        # Verificar resultados
        verificar_archivos_drive()
    
    print("\n✅ Proceso completado")
