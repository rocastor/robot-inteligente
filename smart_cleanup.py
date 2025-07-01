
#!/usr/bin/env python3
"""
🧹 Script de Limpieza Inteligente - Robot AI
Optimiza espacio en Replit eliminando duplicados seguros
"""

import os
import json
import glob
import shutil
from datetime import datetime, timedelta
from aws_s3_utils import listar_archivos_s3, get_s3_client

class SmartCleanup:
    def __init__(self):
        self.files_cleaned = 0
        self.space_freed = 0
        self.s3_available = False
        self.procesos_en_s3 = []
        
    def check_s3_connection(self):
        """Verifica conexión con S3"""
        try:
            if not (os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY')):
                print("❌ AWS S3 no configurado")
                return False
                
            archivos_s3 = listar_archivos_s3("procesos/")
            for archivo in archivos_s3:
                if archivo['key'].endswith('analisis_completo.json'):
                    parts = archivo['key'].split('/')
                    if len(parts) >= 3:
                        proceso_name = parts[-2]
                        self.procesos_en_s3.append(proceso_name)
            
            self.s3_available = True
            print(f"✅ S3 conectado: {len(self.procesos_en_s3)} procesos encontrados")
            return True
            
        except Exception as e:
            print(f"❌ Error S3: {str(e)}")
            return False

    def calculate_folder_size(self, folder_path):
        """Calcula tamaño de carpeta"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except:
            pass
        return total_size

    def clean_local_processes_in_s3(self):
        """Limpia procesos locales que están respaldados en S3"""
        if not self.s3_available:
            print("⚠️ Saltando limpieza de procesos - S3 no disponible")
            return 0
            
        cleaned = 0
        carpetas_locales = glob.glob("resultados_analisis/proceso_*")
        
        print(f"\n🗂️ Verificando {len(carpetas_locales)} carpetas locales...")
        
        for carpeta in carpetas_locales:
            if os.path.isdir(carpeta):
                nombre_carpeta = os.path.basename(carpeta)
                
                # Verificar si está en S3 con coincidencia flexible
                proceso_en_s3 = any(
                    nombre_carpeta in proceso_s3 or 
                    proceso_s3 in nombre_carpeta 
                    for proceso_s3 in self.procesos_en_s3
                )
                
                if proceso_en_s3:
                    try:
                        size = self.calculate_folder_size(carpeta)
                        shutil.rmtree(carpeta)
                        cleaned += 1
                        self.space_freed += size
                        print(f"✅ Eliminado: {nombre_carpeta} ({size/1024/1024:.1f} MB)")
                    except Exception as e:
                        print(f"❌ Error eliminando {carpeta}: {str(e)}")
                else:
                    print(f"⚠️ Mantenido: {nombre_carpeta} (no en S3)")
        
        return cleaned

    def clean_old_checkpoints(self):
        """Limpia checkpoints antiguos (más de 7 días)"""
        cleaned = 0
        cutoff_date = datetime.now() - timedelta(days=7)
        
        checkpoints = glob.glob("checkpoint_analisis_*.json")
        
        print(f"\n📊 Verificando {len(checkpoints)} checkpoints...")
        
        for checkpoint in checkpoints:
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(checkpoint))
                if file_time < cutoff_date:
                    size = os.path.getsize(checkpoint)
                    os.remove(checkpoint)
                    cleaned += 1
                    self.space_freed += size
                    print(f"✅ Eliminado: {checkpoint}")
                else:
                    print(f"⚠️ Mantenido: {checkpoint} (reciente)")
            except Exception as e:
                print(f"❌ Error con {checkpoint}: {str(e)}")
        
        return cleaned

    def clean_old_assets(self):
        """Limpia assets antiguos (más de 30 días)"""
        if not os.path.exists("attached_assets"):
            return 0
            
        cleaned = 0
        cutoff_date = datetime.now() - timedelta(days=30)
        
        assets = os.listdir("attached_assets")
        print(f"\n🖼️ Verificando {len(assets)} assets...")
        
        for asset in assets:
            asset_path = os.path.join("attached_assets", asset)
            try:
                if os.path.isfile(asset_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(asset_path))
                    if file_time < cutoff_date:
                        size = os.path.getsize(asset_path)
                        os.remove(asset_path)
                        cleaned += 1
                        self.space_freed += size
                        print(f"✅ Asset eliminado: {asset}")
            except Exception as e:
                print(f"❌ Error con {asset}: {str(e)}")
        
        return cleaned

    def clean_temp_files(self):
        """Limpia archivos temporales seguros"""
        cleaned = 0
        temp_patterns = [
            "/tmp/*",
            "*.tmp",
            "*.temp",
            "__pycache__/*",
            "*.pyc",
            ".pytest_cache/*"
        ]
        
        print(f"\n🗑️ Limpiando archivos temporales...")
        
        for pattern in temp_patterns:
            try:
                files = glob.glob(pattern, recursive=True)
                for file in files:
                    try:
                        if os.path.isfile(file):
                            size = os.path.getsize(file)
                            os.remove(file)
                            cleaned += 1
                            self.space_freed += size
                        elif os.path.isdir(file):
                            size = self.calculate_folder_size(file)
                            shutil.rmtree(file)
                            cleaned += 1
                            self.space_freed += size
                    except:
                        pass
            except:
                pass
        
        if cleaned > 0:
            print(f"✅ Archivos temporales limpiados: {cleaned}")
        
        return cleaned

    def optimize_rocastor_storage(self):
        """Optimiza almacenamiento Rocastor eliminando duplicados"""
        cleaned = 0
        
        # Limpiar PDFs duplicados muy antiguos (más de 60 días)
        pdf_dir = "rocastor_storage/pdfs"
        if os.path.exists(pdf_dir):
            cutoff_date = datetime.now() - timedelta(days=60)
            pdfs = os.listdir(pdf_dir)
            
            for pdf_file in pdfs:
                pdf_path = os.path.join(pdf_dir, pdf_file)
                try:
                    if os.path.isfile(pdf_path):
                        file_time = datetime.fromtimestamp(os.path.getmtime(pdf_path))
                        if file_time < cutoff_date:
                            size = os.path.getsize(pdf_path)
                            os.remove(pdf_path)
                            cleaned += 1
                            self.space_freed += size
                except:
                    pass
        
        if cleaned > 0:
            print(f"✅ PDFs Rocastor antiguos eliminados: {cleaned}")
        
        return cleaned

    def generate_report(self):
        """Genera reporte de limpieza"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "limpieza_realizada": {
                "archivos_eliminados": self.files_cleaned,
                "espacio_liberado_mb": round(self.space_freed / (1024 * 1024), 2),
                "espacio_liberado_gb": round(self.space_freed / (1024 * 1024 * 1024), 3)
            },
            "s3_status": {
                "disponible": self.s3_available,
                "procesos_en_s3": len(self.procesos_en_s3)
            },
            "recomendaciones": [
                "Ejecutar limpieza semanalmente",
                "Verificar que S3 esté siempre configurado",
                "Monitorear espacio en disco regularmente"
            ]
        }
        
        with open("smart_cleanup_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report

    def run_safe_cleanup(self):
        """Ejecuta limpieza segura completa"""
        print("🧹 ===== LIMPIEZA INTELIGENTE INICIADA =====")
        print("🎯 Optimizando espacio sin afectar funcionalidad\n")
        
        # Verificar S3
        self.check_s3_connection()
        
        # Ejecutar limpiezas
        processes_cleaned = self.clean_local_processes_in_s3()
        checkpoints_cleaned = self.clean_old_checkpoints()
        assets_cleaned = self.clean_old_assets()
        temp_cleaned = self.clean_temp_files()
        rocastor_cleaned = self.optimize_rocastor_storage()
        
        self.files_cleaned = processes_cleaned + checkpoints_cleaned + assets_cleaned + temp_cleaned + rocastor_cleaned
        
        # Generar reporte
        report = self.generate_report()
        
        print(f"\n🎉 ===== LIMPIEZA COMPLETADA =====")
        print(f"📊 Total eliminado: {self.files_cleaned} elementos")
        print(f"💾 Espacio liberado: {report['limpieza_realizada']['espacio_liberado_mb']:.2f} MB")
        print(f"📄 Reporte: smart_cleanup_report.json")
        print(f"✅ Editor de Replit optimizado!")

def main():
    cleanup = SmartCleanup()
    
    print("¿Ejecutar limpieza inteligente? (y/N): ", end="")
    respuesta = input().strip().lower()
    
    if respuesta in ['y', 'yes', 'sí', 'si']:
        cleanup.run_safe_cleanup()
    else:
        print("❌ Limpieza cancelada")

if __name__ == "__main__":
    main()
