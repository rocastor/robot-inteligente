
#!/usr/bin/env python3
"""
🔗 Obtener Links Directos de Google Drive - Robot AI
Script para obtener enlaces directos a archivos almacenados en Google Drive
"""

import os
import json
from datetime import datetime
from modules.google_drive_client import get_drive_client

def get_all_drive_links():
    """Obtiene todos los links de archivos en Google Drive"""
    print("🔗 ===== LINKS DIRECTOS DE GOOGLE DRIVE =====\n")
    
    try:
        # Obtener cliente de Google Drive
        drive_client = get_drive_client()
        if not drive_client:
            print("❌ No se pudo conectar a Google Drive")
            return
        
        print(f"✅ Conectado a Google Drive")
        print(f"📁 Carpeta principal ID: {drive_client.folder_id}")
        
        # Obtener todos los archivos en la carpeta principal
        print("\n📋 ===== ARCHIVOS EN CARPETA PRINCIPAL =====")
        main_files = drive_client.list_files()
        
        all_links = []
        
        for file_info in main_files:
            file_data = {
                'name': file_info['name'],
                'id': file_info['id'],
                'size': int(file_info.get('size', 0)),
                'modified': file_info.get('modifiedTime', ''),
                'type': file_info.get('mimeType', ''),
                'web_view_link': file_info.get('webViewLink', ''),
                'location': 'Carpeta Principal'
            }
            all_links.append(file_data)
            
            print(f"📄 {file_info['name']}")
            print(f"   🆔 ID: {file_info['id']}")
            print(f"   🔗 Link directo: {file_info.get('webViewLink', 'No disponible')}")
            print(f"   💾 Tamaño: {int(file_info.get('size', 0))/1024:.1f} KB")
            print()
        
        # Buscar en subcarpetas (Robot_AI_Procesos, etc.)
        print("\n📂 ===== BUSCANDO EN SUBCARPETAS =====")
        
        # Buscar carpetas
        folders_query = f"'{drive_client.folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
        folders_result = drive_client.service.files().list(q=folders_query).execute()
        folders = folders_result.get('files', [])
        
        for folder in folders:
            print(f"\n📁 Carpeta: {folder['name']} (ID: {folder['id']})")
            
            # Listar archivos en esta carpeta
            folder_files = drive_client.list_files(folder['id'])
            
            for file_info in folder_files:
                file_data = {
                    'name': file_info['name'],
                    'id': file_info['id'],
                    'size': int(file_info.get('size', 0)),
                    'modified': file_info.get('modifiedTime', ''),
                    'type': file_info.get('mimeType', ''),
                    'web_view_link': file_info.get('webViewLink', ''),
                    'location': f"Carpeta: {folder['name']}"
                }
                all_links.append(file_data)
                
                print(f"   📄 {file_info['name']}")
                print(f"      🆔 ID: {file_info['id']}")
                print(f"      🔗 Link directo: {file_info.get('webViewLink', 'No disponible')}")
                print(f"      💾 Tamaño: {int(file_info.get('size', 0))/1024:.1f} KB")
            
            # Buscar subcarpetas dentro de esta carpeta
            subfolders_query = f"'{folder['id']}' in parents and mimeType='application/vnd.google-apps.folder'"
            subfolders_result = drive_client.service.files().list(q=subfolders_query).execute()
            subfolders = subfolders_result.get('files', [])
            
            for subfolder in subfolders:
                print(f"\n   📁 Subcarpeta: {subfolder['name']} (ID: {subfolder['id']})")
                
                subfolder_files = drive_client.list_files(subfolder['id'])
                for file_info in subfolder_files:
                    file_data = {
                        'name': file_info['name'],
                        'id': file_info['id'],
                        'size': int(file_info.get('size', 0)),
                        'modified': file_info.get('modifiedTime', ''),
                        'type': file_info.get('mimeType', ''),
                        'web_view_link': file_info.get('webViewLink', ''),
                        'location': f"Carpeta: {folder['name']} > {subfolder['name']}"
                    }
                    all_links.append(file_data)
                    
                    print(f"      📄 {file_info['name']}")
                    print(f"         🆔 ID: {file_info['id']}")
                    print(f"         🔗 Link directo: {file_info.get('webViewLink', 'No disponible')}")
                    print(f"         💾 Tamaño: {int(file_info.get('size', 0))/1024:.1f} KB")
        
        # Generar reporte HTML con links
        html_content = generate_html_report(all_links)
        
        with open('drive_links_report.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Generar reporte JSON
        json_report = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(all_links),
            'files': all_links,
            'drive_folder_id': drive_client.folder_id
        }
        
        with open('drive_links_report.json', 'w', encoding='utf-8') as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 ===== RESUMEN =====")
        print(f"📄 Total archivos encontrados: {len(all_links)}")
        print(f"📁 Carpeta principal Google Drive: https://drive.google.com/drive/folders/{drive_client.folder_id}")
        print(f"📋 Reporte HTML generado: drive_links_report.html")
        print(f"📋 Reporte JSON generado: drive_links_report.json")
        
        # Mostrar links más importantes
        print(f"\n🔗 ===== LINKS MÁS IMPORTANTES =====")
        analysis_files = [f for f in all_links if 'analisis' in f['name'].lower()]
        for file_data in analysis_files[:5]:
            print(f"📄 {file_data['name']}")
            print(f"   🔗 {file_data['web_view_link']}")
            print()
        
        return all_links
        
    except Exception as e:
        print(f"❌ Error obteniendo links: {str(e)}")
        import traceback
        print(f"📋 Detalles: {traceback.format_exc()}")
        return []

def generate_html_report(files_data):
    """Genera reporte HTML con todos los links"""
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔗 Links Directos Google Drive - Robot AI</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #4a90e2;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .file-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}
        .file-card {{
            border: 1px solid #e1e8ed;
            border-radius: 10px;
            padding: 20px;
            background: #f8f9fa;
            transition: transform 0.2s;
        }}
        .file-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }}
        .file-name {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .file-info {{
            font-size: 0.9em;
            color: #7f8c8d;
            margin-bottom: 15px;
        }}
        .link-button {{
            display: inline-block;
            background: #4a90e2;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }}
        .link-button:hover {{
            background: #357abd;
        }}
        .location {{
            background: #e74c3c;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            display: inline-block;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 Links Directos Google Drive</h1>
        <p style="text-align: center; color: #7f8c8d; margin-bottom: 30px;">
            Generado el {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
        </p>
        
        <div class="stats">
            <div class="stat-card">
                <h3>📄 Total Archivos</h3>
                <p style="font-size: 2em; margin: 0;">{len(files_data)}</p>
            </div>
            <div class="stat-card">
                <h3>💾 Tamaño Total</h3>
                <p style="font-size: 2em; margin: 0;">{sum(f['size'] for f in files_data)/1024/1024:.1f} MB</p>
            </div>
        </div>
        
        <div class="file-grid">
"""
    
    for file_data in files_data:
        file_size_mb = file_data['size'] / 1024 / 1024
        modified_date = file_data['modified'][:10] if file_data['modified'] else 'N/A'
        
        html += f"""
            <div class="file-card">
                <div class="location">{file_data['location']}</div>
                <div class="file-name">📄 {file_data['name']}</div>
                <div class="file-info">
                    💾 Tamaño: {file_size_mb:.2f} MB<br>
                    📅 Modificado: {modified_date}<br>
                    🆔 ID: {file_data['id']}
                </div>
                <a href="{file_data['web_view_link']}" target="_blank" class="link-button">
                    🔗 Abrir en Google Drive
                </a>
            </div>
"""
    
    html += """
        </div>
    </div>
</body>
</html>
"""
    return html

if __name__ == "__main__":
    get_all_drive_links()
