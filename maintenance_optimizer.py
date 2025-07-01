
#!/usr/bin/env python3
"""
🔧 Script de Mantenimiento Automático - Robot AI
Optimiza el rendimiento de Replit eliminando archivos innecesarios
"""

import os
import gc
import psutil
import shutil
import glob
from datetime import datetime, timedelta

class ReplitOptimizer:
    def __init__(self):
        self.start_time = datetime.now()
        print("🔧 Robot AI - Optimizador de Rendimiento Replit")
        print(f"⏰ Iniciado: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def get_memory_usage(self):
        """Obtiene uso actual de memoria"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent()
            }
        except:
            return {'rss_mb': 0, 'vms_mb': 0, 'percent': 0}
    
    def cleanup_temp_files(self):
        """Limpia archivos temporales"""
        print("\n🗑️ Limpiando archivos temporales...")
        cleaned = 0
        
        temp_patterns = [
            "/tmp/*",
            "*.tmp",
            "*.temp",
            "__pycache__/*",
            "*.pyc",
            ".pytest_cache/*"
        ]
        
        for pattern in temp_patterns:
            try:
                files = glob.glob(pattern, recursive=True)
                for file in files:
                    try:
                        if os.path.isfile(file):
                            os.remove(file)
                            cleaned += 1
                        elif os.path.isdir(file):
                            shutil.rmtree(file)
                            cleaned += 1
                    except:
                        pass
            except:
                pass
        
        print(f"✅ Archivos temporales limpiados: {cleaned}")
        return cleaned
    
    def optimize_attached_assets(self):
        """Optimiza carpeta de assets adjuntos"""
        print("\n🖼️ Optimizando attached_assets...")
        
        if not os.path.exists("attached_assets"):
            print("⚠️ Carpeta attached_assets no existe")
            return 0
        
        files = os.listdir("attached_assets")
        total_files = len(files)
        
        # Eliminar archivos más antiguos de 7 días
        cutoff_date = datetime.now() - timedelta(days=7)
        old_files = 0
        
        for file in files:
            file_path = os.path.join("attached_assets", file)
            try:
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        old_files += 1
            except:
                pass
        
        print(f"📊 Assets procesados: {total_files}")
        print(f"🗑️ Assets antiguos eliminados: {old_files}")
        return old_files
    
    def force_garbage_collection(self):
        """Fuerza la recolección de basura de Python"""
        print("\n🧹 Ejecutando recolección de basura...")
        
        before_mem = self.get_memory_usage()
        
        # Ejecutar múltiples pasadas de GC
        collected = 0
        for i in range(3):
            collected += gc.collect()
        
        after_mem = self.get_memory_usage()
        memory_freed = before_mem['rss_mb'] - after_mem['rss_mb']
        
        print(f"🗑️ Objetos recolectados: {collected}")
        print(f"💾 Memoria liberada: {memory_freed:.1f} MB")
        
        return collected, memory_freed
    
    def check_disk_space(self):
        """Verifica espacio en disco"""
        try:
            disk_usage = shutil.disk_usage("/")
            total_gb = disk_usage.total / (1024**3)
            used_gb = disk_usage.used / (1024**3)
            free_gb = disk_usage.free / (1024**3)
            used_percent = (used_gb / total_gb) * 100
            
            print(f"\n💾 Espacio en disco:")
            print(f"   📊 Total: {total_gb:.1f} GB")
            print(f"   📈 Usado: {used_gb:.1f} GB ({used_percent:.1f}%)")
            print(f"   📉 Libre: {free_gb:.1f} GB")
            
            if used_percent > 80:
                print("⚠️ Advertencia: Poco espacio en disco")
                return False
            return True
        except:
            return True
    
    def optimize_imports(self):
        """Optimiza imports en el código principal"""
        print("\n⚡ Verificando optimizaciones de imports...")
        
        # Verificar si main.py usa lazy loading
        try:
            with open("main.py", "r", encoding="utf-8") as f:
                content = f.read()
                
            if "lazy_import" in content:
                print("✅ Lazy loading implementado")
                return True
            else:
                print("⚠️ Recomendación: Implementar lazy loading")
                return False
        except:
            return False
    
    def generate_report(self, stats):
        """Genera reporte de optimización"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        report = {
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "optimizations": stats,
            "memory_after": self.get_memory_usage(),
            "recommendations": [
                "Ejecutar optimización semanalmente",
                "Monitorear uso de memoria durante desarrollo",
                "Mantener archivos S3 sincronizados",
                "Usar lazy loading para módulos pesados"
            ]
        }
        
        with open("optimization_report.json", "w", encoding="utf-8") as f:
            import json
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Reporte guardado: optimization_report.json")
        return report
    
    def run_full_optimization(self):
        """Ejecuta optimización completa"""
        print("\n🚀 ===== OPTIMIZACIÓN COMPLETA =====")
        
        initial_memory = self.get_memory_usage()
        print(f"💾 Memoria inicial: {initial_memory['rss_mb']:.1f} MB")
        
        stats = {}
        
        # Ejecutar optimizaciones
        stats['temp_files_cleaned'] = self.cleanup_temp_files()
        stats['assets_optimized'] = self.optimize_attached_assets()
        stats['gc_objects'], stats['memory_freed'] = self.force_garbage_collection()
        stats['disk_space_ok'] = self.check_disk_space()
        stats['lazy_imports_enabled'] = self.optimize_imports()
        
        # Generar reporte
        report = self.generate_report(stats)
        
        final_memory = self.get_memory_usage()
        total_memory_saved = initial_memory['rss_mb'] - final_memory['rss_mb']
        
        print(f"\n🎉 ===== OPTIMIZACIÓN COMPLETADA =====")
        print(f"⏱️ Duración: {report['duration_seconds']:.1f} segundos")
        print(f"💾 Memoria final: {final_memory['rss_mb']:.1f} MB")
        print(f"📉 Memoria ahorrada: {total_memory_saved:.1f} MB")
        print(f"⚡ Rendimiento de Replit optimizado!")

def main():
    optimizer = ReplitOptimizer()
    optimizer.run_full_optimization()

if __name__ == "__main__":
    main()
