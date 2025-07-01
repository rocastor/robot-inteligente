
"""
🤖 Módulo de Analytics
Maneja análisis financiero, costos S3 y proyecciones
"""

import os
from datetime import datetime
from aws_s3_utils import listar_archivos_s3, get_s3_client

class S3CostAnalytics:
    """Sistema de análisis de costos específico para AWS S3"""
    
    S3_STORAGE_PRICE_PER_GB_MONTH = 0.023
    S3_REQUEST_PUT_PRICE_PER_1000 = 0.0005
    S3_REQUEST_GET_PRICE_PER_1000 = 0.0004
    S3_DATA_TRANSFER_PRICE_PER_GB = 0.09
    
    @staticmethod
    def calcular_costos_almacenamiento(total_gb, dias_almacenados=30):
        """Calcula costos de almacenamiento S3"""
        meses = dias_almacenados / 30.0
        costo_storage = total_gb * S3CostAnalytics.S3_STORAGE_PRICE_PER_GB_MONTH * meses
        return round(costo_storage, 4)
    
    @staticmethod
    def calcular_costos_requests(put_requests=0, get_requests=0):
        """Calcula costos de requests S3"""
        costo_put = (put_requests / 1000) * S3CostAnalytics.S3_REQUEST_PUT_PRICE_PER_1000
        costo_get = (get_requests / 1000) * S3CostAnalytics.S3_REQUEST_GET_PRICE_PER_1000
        return round(costo_put + costo_get, 4)
    
    @staticmethod
    def calcular_costos_transferencia(gb_transferidos):
        """Calcula costos de transferencia de datos"""
        gb_facturables = max(0, gb_transferidos - 100)
        costo = gb_facturables * S3CostAnalytics.S3_DATA_TRANSFER_PRICE_PER_GB
        return round(costo, 4)
    
    @staticmethod
    async def analizar_costos_s3_completo():
        """Análisis completo de costos S3"""
        try:
            archivos_s3 = listar_archivos_s3("procesos/")
            
            if not archivos_s3:
                return {
                    "error": "No hay archivos en S3 para analizar",
                    "total_files": 0,
                    "estimated_costs": {}
                }
            
            total_archivos = len(archivos_s3)
            total_bytes = sum(archivo.get('tamaño', 0) for archivo in archivos_s3)
            total_gb = total_bytes / (1024**3)
            
            estimated_put_requests = total_archivos
            estimated_get_requests = total_archivos * 0.5
            estimated_transfer_gb = total_gb * 0.1
            
            costo_almacenamiento = S3CostAnalytics.calcular_costos_almacenamiento(total_gb)
            costo_requests = S3CostAnalytics.calcular_costos_requests(
                estimated_put_requests, estimated_get_requests
            )
            costo_transferencia = S3CostAnalytics.calcular_costos_transferencia(estimated_transfer_gb)
            costo_total_estimado = costo_almacenamiento + costo_requests + costo_transferencia
            
            costo_anual_proyectado = costo_total_estimado * 12
            
            procesos_s3 = {}
            for archivo in archivos_s3:
                key = archivo['key']
                if '/procesos/' in key:
                    proceso_name = key.split('/')[2] if len(key.split('/')) > 2 else 'unknown'
                    if proceso_name not in procesos_s3:
                        procesos_s3[proceso_name] = {
                            'archivos': 0,
                            'bytes': 0,
                            'costo_estimado': 0
                        }
                    procesos_s3[proceso_name]['archivos'] += 1
                    procesos_s3[proceso_name]['bytes'] += archivo.get('tamaño', 0)
            
            for proceso_name, data in procesos_s3.items():
                proceso_gb = data['bytes'] / (1024**3)
                proceso_costo = S3CostAnalytics.calcular_costos_almacenamiento(proceso_gb)
                procesos_s3[proceso_name]['costo_estimado'] = proceso_costo
                procesos_s3[proceso_name]['gb'] = round(proceso_gb, 3)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "metricas_s3": {
                    "total_archivos": total_archivos,
                    "total_bytes": total_bytes,
                    "total_gb": round(total_gb, 3),
                    "total_mb": round(total_bytes / (1024**2), 1)
                },
                "costos_estimados_usd": {
                    "almacenamiento_mensual": costo_almacenamiento,
                    "requests_estimados": costo_requests,
                    "transferencia_estimada": costo_transferencia,
                    "total_mensual": round(costo_total_estimado, 4),
                    "total_anual_proyectado": round(costo_anual_proyectado, 4)
                },
                "requests_estimados": {
                    "put_requests": estimated_put_requests,
                    "get_requests": estimated_get_requests,
                    "transfer_gb": round(estimated_transfer_gb, 3)
                },
                "analisis_por_proceso": dict(sorted(
                    procesos_s3.items(), 
                    key=lambda x: x[1]['costo_estimado'], 
                    reverse=True
                )[:10]),
                "precios_referencia": {
                    "storage_per_gb_month": S3CostAnalytics.S3_STORAGE_PRICE_PER_GB_MONTH,
                    "put_per_1000_requests": S3CostAnalytics.S3_REQUEST_PUT_PRICE_PER_1000,
                    "get_per_1000_requests": S3CostAnalytics.S3_REQUEST_GET_PRICE_PER_1000,
                    "transfer_per_gb": S3CostAnalytics.S3_DATA_TRANSFER_PRICE_PER_GB,
                    "fecha_precios": "2025-01"
                },
                "recomendaciones": [
                    f"Costo mensual estimado: ${costo_total_estimado:.4f} USD",
                    f"Almacenamiento: {total_gb:.2f} GB en {total_archivos} archivos",
                    f"Proceso más costoso: {max(procesos_s3.items(), key=lambda x: x[1]['costo_estimado'])[0] if procesos_s3 else 'N/A'}",
                    "Considera limpiar archivos antiguos si el costo supera el presupuesto"
                ]
            }
            
        except Exception as e:
            return {
                "error": f"Error analizando costos S3: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

class FinancialAnalytics:
    """Sistema de análisis financiero para el Robot AI"""
    
    @staticmethod
    def calcular_roi_por_proceso(procesos):
        """Calcula ROI por cada proceso"""
        roi_data = []
        
        for proceso in procesos:
            costo = proceso.get('costo_openai_usd', 0)
            preguntas = proceso.get('preguntas_analizadas', 0)
            respuestas = proceso.get('respuestas_encontradas', 0)
            
            horas_ahorradas = respuestas * 1.0
            valor_hora = 25
            valor_generado = horas_ahorradas * valor_hora
            
            roi = ((valor_generado - costo) / costo * 100) if costo > 0 else 0
            
            roi_data.append({
                'proceso': proceso['nombre_proceso'],
                'costo_usd': costo,
                'valor_generado_usd': valor_generado,
                'roi_porcentaje': round(roi, 2),
                'horas_ahorradas': horas_ahorradas,
                'eficiencia': round((respuestas / preguntas * 100) if preguntas > 0 else 0, 1)
            })
        
        return sorted(roi_data, key=lambda x: x['roi_porcentaje'], reverse=True)
    
    @staticmethod
    def proyectar_costos_futuros(procesos_historicos, periodos_futuros=12):
        """Proyecta costos futuros basado en tendencias"""
        if len(procesos_historicos) < 3:
            return None
        
        import collections
        from datetime import datetime, timedelta
        
        gastos_mensuales = collections.defaultdict(float)
        
        for proceso in procesos_historicos:
            if proceso.get('timestamp'):
                fecha = datetime.fromisoformat(proceso['timestamp'].replace('Z', '+00:00'))
                mes_key = fecha.strftime('%Y-%m')
                gastos_mensuales[mes_key] += proceso.get('costo_openai_usd', 0)
        
        meses = sorted(gastos_mensuales.keys())
        valores = [gastos_mensuales[mes] for mes in meses]
        
        if len(valores) >= 2:
            tendencia = (valores[-1] - valores[0]) / len(valores)
            ultimo_valor = valores[-1]
            
            proyecciones = []
            for i in range(1, periodos_futuros + 1):
                proyeccion = max(0, ultimo_valor + (tendencia * i))
                proyecciones.append({
                    'periodo': i,
                    'costo_proyectado': round(proyeccion, 4),
                    'fecha_estimada': (datetime.now() + timedelta(days=30*i)).strftime('%Y-%m')
                })
            
            return {
                'tendencia_mensual': round(tendencia, 4),
                'ultimo_mes': round(ultimo_valor, 4),
                'proyecciones': proyecciones,
                'total_proyectado_anual': round(sum(p['costo_proyectado'] for p in proyecciones), 4)
            }
        
        return None

def crear_analytics_financiero(procesos):
    """Genera análisis financiero completo"""
    try:
        if not procesos:
            return {"error": "No hay procesos para analizar"}
        
        analytics = FinancialAnalytics()
        roi_data = analytics.calcular_roi_por_proceso(procesos)
        proyecciones = analytics.proyectar_costos_futuros(procesos)
        
        total_costo = sum(p.get('costo_openai_usd', 0) for p in procesos)
        total_tokens = sum(p.get('tokens_usados', 0) for p in procesos)
        promedio_eficiencia = sum(p.get('respuestas_encontradas', 0) / max(p.get('preguntas_analizadas', 1), 1) for p in procesos) / len(procesos) * 100
        
        resultado = {
            'timestamp': datetime.now().isoformat(),
            'resumen_general': {
                'total_procesos': len(procesos),
                'costo_total_usd': round(total_costo, 4),
                'tokens_totales': total_tokens,
                'eficiencia_promedio': round(promedio_eficiencia, 2),
                'costo_por_token': round(total_costo / total_tokens if total_tokens > 0 else 0, 6)
            },
            'roi_por_proceso': roi_data[:10],
            'proyecciones_futuras': proyecciones,
            'recomendaciones': [
                f"ROI promedio: {round(sum(r['roi_porcentaje'] for r in roi_data) / len(roi_data), 1)}%",
                f"Mejor proceso: {roi_data[0]['proceso']}" if roi_data else "N/A",
                f"Ahorro estimado anual: ${round(sum(r['valor_generado_usd'] for r in roi_data), 2)} USD"
            ]
        }
        
        return resultado
        
    except Exception as e:
        return {"error": f"Error en análisis financiero: {str(e)}"}
