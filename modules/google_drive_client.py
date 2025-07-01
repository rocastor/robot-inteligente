
"""
🤖 Módulo de Google Drive - Almacenamiento Económico
Maneja la subida, descarga y gestión de archivos en Google Drive
"""

import os
import json
import io
import pickle
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

# Alcances necesarios para Google Drive con service account
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
]

class GoogleDriveClient:
    def __init__(self, service=None, credentials=None):
        self.service = service
        self.folder_id = None
        self.credentials = credentials
        if service and credentials:
            self.initialize_folder()

    def initialize_folder(self):
        """Inicializa la carpeta raíz para Robot AI"""
        try:
            # Crear carpeta raíz para Robot AI
            self.folder_id = self.create_or_get_folder('Robot_AI_Resultados')

            print(f"✅ Cliente de Google Drive inicializado correctamente")
            print(f"📁 Carpeta principal ID: {self.folder_id}")

        except Exception as e:
            print(f"❌ Error inicializando carpeta en Google Drive: {str(e)}")

    def create_or_get_folder(self, folder_name, parent_id=None):
        """Crea o obtiene una carpeta en Google Drive"""
        try:
            # Si no se especifica parent_id, usar el folder_id por defecto
            target_parent = parent_id or self.folder_id
            
            # Buscar si la carpeta ya existe
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if target_parent:
                query += f" and '{target_parent}' in parents"
            else:
                query += " and 'root' in parents"

            results = self.service.files().list(q=query).execute()
            items = results.get('files', [])

            if items:
                print(f"📁 Carpeta existente encontrada: {folder_name} (Parent: {target_parent})")
                return items[0]['id']

            # Crear nueva carpeta
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            if target_parent:
                folder_metadata['parents'] = [target_parent]

            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()

            folder_id = folder.get('id')
            print(f"✅ Nueva carpeta creada: {folder_name} (ID: {folder_id}, Parent: {target_parent})")
            return folder_id

        except Exception as e:
            print(f"❌ Error creando carpeta {folder_name} en parent {target_parent}: {str(e)}")
            return None

    def upload_file(self, file_path, drive_filename, folder_id=None, metadata=None):
        """Sube un archivo a Google Drive"""
        try:
            if not os.path.exists(file_path):
                print(f"❌ Archivo no encontrado: {file_path}")
                return None

            target_folder = folder_id or self.folder_id
            if not target_folder:
                print("❌ No hay carpeta de destino configurada")
                return None

            print(f"⬆️ Subiendo archivo: {drive_filename}")

            # Determinar tipo de contenido
            file_extension = os.path.splitext(file_path)[1].lower()
            content_types = {
                '.pdf': 'application/pdf',
                '.json': 'application/json',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.zip': 'application/zip',
                '.txt': 'text/plain'
            }

            mime_type = content_types.get(file_extension, 'application/octet-stream')

            # Metadatos del archivo
            file_metadata = {
                'name': drive_filename,
                'parents': [target_folder],
                'description': f"Subido por Robot AI - {datetime.now().isoformat()}"
            }

            if metadata:
                file_metadata['description'] += f" | {json.dumps(metadata)}"

            # Subir archivo
            media = MediaFileUpload(file_path, mimetype=mime_type)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,webViewLink,webContentLink'
            ).execute()

            file_size = os.path.getsize(file_path)
            print(f"✅ Archivo subido exitosamente:")
            print(f"   📄 Nombre: {drive_filename}")
            print(f"   🆔 ID: {file.get('id')}")
            print(f"   💾 Tamaño: {file_size/1024:.1f} KB")
            print(f"   🔗 Link: {file.get('webViewLink')}")

            return {
                'id': file.get('id'),
                'name': file.get('name'),
                'size': file.get('size', file_size),
                'web_view_link': file.get('webViewLink'),
                'web_content_link': file.get('webContentLink'),
                'folder_id': target_folder,
                'upload_time': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ Error subiendo archivo {drive_filename}: {str(e)}")
            return None

    def upload_from_content(self, content, filename, folder_id=None, content_type='application/octet-stream'):
        """Sube contenido directamente a Google Drive sin archivo local"""
        try:
            target_folder = folder_id or self.folder_id
            if not target_folder:
                print("❌ No hay carpeta de destino configurada")
                return None

            print(f"⬆️ Subiendo contenido: {filename}")

            # Preparar contenido
            if isinstance(content, str):
                content_bytes = content.encode('utf-8')
            else:
                content_bytes = content

            # Metadatos del archivo
            file_metadata = {
                'name': filename,
                'parents': [target_folder],
                'description': f"Subido por Robot AI - {datetime.now().isoformat()}"
            }

            # Crear media desde contenido en memoria
            media = MediaIoBaseUpload(
                io.BytesIO(content_bytes), 
                mimetype=content_type
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,webViewLink,webContentLink'
            ).execute()

            print(f"✅ Contenido subido exitosamente:")
            print(f"   📄 Nombre: {filename}")
            print(f"   🆔 ID: {file.get('id')}")
            print(f"   💾 Tamaño: {len(content_bytes)/1024:.1f} KB")

            return {
                'id': file.get('id'),
                'name': file.get('name'),
                'size': len(content_bytes),
                'web_view_link': file.get('webViewLink'),
                'web_content_link': file.get('webContentLink'),
                'folder_id': target_folder,
                'upload_time': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ Error subiendo contenido {filename}: {str(e)}")
            return None

    def download_file(self, file_id, local_path=None):
        """Descarga un archivo de Google Drive"""
        try:
            print(f"⬇️ Descargando archivo ID: {file_id}")

            # Obtener información del archivo
            file_info = self.service.files().get(fileId=file_id).execute()
            filename = file_info['name']

            if not local_path:
                local_path = filename

            # Descargar archivo
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    print(f"   📊 Descarga {int(status.progress() * 100)}%")

            # Guardar archivo localmente
            with open(local_path, 'wb') as f:
                f.write(fh.getvalue())

            print(f"✅ Archivo descargado: {filename} -> {local_path}")
            return local_path

        except Exception as e:
            print(f"❌ Error descargando archivo {file_id}: {str(e)}")
            return None

    def get_file_content(self, file_id):
        """Obtiene el contenido de un archivo sin guardarlo localmente"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while done is False:
                status, done = downloader.next_chunk()

            content = fh.getvalue()
            print(f"✅ Contenido obtenido: {len(content)} bytes")
            return content

        except Exception as e:
            print(f"❌ Error obteniendo contenido {file_id}: {str(e)}")
            return None

    def list_files(self, folder_id=None, query=None):
        """Lista archivos en una carpeta"""
        try:
            target_folder = folder_id or self.folder_id

            if query:
                search_query = query
            else:
                search_query = f"'{target_folder}' in parents and trashed=false"

            results = self.service.files().list(
                q=search_query,
                fields="nextPageToken, files(id,name,size,modifiedTime,mimeType,webViewLink)"
            ).execute()

            items = results.get('files', [])
            print(f"📋 Encontrados {len(items)} archivos")

            return items

        except Exception as e:
            print(f"❌ Error listando archivos: {str(e)}")
            return []

    def delete_file(self, file_id):
        """Elimina un archivo de Google Drive"""
        try:
            self.service.files().delete(fileId=file_id).execute()
            print(f"🗑️ Archivo eliminado: {file_id}")
            return True
        except Exception as e:
            print(f"❌ Error eliminando archivo {file_id}: {str(e)}")
            return False

    def upload_process_folder(self, process_name, files_data, original_folder=None):
        """Sube una carpeta completa de proceso a Google Drive"""
        try:
            print(f"📁 Subiendo proceso completo: {process_name}")

            # Crear estructura de carpetas
            if original_folder:
                # procesos/carpeta_original/nombre_proceso/
                original_folder_id = self.create_or_get_folder(original_folder, self.folder_id)
                process_folder_id = self.create_or_get_folder(process_name, original_folder_id)
            else:
                # procesos/nombre_proceso/
                process_folder_id = self.create_or_get_folder(process_name, self.folder_id)

            uploaded_files = []

            for file_data in files_data:
                if 'file_path' in file_data:
                    # Subir desde archivo local
                    result = self.upload_file(
                        file_data['file_path'],
                        file_data['filename'],
                        process_folder_id,
                        file_data.get('metadata')
                    )
                elif 'content' in file_data:
                    # Subir desde contenido en memoria
                    result = self.upload_from_content(
                        file_data['content'],
                        file_data['filename'],
                        process_folder_id,
                        file_data.get('content_type', 'application/octet-stream')
                    )

                if result:
                    uploaded_files.append(result)

            print(f"✅ Proceso subido: {len(uploaded_files)} archivos")

            return {
                'success': True,
                'process_folder_id': process_folder_id,
                'uploaded_files': uploaded_files,
                'process_name': process_name,
                'original_folder': original_folder
            }

        except Exception as e:
            print(f"❌ Error subiendo proceso: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_storage_quota(self):
        """Obtiene información del espacio usado y disponible"""
        try:
            about = self.service.about().get(fields="storageQuota,user").execute()
            quota = about.get('storageQuota', {})

            total = int(quota.get('limit', 0))
            used = int(quota.get('usage', 0))
            available = total - used

            print(f"💾 Espacio Google Drive:")
            print(f"   Total: {total/1024/1024/1024:.2f} GB")
            print(f"   Usado: {used/1024/1024/1024:.2f} GB")
            print(f"   Disponible: {available/1024/1024/1024:.2f} GB")

            return {
                'total_gb': total/1024/1024/1024,
                'used_gb': used/1024/1024/1024,
                'available_gb': available/1024/1024/1024,
                'usage_percentage': (used/total)*100 if total > 0 else 0
            }

        except Exception as e:
            print(f"❌ Error obteniendo quota: {str(e)}")
            return None

_drive_client = None

def get_drive_client():
    """Obtiene cliente configurado de Google Drive"""
    global _drive_client

    if _drive_client is not None:
        return _drive_client

    try:
        print(f"🔧 Inicializando cliente de Google Drive...")

        # Obtener credenciales desde variable de entorno
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if not credentials_json:
            print("⚠️ GOOGLE_CREDENTIALS no configurado - usando almacenamiento local")
            return None

        print(f"🔐 Autenticando con Google Drive...")

        # Parsear credenciales JSON
        try:
            creds_dict = json.loads(credentials_json)
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando credenciales JSON: {str(e)}")
            return None

        # Validar estructura de credenciales para service account
        if creds_dict.get('type') == 'service_account':
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            if not all(field in creds_dict for field in required_fields):
                print(f"❌ Credenciales de service account incompletas. Campos requeridos: {required_fields}")
                return None

            # MÉTODO CORREGIDO: Crear credenciales sin delegación
            try:
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=SCOPES
                )
                
                # NO llamar refresh() para service accounts - se autentican automáticamente
                print("✅ Credenciales de service account configuradas correctamente")
                
            except Exception as cred_error:
                print(f"❌ Error creando credenciales: {str(cred_error)}")
                return None

        else:
            print(f"❌ Tipo de credenciales no soportado: {creds_dict.get('type')}")
            print(f"💡 Solo se admiten credenciales de tipo 'service_account'")
            return None

        # Construir servicio
        try:
            service = build('drive', 'v3', credentials=credentials)
            print(f"✅ Servicio Google Drive creado exitosamente")
        except Exception as service_error:
            print(f"❌ Error creando servicio Google Drive: {str(service_error)}")
            return None

        # Probar conexión con el método correcto
        try:
            # Test básico de listado sin forzar refresh
            results = service.files().list(pageSize=1, fields="files(id,name)").execute()
            files = results.get('files', [])
            user_email = creds_dict.get('client_email', 'Service Account')
            print(f"✅ Conectado a Google Drive como: {user_email}")
            print(f"📁 Test de conexión exitoso: {len(files)} archivos accesibles")
            
        except Exception as test_error:
            print(f"❌ Error probando conexión a Google Drive: {str(test_error)}")
            print(f"📋 Detalles del error: {type(test_error).__name__}")
            
            # Análisis del error mejorado
            error_str = str(test_error).lower()
            if 'insufficient authentication scopes' in error_str or 'scope' in error_str:
                print(f"💡 Sugerencia: Verificar que el service account tenga los scopes correctos")
                print(f"💡 Scopes requeridos: {SCOPES}")
            elif 'forbidden' in error_str or 'access denied' in error_str:
                print(f"💡 Sugerencia: Verificar permisos del service account en Google Cloud")
            elif 'not found' in error_str:
                print(f"💡 Sugerencia: Verificar que Google Drive API esté habilitada")
            elif 'quota' in error_str:
                print(f"💡 Sugerencia: Verificar límites de cuota de la API")
            
            return None

        # Crear cliente
        _drive_client = GoogleDriveClient(service, credentials)

        print(f"✅ Cliente Google Drive inicializado correctamente")
        print(f"📁 Google Drive listo para almacenar procesos")
        return _drive_client

    except Exception as e:
        print(f"❌ Error inicializando Google Drive: {str(e)}")
        print(f"💡 Asegúrate de que GOOGLE_DRIVE_CREDENTIALS contenga credenciales válidas de service account")
        return None

def test_google_drive_connection():
    """Test de conexión con Google Drive"""
    try:
        print("🔧 Iniciando test de Google Drive...")

        # Verificar credenciales
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if not credentials_json:
            print("❌ GOOGLE_CREDENTIALS no configurado")
            return {
                'success': False,
                'message': 'GOOGLE_CREDENTIALS no configurado'
            }

        print(f"📋 Credenciales encontradas: {len(credentials_json)} caracteres")

        # Validar JSON
        try:
            import json
            creds_data = json.loads(credentials_json)
            print(f"✅ JSON válido - Tipo: {creds_data.get('type', 'unknown')}")

            # Verificar campos requeridos para service account
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in creds_data]

            if missing_fields:
                print(f"❌ Campos faltantes: {missing_fields}")
                return {
                    'success': False,
                    'message': f'Credenciales incompletas. Faltan: {missing_fields}'
                }

            print(f"📧 Service Account: {creds_data.get('client_email', 'unknown')}")
            print(f"📂 Project ID: {creds_data.get('project_id', 'unknown')}")

        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {str(e)}")
            return {
                'success': False,
                'message': f'Credenciales JSON inválidas: {str(e)}'
            }

        # Test directo mejorado
        print("🔧 Creando servicio de prueba directo...")
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            # Crear credenciales sin refresh automático
            test_credentials = service_account.Credentials.from_service_account_info(
                creds_data,
                scopes=SCOPES
            )
            
            # Crear servicio directo
            test_service = build('drive', 'v3', credentials=test_credentials)
            print("✅ Servicio de prueba creado exitosamente")
            
            # Test de conexión mejorado
            print("🔧 Probando conexión con API...")
            results = test_service.files().list(
                pageSize=5, 
                fields="files(id,name,size)"
            ).execute()
            files = results.get('files', [])
            print(f"✅ Test de Google Drive exitoso - {len(files)} archivos accesibles")

            # Test de cuota mejorado
            try:
                about = test_service.about().get(fields='storageQuota,user').execute()
                quota = about.get('storageQuota', {})
                user = about.get('user', {})
                print(f"📊 Información de cuenta obtenida exitosamente")
                print(f"👤 Usuario: {user.get('displayName', 'Service Account')}")
            except Exception as quota_error:
                print(f"⚠️ No se pudo obtener información de cuenta: {str(quota_error)}")

            return {
                'success': True,
                'message': 'Conexión a Google Drive exitosa',
                'details': {
                    'files_accessible': len(files),
                    'service_account': creds_data.get('client_email'),
                    'project_id': creds_data.get('project_id'),
                    'scopes_used': SCOPES
                }
            }
            
        except Exception as e:
            print(f"❌ Error en test directo: {str(e)}")
            print(f"📋 Tipo de error: {type(e).__name__}")

            # Análisis específico del error
            error_str = str(e).lower()
            if 'insufficient authentication scopes' in error_str or 'scope' in error_str:
                return {
                    'success': False,
                    'message': 'Error de scopes: El service account necesita permisos adicionales para Google Drive',
                    'fix_suggestion': 'Verificar que el service account tenga habilitados los scopes de Google Drive'
                }
            elif 'forbidden' in error_str or 'access denied' in error_str:
                return {
                    'success': False,
                    'message': 'Acceso denegado: Verificar que el service account tenga acceso a Google Drive',
                    'fix_suggestion': 'Verificar permisos del service account en Google Cloud Console'
                }
            elif 'not found' in error_str or 'disabled' in error_str:
                return {
                    'success': False,
                    'message': 'API no disponible: Verificar que Google Drive API esté habilitada',
                    'fix_suggestion': 'Habilitar Google Drive API en Google Cloud Console'
                }
            elif 'quota' in error_str or 'limit' in error_str:
                return {
                    'success': False,
                    'message': 'Límite de cuota excedido',
                    'fix_suggestion': 'Verificar límites de cuota en Google Cloud Console'
                }
            else:
                return {
                    'success': False,
                    'message': f'Error de conexión: {str(e)}',
                    'fix_suggestion': 'Verificar credenciales y configuración del service account'
                }

    except Exception as e:
        print(f"❌ Error en test de Google Drive: {str(e)}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return {
            'success': False,
            'message': f'Error en test de conexión: {str(e)}',
            'fix_suggestion': 'Revisar configuración completa de Google Drive'
        }
