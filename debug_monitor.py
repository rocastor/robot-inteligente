
#!/usr/bin/env python3
"""
🔍 Monitor de Debugging - Robot AI
Sistema de monitoreo en tiempo real para identificar errores
"""

import os
import json
import glob
import asyncio
import requests
from datetime import datetime
from typing import Dict, List, Any
import tracebackack

class RobotDebugMonitor:
    def __init__(self):
        self.base_url = "http://0.0.0.0:5000"
        self.test_results = {}
        
    async def run_complete_diagnostics(self):
        """Ejecuta diagnósticos completos del sistema"""
        print("🔍 ===== DIAGNÓSTICOS COMPLETOS DEL ROBOT AI =====\n")
        
        # 1. Test de conectividad básica
        await self.test_api_connectivity()
        
        # 2. Test de configuración
        await self.test_configuration()
        
        # 3. Test de almacenamiento
        await self.test_storage_systems()
        
        # 4. Test de datos locales
        await self.test_local_data()
        
        # 5. Test de Google Drive
        await self.test_google_drive()
        
        # 6. Test de endpoints críticos
        await self.test_critical_endpoints()
        
        # 7. Generar reporte final
        self.generate_final_report()
        
    async def test_api_connectivity(self):
        """Test de conectividad básica con la API"""
        print("🌐 ===== TEST DE CONECTIVIDAD =====")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ API respondiendo correctamente")
                print(f"   📊 Versión: {data.get('version', 'N/A')}")
                print(f"   🔧 OpenAI configurado: {data.get('openai_configured', False)}")
                print(f"   ☁️ Google Drive conectado: {data.get('google_drive_connected', False)}")
                print(f"   📁 Almacenamiento principal: {data.get('almacenamiento_principal', 'N/A')}")
                
                self.test_results['api_connectivity'] = {
                    'status': 'success',
                    'details': data
                }
            else:
                print(f"❌ API respondió con código: {response.status_code}")
                self.test_results['api_connectivity'] = {
                    'status': 'error',
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            print(f"❌ Error conectando con API: {str(e)}")
            self.test_results['api_connectivity'] = {
                'status': 'error',
                'error': str(e)
            }
        
        print()
    
    async def test_configuration(self):
        """Test de configuración del sistema"""
        print("⚙️ ===== TEST DE CONFIGURACIÓN =====")
        
        # Variables de entorno críticas
        env_vars = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
            'GOOGLE_DRIVE_CREDENTIALS': os.getenv('GOOGLE_DRIVE_CREDENTIALS', ''),
            'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID', ''),
            'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY', '')
        }
        
        config_status = {}
        
        for var, value in env_vars.items():
            if value and value != 'tu_api_key_aqui':
                print(f"✅ {var}: Configurado")
                config_status[var] = 'configured'
            else:
                print(f"❌ {var}: No configurado")
                config_status[var] = 'missing'
        
        self.test_results['configuration'] = config_status
        print()
    
    async def test_storage_systems(self):
        """Test de sistemas de almacenamiento"""
        print("💾 ===== TEST DE ALMACENAMIENTO =====")
        
        storage_results = {}
        
        # Test Google Drive
        try:
            response = requests.get(f"{self.base_url}/test-google-drive", timeout=15)
            if response.status_code == 200:
                data = response.json()
                print("✅ Google Drive: Conectado")
                print(f"   📊 Cuota disponible: {data.get('quota_info', {}).get('storage_usage', 'N/A')}")
                storage_results['google_drive'] = 'connected'
            else:
                print("❌ Google Drive: Error de conexión")
                storage_results['google_drive'] = 'error'
        except Exception as e:
            print(f"❌ Google Drive: {str(e)}")
            storage_results['google_drive'] = 'error'
        
        # Test almacenamiento local
        try:
            local_processes = glob.glob("resultados_analisis/proceso_*")
            print(f"📂 Almacenamiento local: {len(local_processes)} procesos encontrados")
            storage_results['local_storage'] = len(local_processes)
        except Exception as e:
            print(f"❌ Almacenamiento local: {str(e)}")
            storage_results['local_storage'] = 0
        
        self.test_results['storage'] = storage_results
        print()
    
    async def test_local_data(self):
        """Test detallado de datos locales"""
        print("📁 ===== TEST DE DATOS LOCALES =====")
        
        local_data = {
            'total_processes': 0,
            'valid_processes': 0,
            'corrupted_processes': 0,
            'process_details': []
        }
        
        try:
            carpetas_procesos = glob.glob("resultados_analisis/proceso_*")
            local_data['total_processes'] = len(carpetas_procesos)
            
            for carpeta in carpetas_procesos:
                if os.path.isdir(carpeta):
                    proceso_name = os.path.basename(carpeta)
                    json_files = glob.glob(os.path.join(carpeta, "analisis_completo.json"))
                    
                    if json_files:
                        try:
                            with open(json_files[0], 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            # Validar estructura
                            required_fields = ['resumen', 'analisis', 'timestamp']
                            is_valid = all(field in data for field in required_fields)
                            
                            if is_valid:
                                local_data['valid_processes'] += 1
                                print(f"✅ {proceso_name}: Válido")
                                
                                resumen = data.get('resumen', {})
                                local_data['process_details'].append({
                                    'name': proceso_name,
                                    'status': 'valid',
                                    'timestamp': data.get('timestamp', ''),
                                    'files_processed': resumen.get('archivos_procesados_exitosamente', 0),
                                    'responses_found': resumen.get('respuestas_con_informacion', 0)
                                })
                            else:
                                local_data['corrupted_processes'] += 1
                                print(f"❌ {proceso_name}: Estructura incompleta")
                                local_data['process_details'].append({
                                    'name': proceso_name,
                                    'status': 'corrupted',
                                    'error': 'Estructura incompleta'
                                })
                        except Exception as e:
                            local_data['corrupted_processes'] += 1
                            print(f"❌ {proceso_name}: Error leyendo JSON - {str(e)}")
                            local_data['process_details'].append({
                                'name': proceso_name,
                                'status': 'corrupted',
                                'error': str(e)
                            })
                    else:
                        local_data['corrupted_processes'] += 1
                        print(f"❌ {proceso_name}: Sin archivo JSON")
                        local_data['process_details'].append({
                            'name': proceso_name,
                            'status': 'corrupted',
                            'error': 'Sin archivo JSON'
                        })
            
            print(f"\n📊 RESUMEN DATOS LOCALES:")
            print(f"   📁 Total procesos: {local_data['total_processes']}")
            print(f"   ✅ Válidos: {local_data['valid_processes']}")
            print(f"   ❌ Corruptos: {local_data['corrupted_processes']}")
            
        except Exception as e:
            print(f"❌ Error analizando datos locales: {str(e)}")
            local_data['error'] = str(e)
        
        self.test_results['local_data'] = local_data
        print()
    
    async def test_google_drive(self):
        """Test específico de Google Drive"""
        print("☁️ ===== TEST DETALLADO DE GOOGLE DRIVE =====")
        
        drive_results = {}
        
        try:
            # Test de conexión
            response = requests.get(f"{self.base_url}/test-google-drive", timeout=15)
            if response.status_code == 200:
                drive_data = response.json()
                print("✅ Conexión establecida")
                
                # Test de archivos
                files_response = requests.get(f"{self.base_url}/drive-files", timeout=15)
                if files_response.status_code == 200:
                    files_data = files_response.json()
                    total_files = files_data.get('total_files', 0)
                    print(f"📄 Archivos encontrados: {total_files}")
                    
                    # Contar procesos en Drive
                    files_list = files_data.get('files', [])
                    json_files = [f for f in files_list if f.get('name', '').endswith('.json')]
                    process_files = [f for f in json_files if 'analisis_completo' in f.get('name', '')]
                    
                    print(f"📊 Archivos de procesos: {len(process_files)}")
                    
                    drive_results = {
                        'connection': 'success',
                        'total_files': total_files,
                        'process_files': len(process_files),
                        'quota_info': drive_data.get('quota_info', {})
                    }
                else:
                    print(f"❌ Error listando archivos: {files_response.status_code}")
                    drive_results = {
                        'connection': 'success',
                        'files_error': files_response.status_code
                    }
            else:
                print(f"❌ Error de conexión: {response.status_code}")
                error_data = response.text
                print(f"   Detalles: {error_data}")
                drive_results = {
                    'connection': 'error',
                    'error_code': response.status_code,
                    'error_details': error_data
                }
        except Exception as e:
            print(f"❌ Excepción en test de Google Drive: {str(e)}")
            drive_results = {
                'connection': 'exception',
                'error': str(e)
            }
        
        self.test_results['google_drive'] = drive_results
        print()
    
    async def test_critical_endpoints(self):
        """Test de endpoints críticos"""
        print("🎯 ===== TEST DE ENDPOINTS CRÍTICOS =====")
        
        endpoints = {
            '/lista-procesos': 'Lista de procesos',
            '/dashboard': 'Dashboard principal',
            '/panel-filtros': 'Panel de filtros',
            '/cargar-pdfs-rocastor': 'PDFs Rocastor'
        }
        
        endpoint_results = {}
        
        for endpoint, description in endpoints.items():
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=15)
                if response.status_code == 200:
                    print(f"✅ {endpoint}: OK ({description})")
                    
                    # Para endpoints de datos, verificar contenido
                    if endpoint == '/lista-procesos':
                        try:
                            data = response.json()
                            total_procesos = data.get('total_procesos', 0)
                            print(f"   📊 Procesos encontrados: {total_procesos}")
                            endpoint_results[endpoint] = {
                                'status': 'success',
                                'data': {'total_procesos': total_procesos}
                            }
                        except:
                            endpoint_results[endpoint] = {
                                'status': 'success',
                                'note': 'Respuesta no JSON'
                            }
                    elif endpoint == '/cargar-pdfs-rocastor':
                        try:
                            data = response.json()
                            total_pdfs = data.get('total', 0)
                            print(f"   📄 PDFs encontrados: {total_pdfs}")
                            endpoint_results[endpoint] = {
                                'status': 'success',
                                'data': {'total_pdfs': total_pdfs}
                            }
                        except:
                            endpoint_results[endpoint] = {
                                'status': 'success',
                                'note': 'Respuesta no JSON'
                            }
                    else:
                        endpoint_results[endpoint] = {'status': 'success'}
                        
                else:
                    print(f"❌ {endpoint}: Error {response.status_code}")
                    endpoint_results[endpoint] = {
                        'status': 'error',
                        'error_code': response.status_code
                    }
            except Exception as e:
                print(f"❌ {endpoint}: Excepción - {str(e)}")
                endpoint_results[endpoint] = {
                    'status': 'exception',
                    'error': str(e)
                }
        
        self.test_results['endpoints'] = endpoint_results
        print()
    
    def generate_final_report(self):
        """Genera reporte final con recomendaciones"""
        print("📋 ===== REPORTE FINAL DE DIAGNÓSTICOS =====\n")
        
        # Análisis de resultados
        issues_found = []
        recommendations = []
        
        # Verificar API
        if self.test_results.get('api_connectivity', {}).get('status') != 'success':
            issues_found.append("API no responde correctamente")
            recommendations.append("Verificar que el servidor esté ejecutándose en puerto 5000")
        
        # Verificar configuración
        config = self.test_results.get('configuration', {})
        if config.get('OPENAI_API_KEY') != 'configured':
            issues_found.append("OpenAI API Key no configurado")
            recommendations.append("Configurar OPENAI_API_KEY en variables de entorno")
        
        if config.get('GOOGLE_DRIVE_CREDENTIALS') != 'configured':
            issues_found.append("Google Drive no configurado")
            recommendations.append("Configurar GOOGLE_DRIVE_CREDENTIALS para almacenamiento")
        
        # Verificar datos
        local_data = self.test_results.get('local_data', {})
        if local_data.get('valid_processes', 0) == 0:
            issues_found.append("No hay procesos válidos localmente")
            recommendations.append("Ejecutar un proceso de prueba para generar datos")
        
        # Verificar Google Drive
        drive_data = self.test_results.get('google_drive', {})
        if drive_data.get('connection') != 'success':
            issues_found.append("Google Drive no conectado")
            recommendations.append("Verificar credenciales de Google Drive")
        
        # Verificar endpoints
        endpoints = self.test_results.get('endpoints', {})
        lista_procesos = endpoints.get('/lista-procesos', {})
        if lista_procesos.get('status') != 'success':
            issues_found.append("Endpoint /lista-procesos no funciona")
            recommendations.append("Revisar logs del servidor para errores en carga de procesos")
        elif lista_procesos.get('data', {}).get('total_procesos', 0) == 0:
            issues_found.append("Lista de procesos retorna 0 procesos")
            recommendations.append("Verificar función de carga de procesos en main.py")
        
        # Mostrar resultados
        if not issues_found:
            print("🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
            print("   El sistema debería estar funcionando correctamente.")
        else:
            print(f"⚠️ SE ENCONTRARON {len(issues_found)} PROBLEMAS:")
            for i, issue in enumerate(issues_found, 1):
                print(f"   {i}. {issue}")
            
            print(f"\n🔧 RECOMENDACIONES PARA SOLUCIONAR:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        # Guardar reporte completo
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'issues_found': len(issues_found),
                'total_tests': len(self.test_results),
                'status': 'healthy' if not issues_found else 'issues_detected'
            },
            'issues': issues_found,
            'recommendations': recommendations,
            'detailed_results': self.test_results
        }
        
        with open('debug_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 Reporte completo guardado en: debug_report.json")
        print("\n🔍 Para ejecutar diagnósticos nuevamente:")
        print("   python debug_monitor.py")

async def main():
    monitor = RobotDebugMonitor()
    await monitor.run_complete_diagnostics()

if __name__ == "__main__":
    asyncio.run(main())
