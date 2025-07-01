
#!/usr/bin/env python3
"""
📊 Analizador de Espacio - Robot AI
Analiza qué archivos ocupan más espacio
"""

import os
import glob
from datetime import datetime

def get_folder_size(folder_path):
    """Calcula tamaño de carpeta"""
    total_size = 0
    file_count = 0
    try:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1
    except:
        pass
    return total_size, file_count

def analyze_space():
    """Analiza uso de espacio por categorías"""
    
    print("📊 ===== ANÁLISIS DE ESPACIO =====\n")
    
    categories = {
        "Resultados de análisis": "resultados_analisis",
        "Assets adjuntos": "attached_assets", 
        "Almacenamiento Rocastor": "rocastor_storage",
        "Módulos": "modules"
    }
    
    total_space = 0
    
    for category, path in categories.items():
        if os.path.exists(path):
            size, files = get_folder_size(path)
            total_space += size
            print(f"📁 {category}:")
            print(f"   💾 Tamaño: {size/1024/1024:.2f} MB")
            print(f"   📄 Archivos: {files}")
            print()
        else:
            print(f"📁 {category}: No existe\n")
    
    # Analizar archivos individuales grandes
    print("📋 ARCHIVOS INDIVIDUALES GRANDES:")
    large_files = []
    
    for root, dirs, files in os.walk("."):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                size = os.path.getsize(file_path)
                if size > 1024 * 1024:  # Mayor a 1MB
                    large_files.append((file_path, size))
            except:
                pass
    
    large_files.sort(key=lambda x: x[1], reverse=True)
    
    for file_path, size in large_files[:10]:
        print(f"   📄 {file_path}: {size/1024/1024:.2f} MB")
    
    print(f"\n💾 ESPACIO TOTAL ANALIZADO: {total_space/1024/1024:.2f} MB")
    
    # Checkpoints antiguos
    checkpoints = glob.glob("checkpoint_analisis_*.json")
    if checkpoints:
        checkpoint_size = sum(os.path.getsize(f) for f in checkpoints if os.path.exists(f))
        print(f"📊 Checkpoints: {len(checkpoints)} archivos, {checkpoint_size/1024:.1f} KB")
    
    return total_space

if __name__ == "__main__":
    analyze_space()
