
import os
import json
import glob
import shutil
from datetime import datetime
from aws_s3_utils import listar_archivos_s3, get_s3_client

def verificar_archivos_en_s3():
    """Verifica qué procesos están disponibles en S3"""
    try:
        print("☁️ Verificando archivos en AWS S3...")
        
        if not (os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY')):
            print("❌ AWS S3 no configurado")
            return False, []

        archivos_s3 = listar_archivos_s3("procesos/")
        procesos_en_s3 = []
        
        for archivo in archivos_s3:
            if archivo['key'].endswith('analisis_completo.json'):
                # Extraer nombre del proceso
                parts = archivo['key'].split('/')
                if len(parts) >= 3:
                    proceso_name = parts[-2]  # El directorio del proceso
                    procesos_en_s3.append(proceso_name)
        
        print(f"✅ Encontrados {len(procesos_en_s3)} procesos en S3")
        return True, procesos_en_s3
        
    except Exception as e:
        print(f"❌ Error verificando S3: {str(e)}")
        return False, []

def limpiar_resultados_analisis(procesos_en_s3):
    """Elimina carpetas de resultados_analisis que están respaldadas en S3"""
    carpetas_eliminadas = 0
    
    print("\n🗂️ Limpiando carpetas de resultados_analisis...")
    
    if not os.path.exists("resultados_analisis"):
        print("⚠️ Carpeta resultados_analisis no existe")
        return 0
    
    carpetas_locales = glob.glob("resultados_analisis/proceso_*")
    
    for carpeta in carpetas_locales:
        nombre_carpeta = os.path.basename(carpeta)
        
        # Verificar si está en S3
        proceso_en_s3 = any(nombre_carpeta in proceso_s3 for proceso_s3 in procesos_en_s3)
        
        if proceso_en_s3:
            try:
                # Calcular tamaño antes de eliminar
                tamaño = 0
                for root, dirs, files in os.walk(carpeta):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            tamaño += os.path.getsize(file_path)
                
                shutil.rmtree(carpeta)
                carpetas_eliminadas += 1
                print(f"✅ Eliminado: {nombre_carpeta} ({tamaño/1024/1024:.1f} MB)")
                
            except Exception as e:
                print(f"❌ Error eliminando {carpeta}: {str(e)}")
        else:
            print(f"⚠️ Mantenido: {nombre_carpeta} (no encontrado en S3)")
    
    return carpetas_eliminadas

def limpiar_checkpoints():
    """Elimina archivos de checkpoint antiguos"""
    archivos_eliminados = 0
    
    print("\n📊 Limpiando archivos checkpoint...")
    
    checkpoints = glob.glob("checkpoint_analisis_*.json")
    
    for checkpoint in checkpoints:
        try:
            os.remove(checkpoint)
            archivos_eliminados += 1
            print(f"✅ Eliminado: {checkpoint}")
        except Exception as e:
            print(f"❌ Error eliminando {checkpoint}: {str(e)}")
    
    return archivos_eliminados

def limpiar_assets_antiguos():
    """Analiza y sugiere limpieza de assets antiguos"""
    print("\n🖼️ Analizando attached_assets...")
    
    if not os.path.exists("attached_assets"):
        print("⚠️ Carpeta attached_assets no existe")
        return 0
    
    archivos_assets = os.listdir("attached_assets")
    total_archivos = len(archivos_assets)
    
    if total_archivos > 0:
        # Calcular tamaño total
        tamaño_total = 0
        for archivo in archivos_assets:
            file_path = os.path.join("attached_assets", archivo)
            if os.path.isfile(file_path):
                tamaño_total += os.path.getsize(file_path)
        
        print(f"📊 Encontrados {total_archivos} archivos ({tamaño_total/1024/1024:.1f} MB)")
        print(f"💡 Sugerencia: Revisar manualmente y eliminar imágenes no utilizadas")
    
    return total_archivos

def generar_reporte_limpieza():
    """Genera reporte de la limpieza realizada"""
    reporte = {
        "timestamp": datetime.now().isoformat(),
        "accion": "limpieza_archivos_duplicados",
        "motivo": "optimizar_espacio_replit_s3_backup",
        "archivos_mantenidos": {
            "codigo_fuente": "main.py, modules/, *.html",
            "configuracion": ".replit, pyproject.toml, requirements.txt",
            "rocastor_storage": "plantillas y PDFs activos"
        },
        "archivos_eliminados": {
            "resultados_analisis": "procesos respaldados en S3",
            "checkpoints": "archivos temporales antiguos"
        },
        "siguiente_paso": "verificar_funcionamiento_aplicacion"
    }
    
    with open("reporte_limpieza.json", "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)
    
    print(f"📄 Reporte guardado en: reporte_limpieza.json")

def main():
    """Función principal de limpieza"""
    print("🚀 ===== LIMPIEZA DE ARCHIVOS DUPLICADOS =====")
    print("🎯 Objetivo: Optimizar espacio en Replit eliminando duplicados en S3\n")
    
    # Verificar conexión S3
    s3_disponible, procesos_en_s3 = verificar_archivos_en_s3()
    
    if not s3_disponible:
        print("❌ Cancelando limpieza - S3 no disponible")
        return
    
    if not procesos_en_s3:
        print("⚠️ No se encontraron procesos en S3 - Cancelando limpieza")
        return
    
    print(f"\n📋 PLAN DE LIMPIEZA:")
    print(f"✓ Eliminar carpetas de resultados_analisis/ respaldadas en S3")
    print(f"✓ Eliminar archivos de checkpoint antiguos")
    print(f"✓ Analizar carpeta attached_assets/")
    print(f"✓ Generar reporte de limpieza")
    
    respuesta = input(f"\n¿Continuar con la limpieza? (y/N): ").strip().lower()
    if respuesta != 'y' and respuesta != 'yes':
        print("❌ Limpieza cancelada por el usuario")
        return
    
    # Ejecutar limpieza
    total_eliminados = 0
    
    total_eliminados += limpiar_resultados_analisis(procesos_en_s3)
    total_eliminados += limpiar_checkpoints()
    limpiar_assets_antiguos()
    
    # Generar reporte
    generar_reporte_limpieza()
    
    print(f"\n🎉 ===== LIMPIEZA COMPLETADA =====")
    print(f"📊 Total de elementos eliminados: {total_eliminados}")
    print(f"💾 Espacio liberado en Replit")
    print(f"☁️ Datos seguros en AWS S3")
    print(f"⚡ Rendimiento de edición mejorado")

if __name__ == "__main__":
    main()
