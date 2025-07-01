
#!/usr/bin/env python3
"""
🚀 Script de Configuración Inicial - Robot AI
Configura automáticamente el robot para funcionar en cualquier entorno
"""

import os
import json
import sys
from pathlib import Path

def main():
    print("🤖 ===== CONFIGURACIÓN INICIAL ROBOT AI =====\n")
    
    print("Este script te ayudará a configurar Robot AI para que funcione")
    print("perfectamente en cualquier entorno (Replit, servidor local, etc.)\n")
    
    # Verificar si ya existe configuración
    config_file = Path('config.json')
    if config_file.exists():
        print("⚠️ Ya existe un archivo config.json")
        overwrite = input("¿Deseas sobrescribirlo? (s/N): ").lower()
        if overwrite != 's':
            print("❌ Configuración cancelada")
            return
    
    config = {}
    
    # Configurar OpenAI
    print("🔧 ===== CONFIGURACIÓN OPENAI =====")
    print("Necesitas una API Key de OpenAI para el análisis con IA")
    print("Obtén tu API Key en: https://platform.openai.com/api-keys\n")
    
    openai_key = input("Introduce tu OpenAI API Key (sk-...): ").strip()
    if openai_key and openai_key.startswith('sk-'):
        config['openai_api_key'] = openai_key
        print("✅ OpenAI API Key configurado")
    else:
        print("⚠️ API Key no válido, puedes configurarlo después")
    
    print("\n🔧 ===== CONFIGURACIÓN GOOGLE DRIVE =====")
    print("Google Drive es el almacenamiento principal del robot")
    print("Necesitas credenciales de Service Account de Google Cloud\n")
    
    print("Opciones para Google Drive:")
    print("1. Pegar JSON completo de Service Account")
    print("2. Usar archivo JSON existente")
    print("3. Configurar después")
    
    option = input("\nSelecciona una opción (1-3): ").strip()
    
    if option == "1":
        print("\nPega el contenido JSON completo de tu Service Account:")
        print("(El JSON debe empezar con { y terminar con })")
        json_content = ""
        while True:
            line = input()
            json_content += line
            if line.strip().endswith('}'):
                break
        
        try:
            google_creds = json.loads(json_content)
            if google_creds.get('type') == 'service_account':
                config['google_credentials'] = google_creds
                print("✅ Google Drive Service Account configurado")
            else:
                print("❌ El JSON no es un Service Account válido")
        except json.JSONDecodeError:
            print("❌ JSON inválido")
    
    elif option == "2":
        json_files = list(Path('.').glob('*.json'))
        if json_files:
            print("\nArchivos JSON encontrados:")
            for i, file in enumerate(json_files, 1):
                print(f"{i}. {file.name}")
            
            try:
                file_idx = int(input("Selecciona el archivo (número): ")) - 1
                selected_file = json_files[file_idx]
                
                with open(selected_file, 'r') as f:
                    google_creds = json.load(f)
                
                if google_creds.get('type') == 'service_account':
                    config['google_credentials'] = google_creds
                    print(f"✅ Google Drive configurado desde {selected_file.name}")
                else:
                    print("❌ El archivo no contiene un Service Account válido")
            except (ValueError, IndexError, FileNotFoundError, json.JSONDecodeError):
                print("❌ Error procesando el archivo")
        else:
            print("❌ No se encontraron archivos JSON")
    
    # Guardar configuración
    if config:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Configuración guardada en config.json")
        
        # Verificar configuración
        print("\n🔍 ===== VERIFICACIÓN =====")
        if 'openai_api_key' in config:
            print("✅ OpenAI configurado")
        else:
            print("⚠️ OpenAI no configurado")
        
        if 'google_credentials' in config:
            print("✅ Google Drive configurado")
        else:
            print("⚠️ Google Drive no configurado")
        
        print(f"\n🚀 Robot AI está listo para funcionar!")
        print(f"Ejecuta: python main.py")
        
    else:
        print("⚠️ No se guardó ninguna configuración")
    
    print("\n📋 ===== INFORMACIÓN ADICIONAL =====")
    print("El robot buscará configuración en este orden:")
    print("1. Variables de entorno (OPENAI_API_KEY, GOOGLE_CREDENTIALS)")
    print("2. Archivo config.json")
    print("3. Archivos JSON individuales")
    print("4. Replit Secrets (si estás en Replit)")
    
    print(f"\n💡 Para máxima portabilidad, usa config.json")
    print(f"💡 Mantén tus credenciales seguras y no las subas a repositorios públicos")

if __name__ == "__main__":
    main()
