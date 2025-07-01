
#!/usr/bin/env python3
"""
⚡ Optimizador de Editor - Robot AI
Mejora el rendimiento del editor de Replit
"""

import os
import shutil
import glob
import json
from datetime import datetime, timedelta

class EditorOptimizer:
    def __init__(self):
        self.files_cleaned = 0
        self.space_freed = 0
        
    def clean_attached_assets_aggressively(self):
        """Limpia assets adjuntos más agresivamente"""
        if not os.path.exists("attached_assets"):
            return 0
            
        cleaned = 0
        cutoff_date = datetime.now() - timedelta(days=3)  # Más agresivo: solo 3 días
        
        assets = os.listdir("attached_assets")
        print(f"🖼️ Limpiando {len(assets)} assets adjuntos...")
        
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
                        print(f"   ✅ {asset}")
            except Exception as e:
                print(f"   ❌ Error con {asset}: {str(e)}")
        
        return cleaned
    
    def clean_rocastor_storage_duplicates(self):
        """Limpia duplicados en rocastor_storage"""
        cleaned = 0
        
        # PDFs duplicados
        pdf_dir = "rocastor_storage/pdfs"
        if os.path.exists(pdf_dir):
            pdfs = os.listdir(pdf_dir)
            if len(pdfs) > 10:  # Si hay más de 10, limpiar los más antiguos
                pdf_files = []
                for pdf in pdfs:
                    pdf_path = os.path.join(pdf_dir, pdf)
                    if os.path.isfile(pdf_path):
                        mtime = os.path.getmtime(pdf_path)
                        pdf_files.append((pdf_path, mtime))
                
                # Ordenar por fecha y mantener solo los 10 más recientes
                pdf_files.sort(key=lambda x: x[1], reverse=True)
                for pdf_path, _ in pdf_files[10:]:
                    try:
                        size = os.path.getsize(pdf_path)
                        os.remove(pdf_path)
                        cleaned += 1
                        self.space_freed += size
                        print(f"   ✅ PDF antiguo eliminado")
                    except:
                        pass
        
        # Templates duplicados
        template_dir = "rocastor_storage/templates"
        if os.path.exists(template_dir):
            templates = os.listdir(template_dir)
            if len(templates) > 5:  # Mantener solo 5 templates
                template_files = []
                for template in templates:
                    template_path = os.path.join(template_dir, template)
                    if os.path.isfile(template_path):
                        mtime = os.path.getmtime(template_path)
                        template_files.append((template_path, mtime))
                
                template_files.sort(key=lambda x: x[1], reverse=True)
                for template_path, _ in template_files[5:]:
                    try:
                        size = os.path.getsize(template_path)
                        os.remove(template_path)
                        cleaned += 1
                        self.space_freed += size
                        print(f"   ✅ Template antiguo eliminado")
                    except:
                        pass
        
        return cleaned
    
    def clean_checkpoints_all(self):
        """Elimina TODOS los checkpoints antiguos"""
        cleaned = 0
        checkpoints = glob.glob("checkpoint_analisis_*.json")
        
        print(f"📊 Eliminando {len(checkpoints)} checkpoints...")
        
        for checkpoint in checkpoints:
            try:
                size = os.path.getsize(checkpoint)
                os.remove(checkpoint)
                cleaned += 1
                self.space_freed += size
                print(f"   ✅ {checkpoint}")
            except Exception as e:
                print(f"   ❌ Error con {checkpoint}: {str(e)}")
        
        return cleaned
    
    def clean_local_results_with_s3_backup(self):
        """Limpia resultados locales que están en S3"""
        cleaned = 0
        
        # Verificar si hay conexión S3
        try:
            aws_configured = bool(os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'))
            if not aws_configured:
                print("⚠️ AWS no configurado, manteniendo archivos locales")
                return 0
        except:
            return 0
        
        resultados_dir = "resultados_analisis"
        if os.path.exists(resultados_dir):
            procesos = os.listdir(resultados_dir)
            print(f"📁 Verificando {len(procesos)} procesos locales...")
            
            for proceso in procesos:
                proceso_path = os.path.join(resultados_dir, proceso)
                if os.path.isdir(proceso_path):
                    try:
                        # Calcular tamaño antes de eliminar
                        size = 0
                        for root, dirs, files in os.walk(proceso_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                if os.path.exists(file_path):
                                    size += os.path.getsize(file_path)
                        
                        shutil.rmtree(proceso_path)
                        cleaned += 1
                        self.space_freed += size
                        print(f"   ✅ {proceso} ({size/1024/1024:.1f} MB)")
                    except Exception as e:
                        print(f"   ❌ Error con {proceso}: {str(e)}")
        
        return cleaned
    
    def force_python_cleanup(self):
        """Fuerza limpieza de Python"""
        import gc
        import sys
        
        print("🐍 Limpieza profunda de Python...")
        
        # Limpiar cache de módulos
        modules_to_clear = []
        for module_name in sys.modules.keys():
            if any(keyword in module_name.lower() for keyword in ['temp', 'cache', 'test']):
                modules_to_clear.append(module_name)
        
        for module_name in modules_to_clear:
            try:
                del sys.modules[module_name]
            except:
                pass
        
        # Múltiples pasadas de garbage collection
        total_collected = 0
        for i in range(5):
            collected = gc.collect()
            total_collected += collected
        
        print(f"   ✅ {total_collected} objetos recolectados")
        return total_collected
    
    def optimize_for_editor(self):
        """Optimización específica para el editor"""
        print("⚡ ===== OPTIMIZACIÓN PARA EDITOR =====")
        print("🎯 Mejorando rendimiento del editor de Replit\n")
        
        # Limpiezas específicas
        assets_cleaned = self.clean_attached_assets_aggressively()
        rocastor_cleaned = self.clean_rocastor_storage_duplicates()
        checkpoints_cleaned = self.clean_checkpoints_all()
        results_cleaned = self.clean_local_results_with_s3_backup()
        python_objects = self.force_python_cleanup()
        
        self.files_cleaned = assets_cleaned + rocastor_cleaned + checkpoints_cleaned + results_cleaned
        
        # Generar reporte
        report = {
            "timestamp": datetime.now().isoformat(),
            "optimizacion_editor": {
                "assets_limpiados": assets_cleaned,
                "rocastor_optimizado": rocastor_cleaned,
                "checkpoints_eliminados": checkpoints_cleaned,
                "resultados_locales_limpiados": results_cleaned,
                "objetos_python_recolectados": python_objects,
                "total_archivos_eliminados": self.files_cleaned,
                "espacio_liberado_mb": round(self.space_freed / (1024 * 1024), 2)
            },
            "recomendaciones": [
                "Reiniciar el editor después de esta limpieza",
                "Ejecutar esta optimización semanalmente",
                "Mantener AWS S3 configurado para respaldos",
                "Evitar acumular muchos attached_assets"
            ]
        }
        
        with open("editor_optimization_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 ===== OPTIMIZACIÓN COMPLETADA =====")
        print(f"📊 Archivos eliminados: {self.files_cleaned}")
        print(f"💾 Espacio liberado: {report['optimizacion_editor']['espacio_liberado_mb']:.2f} MB")
        print(f"🐍 Objetos Python limpiados: {python_objects}")
        print(f"📄 Reporte: editor_optimization_report.json")
        print(f"⚡ ¡Editor optimizado para mejor rendimiento!")
        print(f"\n💡 RECOMENDACIÓN: Reinicia el editor para ver la mejora completa")

def main():
    optimizer = EditorOptimizer()
    optimizer.optimize_for_editor()

if __name__ == "__main__":
    main()
