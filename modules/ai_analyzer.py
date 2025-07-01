"""
🤖 Módulo de Análisis con IA - OPTIMIZADO
Maneja las consultas a OpenAI y el análisis de preguntas con procesamiento paralelo
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import openai
from openai import OpenAI
import random
import threading
import os

# Precios de GPT-4o-mini (por 1M tokens)
PRECIO_INPUT_POR_1M_TOKENS = 5.0
PRECIO_OUTPUT_POR_1M_TOKENS = 15.0

# Preguntas DEFAULT del sistema Robot AI (optimizadas para máxima precisión)
DEFAULT_QUESTIONS = [
    "¿Cuál es el nombre oficial de la entidad contratante o institución que está comprando o contratando? Responde ÚNICAMENTE con el nombre de la organización, sin frases como 'El nombre oficial es' o explicaciones adicionales. No incluyas ciudades, direcciones ni ubicaciones geográficas.",
    "¿Cuál es el número de NIT o identificación tributaria de la entidad contratante? Responde ÚNICAMENTE con los números del NIT, sin frases como 'El NIT es' o explicaciones adicionales. Sin espacios ni caracteres especiales.",
    "¿Cuál es la dirección física completa de la entidad contratante? Responde ÚNICAMENTE con la dirección postal, sin frases como 'La dirección es' o explicaciones adicionales. No incluyas nombres de entidades.",
    "¿En qué ciudad está ubicada la entidad contratante? Responde ÚNICAMENTE con el nombre de la ciudad, sin frases como 'La ciudad es' o explicaciones adicionales.",
    "¿Cuál es el objeto específico del contrato, licitación o proceso de compra? Responde ÚNICAMENTE con la descripción del objeto, sin frases como 'El objeto es' o explicaciones adicionales.",
    "¿Cuál es el valor total del contrato, presupuesto o monto estimado? Responde ÚNICAMENTE con la cifra numérica y su moneda, sin frases como 'El valor es' o explicaciones adicionales.",
    "¿Qué requisitos de experiencia específica se mencionan para los proponentes o contratistas? Responde ÚNICAMENTE con los requisitos, sin frases introductorias o explicaciones adicionales.",
    "¿Qué requisitos se mencionan sobre afiliación a salud, pensión o seguridad social? Responde ÚNICAMENTE con los requisitos, sin frases introductorias o explicaciones adicionales.",
    "¿Qué documentos anexos, formatos específicos o certificados se requieren entregar? Responde ÚNICAMENTE con la lista de documentos, sin frases introductorias o explicaciones adicionales.",
    "¿Cuál es el cronograma detallado del proceso? Responde ÚNICAMENTE con las fechas, horarios y actividades tal como aparecen en el documento, sin frases introductorias o explicaciones adicionales."
]

# Configuración de OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Configuración para rate limiting
MAX_RETRIES = 5
BASE_DELAY = 1.0
MAX_DELAY = 60.0

# Control inteligente de rate limiting
class RateLimitManager:
    def __init__(self):
        self.requests_per_minute = 0
        self.tokens_per_minute = 0
        self.last_reset = datetime.now()
        self.request_times = []
        self.token_usage = []

        # Límites conservadores para gpt-4o-mini (Tier 1)
        self.MAX_REQUESTS_PER_MINUTE = 500  # Límite real es 3000, usamos margen
        self.MAX_TOKENS_PER_MINUTE = 150000  # Límite real es 200K, usamos margen
        self.PAUSE_THRESHOLD_REQUESTS = 450  # Pausar cuando lleguemos a 450 requests
        self.PAUSE_THRESHOLD_TOKENS = 130000  # Pausar cuando lleguemos a 130K tokens

    def should_pause(self):
        """Determina si debemos hacer una pausa antes de la siguiente request"""
        now = datetime.now()

        # Limpiar requests y tokens de hace más de 1 minuto
        self._cleanup_old_data(now)

        current_requests = len(self.request_times)
        current_tokens = sum(self.token_usage)

        print(f"📊 Rate limit actual: {current_requests}/{self.MAX_REQUESTS_PER_MINUTE} requests, {current_tokens}/{self.MAX_TOKENS_PER_MINUTE} tokens")

        # Verificar si estamos cerca de los límites
        if current_requests >= self.PAUSE_THRESHOLD_REQUESTS:
            print(f"⚠️ Cerca del límite de requests ({current_requests}/{self.MAX_REQUESTS_PER_MINUTE})")
            return True, "requests"

        if current_tokens >= self.PAUSE_THRESHOLD_TOKENS:
            print(f"⚠️ Cerca del límite de tokens ({current_tokens}/{self.MAX_TOKENS_PER_MINUTE})")
            return True, "tokens"

        return False, None

    def _cleanup_old_data(self, now):
        """Limpia datos de hace más de 1 minuto"""
        one_minute_ago = now - timedelta(minutes=1)

        # Filtrar requests antiguos
        self.request_times = [t for t in self.request_times if t > one_minute_ago]

        # Como token_usage corresponde 1:1 con request_times, mantener la misma longitud
        if len(self.token_usage) > len(self.request_times):
            self.token_usage = self.token_usage[-len(self.request_times):]

    def record_request(self, tokens_used=0):
        """Registra una nueva request con su uso de tokens"""
        now = datetime.now()
        self.request_times.append(now)
        self.token_usage.append(tokens_used)

        # Mantener solo el último minuto de datos
        self._cleanup_old_data(now)

    def calculate_pause_time(self, limit_type):
        """Calcula cuánto tiempo pausar basado en el tipo de límite"""
        now = datetime.now()

        if limit_type == "requests":
            # Encontrar la request más antigua dentro del minuto actual
            if self.request_times:
                oldest_request = min(self.request_times)
                time_until_reset = 60 - (now - oldest_request).total_seconds()
                return max(time_until_reset + 5, 10)  # Mínimo 10 segundos de buffer

        elif limit_type == "tokens":
            # Para tokens, hacer una pausa más conservadora
            return 30  # Pausa fija de 30 segundos

        return 15  # Pausa por defecto

# Instancia global del gestor de rate limiting
rate_limit_manager = RateLimitManager()

async def wait_for_rate_limit(error_message: str, attempt: int) -> float:
    """
    Calcula el tiempo de espera basado en el error de rate limit
    """
    try:
        # Extraer tiempo de espera del mensaje de error si está disponible
        if "Please try again in" in error_message:
            # Buscar patrón como "Please try again in 11.087s"
            import re
            match = re.search(r'try again in ([\d.]+)s', error_message)
            if match:
                suggested_wait = float(match.group(1))
                # Agregar un poco de buffer adicional
                return min(suggested_wait + random.uniform(1.0, 3.0), MAX_DELAY)
    except:
        pass

    # Fallback: exponential backoff con jitter
    delay = min(BASE_DELAY * (2 ** attempt) + random.uniform(0.1, 1.0), MAX_DELAY)
    return delay

async def call_openai_with_retry(messages: list, max_tokens: int = 500) -> dict:
    """
    Llama a OpenAI con manejo automático de rate limits y reintentos
    """
    # 🚀 PAUSA INTELIGENTE: Verificar si debemos pausar antes de hacer la request
    should_pause, limit_type = rate_limit_manager.should_pause()
    if should_pause:
        pause_time = rate_limit_manager.calculate_pause_time(limit_type)
        print(f"🛑 PAUSA INTELIGENTE: Límite de {limit_type} alcanzado")
        print(f"⏱️ Pausando {pause_time:.1f} segundos para evitar rate limit...")
        await asyncio.sleep(pause_time)
        print(f"✅ Pausa completada, reanudando procesamiento...")

    for attempt in range(MAX_RETRIES):
        try:
            print(f"🤖 Intento {attempt + 1}/{MAX_RETRIES} - Llamada a OpenAI...")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
                timeout=30.0  # Timeout de 30 segundos
            )

            # 📊 Registrar la request en el rate limit manager
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
            rate_limit_manager.record_request(tokens_used)

            return {
                'success': True,
                'response': response,
                'attempt': attempt + 1
            }

        except openai.RateLimitError as e:
            print(f"⏳ Rate limit alcanzado en intento {attempt + 1}: {str(e)}")

            if attempt < MAX_RETRIES - 1:
                wait_time = await wait_for_rate_limit(str(e), attempt)
                print(f"⏱️ Esperando {wait_time:.1f} segundos antes del siguiente intento...")
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ Máximo de reintentos alcanzado")
                return {
                    'success': False,
                    'error': f'Rate limit después de {MAX_RETRIES} intentos: {str(e)}',
                    'error_type': 'rate_limit'
                }

        except openai.APITimeoutError as e:
            print(f"⏰ Timeout en intento {attempt + 1}: {str(e)}")

            if attempt < MAX_RETRIES - 1:
                wait_time = min(5.0 * (attempt + 1), 20.0)
                print(f"⏱️ Esperando {wait_time:.1f} segundos por timeout...")
                await asyncio.sleep(wait_time)
            else:
                return {
                    'success': False,
                    'error': f'Timeout después de {MAX_RETRIES} intentos: {str(e)}',
                    'error_type': 'timeout'
                }

        except Exception as e:
            print(f"❌ Error inesperado en intento {attempt + 1}: {str(e)}")

            if attempt < MAX_RETRIES - 1:
                wait_time = min(2.0 * (attempt + 1), 10.0)
                await asyncio.sleep(wait_time)
            else:
                return {
                    'success': False,
                    'error': f'Error después de {MAX_RETRIES} intentos: {str(e)}',
                    'error_type': 'unknown'
                }

    return {
        'success': False,
        'error': 'No se pudo completar la llamada a OpenAI',
        'error_type': 'unknown'
    }

async def analyze_questions_parallel(text_chunks, questions, api_key, max_workers=3):
    """Analiza múltiples preguntas en paralelo - OPTIMIZACIÓN PRINCIPAL"""
    print(f"🚀 ANÁLISIS PARALELO: {len(questions)} preguntas con {max_workers} workers")

    if not api_key or api_key == "tu_api_key_aqui":
        return [(f"API Key no configurada", {"tokens_usados": 0, "costo_estimado": 0.0}) for _ in questions]

    # Ejecutar análisis en paralelo
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            loop.run_in_executor(
                executor, 
                analyze_single_question_optimized, 
                text_chunks, 
                question, 
                api_key,
                i+1,
                len(questions)
            ) for i, question in enumerate(questions)
        ]

        results = await asyncio.gather(*tasks)

    print(f"✅ ANÁLISIS PARALELO COMPLETADO")
    return results

def analyze_single_question_optimized(text_chunks, question, api_key, question_num=1, total_questions=1):
    """Analiza una pregunta con optimizaciones de velocidad"""
    print(f"      🤖 [{question_num}/{total_questions}] Análisis optimizado...")

    if not api_key:
        return "API Key de OpenAI no configurada", {"tokens_usados": 0, "costo_estimado": 0.0}

    if not question.strip():
        return "Pregunta vacía", {"tokens_usados": 0, "costo_estimado": 0.0}

    try:
        client = openai.OpenAI(api_key=api_key)
    except Exception as e:
        return f"Error al configurar OpenAI: {str(e)}", {"tokens_usados": 0, "costo_estimado": 0.0}

    # 🚀 OPTIMIZACIÓN 1: Análisis inteligente de fragmentos
    relevant_chunks = smart_chunk_selection(text_chunks, question)
    print(f"      ⚡ Optimización: {len(relevant_chunks)}/{len(text_chunks)} fragmentos relevantes")

    all_answers = []
    total_tokens_usados = 0
    total_costo_estimado = 0.0

    # 🚀 OPTIMIZACIÓN 2: Prompt compacto y eficiente
    prompt_template = get_optimized_prompt_template(question)

    for i, chunk in enumerate(relevant_chunks, 1):
        print(f"         📄 Fragmento {i}/{len(relevant_chunks)} ({len(chunk.split())} palabras)...")

        prompt = prompt_template.format(chunk=chunk, question=question)

        try:
            print(f"         🤖 Consultando GPT-4o-mini con contexto mejorado...")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.0,
                timeout=45
            )

            if hasattr(response, 'usage') and response.usage:
                prompt_tokens = response.usage.prompt_tokens if response.usage else 0
                completion_tokens = response.usage.completion_tokens if response.usage else 0
                total_tokens = response.usage.total_tokens if response.usage else 0

                input_cost = (prompt_tokens / 1_000_000) * PRECIO_INPUT_POR_1M_TOKENS
                output_cost = (completion_tokens / 1_000_000) * PRECIO_OUTPUT_POR_1M_TOKENS
                chunk_cost = input_cost + output_cost

                print(f"         💰 Tokens: entrada={prompt_tokens}, salida={completion_tokens}, total={total_tokens}")
                print(f"         💸 Costo estimado: ${chunk_cost:.4f}")

                total_tokens_usados += total_tokens
                total_costo_estimado += chunk_cost
            else:
                print("         💰 Tokens: No se pudo calcular el uso de tokens")
                total_costo_estimado = 0
                total_tokens_usados = 0

            answer = response.choices[0].message.content.strip()
            print(f"         📝 Respuesta: {answer[:80]}{'...' if len(answer) > 80 else ''}")

            if answer and len(answer.strip()) > 3:
                # Validación básica menos restrictiva
                respuestas_invalidas = [
                    "no encontrado", "no se encontró", "no aparece", "no está disponible",
                    "no mencionado", "no especificado", "sin información"
                ]

                # Solo rechazar si la respuesta es claramente inválida
                if not any(invalida in answer.lower() for invalida in respuestas_invalidas):
                    all_answers.append(answer)
                    print(f"         ✅ Respuesta encontrada en fragmento {i}")
                else:
                    print(f"         ⚠️ Respuesta indica que no se encontró información")
            else:
                print(f"         ❌ Respuesta muy corta o vacía")

        except Exception as e:
            error_msg = f"Error en fragmento {i+1}: {str(e)}"
            print(f"         ❌ {error_msg}")
            continue

    print(f"      📋 Completado: {len(all_answers)} respuestas válidas de {len(text_chunks)} fragmentos")
    print(f"      💰 Total tokens usados: {total_tokens_usados} | Costo total: ${total_costo_estimado:.4f}")

    metricas = {
        "tokens_usados": total_tokens_usados,
        "costo_estimado": total_costo_estimado,
        "fragmentos_procesados": len(text_chunks),
        "respuestas_encontradas": len(all_answers)
    }

    if all_answers:
        if len(all_answers) == 1:
            final_answer = all_answers[0]
        else:
            sorted_answers = sorted(all_answers, key=len, reverse=True)
            final_answer = sorted_answers[0]

            unique_answers = []
            for ans in sorted_answers:
                if not any(ans.lower() in existing.lower() or existing.lower() in ans.lower() 
                          for existing in unique_answers):
                    unique_answers.append(ans)

            if len(unique_answers) > 1:
                final_answer = " | ".join(unique_answers[:2])
            else:
                final_answer = unique_answers[0] if unique_answers else sorted_answers[0]

        print(f"      ✅ Respuesta final validada: {final_answer[:100]}{'...' if len(final_answer) > 100 else ''}")
        return final_answer, metricas
    else:
        print(f"      ❌ No se encontró información específica válida")
        return "No se encontró información específica para esta pregunta", metricas

def process_custom_questions(preguntas_personalizadas):
    """Procesa preguntas personalizadas del usuario"""
    preguntas_finales = DEFAULT_QUESTIONS.copy()
    if preguntas_personalizadas:
        try:
            preguntas_custom = json.loads(preguntas_personalizadas)
            if isinstance(preguntas_custom, list):
                preguntas_finales.extend(preguntas_custom)
                print(f"✅ Se agregaron {len(preguntas_custom)} preguntas personalizadas")
        except json.JSONDecodeError:
            print(f"⚠️ Error en formato JSON de preguntas personalizadas - usando preguntas por defecto")

    return preguntas_finales

def smart_chunk_selection(text_chunks, question):
    """Selección inteligente de fragmentos relevantes para la pregunta"""
    # Palabras clave por tipo de pregunta
    keywords_map = {
        'entidad': ['entidad', 'institución', 'ministerio', 'alcaldía', 'gobernación', 'empresa', 'contratante'],
        'nit': ['nit', 'identificación', 'tributaria', 'rut'],
        'ciudad': ['ciudad', 'municipio', 'sede', 'ubicación'],
        'direccion': ['dirección', 'dirección', 'calle', 'carrera', 'avenida'],
        'valor': ['valor', 'presupuesto', 'precio', 'costo', '$', 'pesos', 'millones'],
        'cronograma': ['fecha', 'plazo', 'término', 'cronograma', 'tiempo'],
        'experiencia': ['experiencia', 'requisitos', 'años', 'similar'],
        'salud': ['salud', 'pensión', 'seguridad social', 'afiliación'],
        'anexos': ['anexos', 'formatos', 'documentos', 'certificado']
    }

    question_lower = question.lower()
    relevant_keywords = []

    # Identificar tipo de pregunta
    for category, keywords in keywords_map.items():
        if any(keyword in question_lower for keyword in keywords):
            relevant_keywords.extend(keywords)
            break

    if not relevant_keywords:
        # Si no se identifica el tipo, usar todos los fragmentos
        return text_chunks[:3]  # Máximo 3 fragmentos

    # Puntuar fragmentos por relevancia
    scored_chunks = []
    for chunk in text_chunks:
        chunk_lower = chunk.lower()
        score = sum(1 for keyword in relevant_keywords if keyword in chunk_lower)
        if score > 0:
            scored_chunks.append((chunk, score))

    # Ordenar por relevancia y tomar los mejores
    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    # Retornar máximo 2-3 fragmentos más relevantes
    max_chunks = 2 if len(scored_chunks) > 5 else 3
    return [chunk for chunk, score in scored_chunks[:max_chunks]]

def estimate_tokens(text: str) -> int:
    """
    Estima la cantidad de tokens de un texto (aproximación)
    """
    # Aproximación: 1 token ≈ 4 caracteres en inglés/español
    return len(text) // 3  # Usar 3 para ser conservadores

def check_token_limits(messages: list, max_tokens: int = 500) -> bool:
    """
    Verifica si la llamada está dentro de los límites de tokens
    """
    total_input_tokens = sum(estimate_tokens(msg.get('content', '')) for msg in messages)

    # Límite conservador para gpt-4o-mini
    max_input_tokens = 100000  # Límite real es 128k, usar margen de seguridad

    if total_input_tokens + max_tokens > max_input_tokens:
        print(f"⚠️ Advertencia: Tokens estimados ({total_input_tokens + max_tokens}) cerca del límite")
        return False

    return True

def get_optimized_system_prompt(question: str) -> str:
    """Genera prompts optimizados según el tipo de pregunta"""
    question_lower = question.lower()

    system_prompt = """
Eres un asistente especializado en análisis de documentos de contratación pública colombiana.

INSTRUCCIONES CRÍTICAS:
1. Analiza EXHAUSTIVAMENTE el texto proporcionado
2. Responde ÚNICAMENTE basándote en la información encontrada en el texto
3. Si la información no está en el texto, responde: "No encontrado"
4. NO inventes, supongas o agregues información
5. Extrae información EXACTAMENTE como aparece en el documento
6. Busca variaciones de la información solicitada (sinónimos, diferentes formatos)

FORMATO DE RESPUESTA REQUERIDO:
- Responde ÚNICAMENTE con la información solicitada, SIN frases introductorias
- NO uses frases como "El nombre es", "La dirección es", "El valor es", "según el documento", "el texto indica", etc.
- NO agregues explicaciones adicionales ni comentarios
- Ve directamente al grano con SOLO la información específica solicitada
- Ejemplo: Si preguntan por el NIT, responde solo "800123456", NO "El NIT es 800123456"
"""

    # Prompt general más permisivo que funcionaba antes
    return system_prompt + """\n\nTEXTO DEL DOCUMENTO:\n{chunk}\n\nPREGUNTA: {question}\n\nRESPUESTA:"""

async def analyze_single_question(text_fragments: List[str], question: str, question_number: int) -> Dict[str, Any]:
    """
    Analiza una pregunta específica contra los fragmentos de texto usando OpenAI
    """
    start_time = time.time()

    try:
        print(f"🤖 Pregunta {question_number}: {question[:80]}...")

        # Combinar fragmentos relevantes
        combined_text = "\n\n".join(text_fragments[:5])  # Limitar a 5 fragmentos

        # Crear prompt optimizado
        messages = [
            {
                "role": "system",
                "content": get_optimized_system_prompt(question)
            },
            {
                "role": "user", 
                "content": f"""Analiza este documento y responde la pregunta específica:

DOCUMENTO:
{combined_text}

PREGUNTA: {question}

Instrucciones:
- Responde SOLO lo que se pregunta
- Si no encuentras información específica, responde "No se encontró información específica"
- Sé conciso y directo
- No agregues explicaciones extra"""
            }
        ]

        # Llamar a OpenAI con retry logic
        openai_result = await call_openai_with_retry(messages, max_tokens=500)

        if not openai_result['success']:
            # Manejar errores específicos
            error_type = openai_result.get('error_type', 'unknown')
            error_msg = openai_result.get('error', 'Error desconocido')

            print(f"❌ Error en pregunta {question_number}: {error_msg}")

            return {
                "pregunta_numero": question_number,
                "pregunta": question,
                "respuesta": f"Error en análisis: {error_type}",
                "informacion_encontrada": False,
                "fragmentos_analizados": len(text_fragments),
                "tiempo_procesamiento": time.time() - start_time,
                "metricas_openai": {
                    "error": error_msg,
                    "error_type": error_type,
                    "intentos_realizados": openai_result.get('attempt', 0)
                }
            }

        response = openai_result['response']

        # Procesar la respuesta de OpenAI
        respuesta = response.choices[0].message.content.strip()
        informacion_encontrada = respuesta.lower() != "no se encontró información específica"

        print(f"✅ Pregunta {question_number} completada")

        return {
            "pregunta_numero": question_number,
            "pregunta": question,
            "respuesta": respuesta,
            "informacion_encontrada": informacion_encontrada,
            "fragmentos_analizados": len(text_fragments),
            "tiempo_procesamiento": time.time() - start_time,
            "metricas_openai": {
                "tokens_usados": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "costo_estimado": (response.usage.total_tokens / 1000000) * (PRECIO_INPUT_POR_1M_TOKENS + PRECIO_OUTPUT_POR_1M_TOKENS),
                "intentos_realizados": openai_result.get('attempt', 1)
            }
        }

    except Exception as e:
        print(f"❌ Error inesperado en pregunta {question_number}: {str(e)}")
        return {
            "pregunta_numero": question_number,
            "pregunta": question,
            "respuesta": f"Error inesperado: {str(e)}",
            "informacion_encontrada": False,
            "fragmentos_analizados": len(text_fragments),
            "tiempo_procesamiento": time.time() - start_time,
            "metricas_openai": {
                "error": str(e),
                "tokens_usados": 0,
                "costo_estimado": 0
            }
        }

async def analyze_with_ai_parallel(text_fragments: List[str], custom_questions: List[str] = None) -> List[Dict[str, Any]]:
    """
    Analiza fragmentos de texto usando IA de forma secuencial con delays para evitar rate limits
    """
    print(f"🤖 Iniciando análisis con IA - {len(text_fragments)} fragmentos")

    questions = custom_questions if custom_questions else DEFAULT_QUESTIONS
    print(f"📝 Analizando {len(questions)} preguntas")

    # Procesar preguntas de forma secuencial para evitar rate limits
    results = []
    start_time = time.time()

    for i, question in enumerate(questions):
        print(f"📋 Procesando pregunta {i + 1}/{len(questions)}")

        try:
            # 🚀 VERIFICACIÓN INTELIGENTE antes de cada pregunta
            should_pause, limit_type = rate_limit_manager.should_pause()
            if should_pause:
                pause_time = rate_limit_manager.calculate_pause_time(limit_type)
                print(f"🛑 PAUSA INTELIGENTE antes de pregunta {i + 1}")
                print(f"⏱️ Límite de {limit_type} alcanzado, pausando {pause_time:.1f} segundos...")
                await asyncio.sleep(pause_time)
                print(f"✅ Pausa completada, procesando pregunta {i + 1}")

            result = await analyze_single_question(text_fragments, question, i + 1)
            results.append(result)

            # Delay adaptativo basado en el estado del rate limit
            if i < len(questions) - 1:  # No delay después de la última pregunta
                # Delay más corto si estamos lejos de los límites, más largo si estamos cerca
                current_requests = len(rate_limit_manager.request_times)
                current_tokens = sum(rate_limit_manager.token_usage)

                if current_requests > 300 or current_tokens > 100000:
                    delay = random.uniform(3.0, 5.0)  # Delay más largo si estamos cerca de límites
                    print(f"⏱️ Delay extendido: {delay:.1f}s (cerca de límites)")
                else:
                    delay = random.uniform(1.0, 2.5)  # Delay normal
                    print(f"⏱️ Delay normal: {delay:.1f}s")

                await asyncio.sleep(delay)

        except Exception as e:
            print(f"❌ Error inesperado en pregunta {i + 1}: {str(e)}")
            results.append({
                "pregunta_numero": i + 1,
                "pregunta": question,
                "respuesta": f"Error crítico en procesamiento: {str(e)}",
                "informacion_encontrada": False,
                "fragmentos_analizados": len(text_fragments),
                "tiempo_procesamiento": 0,
                "metricas_openai": {
                    "error": str(e),
                    "tokens_usados": 0,
                    "costo_estimado": 0
                }
            })

    total_time = time.time() - start_time

    # 📊 Información final del rate limiting
    final_requests = len(rate_limit_manager.request_times)
    final_tokens = sum(rate_limit_manager.token_usage)

    print(f"✅ Análisis completado en {total_time:.2f} segundos")
    print(f"📊 Rate limiting final: {final_requests}/{rate_limit_manager.MAX_REQUESTS_PER_MINUTE} requests, {final_tokens}/{rate_limit_manager.MAX_TOKENS_PER_MINUTE} tokens")

    # Agregar información de rate limiting a los resultados
    for result in results:
        if 'metricas_openai' in result:
            result['metricas_openai']['rate_limit_info'] = {
                'requests_utilizados': final_requests,
                'tokens_utilizados': final_tokens,
                'limite_requests': rate_limit_manager.MAX_REQUESTS_PER_MINUTE,
                'limite_tokens': rate_limit_manager.MAX_TOKENS_PER_MINUTE
            }

    return results