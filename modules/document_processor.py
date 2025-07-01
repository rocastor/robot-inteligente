import concurrent.futures
import threading
from functools import lru_cache


"""
🤖 Módulo de Procesamiento de Documentos
Maneja la extracción de texto de PDFs, Word, imágenes, etc.
"""

import PyPDF2
import io
import os
from PIL import Image
from docx import Document
import tempfile
import re
import base64
import cv2
import numpy as np
from pdf2image import convert_from_bytes
import pytesseract
import openai

def preprocess_image_for_ocr(image):
    """Preprocesa imagen para OCR - VERSIÓN OPTIMIZADA"""
    try:
        # OPTIMIZACIÓN: Preprocesamiento más rápido
        img_array = np.array(image)

        # Convertir a escala de grises directamente si es necesario
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # OPTIMIZACIÓN: Solo aplicar mejoras esenciales
        # Usar threshold simple en lugar de adaptativo (más rápido)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        # Solo aplicar CLAHE si la imagen está muy oscura
        if np.mean(gray) < 100:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            binary = clahe.apply(gray)
            _, binary = cv2.threshold(binary, 127, 255, cv2.THRESH_BINARY)

        return Image.fromarray(binary)

    except Exception as e:
        print(f"   ⚠️ Error en preprocesamiento: {str(e)}")
        # Fallback: devolver imagen original
        return image

def extract_text_with_vision_api(image, api_key):
    """Extrae texto usando OpenAI Vision API - OPTIMIZADO"""
    if not api_key:
        return ""

    try:
        print("   🤖 Optimizando imagen para Vision API...")

        # OPTIMIZACIÓN 1: Redimensionar imagen para reducir tiempo de procesamiento
        max_size = 2048  # Máximo 2048px en cualquier dimensión
        if image.width > max_size or image.height > max_size:
            ratio = min(max_size / image.width, max_size / image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.LANCZOS)
            print(f"   📏 Imagen redimensionada a {new_size}")

        # OPTIMIZACIÓN 2: Comprimir imagen para reducir tamaño del payload
        buffered = io.BytesIO()
        # Usar JPEG con calidad 85 en lugar de PNG para reducir tamaño
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        image.save(buffered, format="JPEG", quality=85, optimize=True)
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        print(f"   📦 Imagen comprimida: {len(img_base64)/1024:.1f} KB")

        client = openai.OpenAI(api_key=api_key)

        # OPTIMIZACIÓN 3: Prompt específico para extraer TODA la información
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Usar gpt-4o-mini (más rápido y económico)
            messages=[
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text",
                            "text": "Extrae TODO el texto visible en este documento. Incluye: datos de tablas, números, fechas, nombres, direcciones, valores monetarios, y cualquier información manuscrita o impresa. Mantén el formato y estructura original."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}",
                                "detail": "high"  # CAMBIO: Usar detalle alto para máxima precisión
                            }
                        }
                    ]
                }
            ],
            max_tokens=3000,  # AUMENTAR tokens para capturar más información
            temperature=0.0,
            timeout=45  # AUMENTAR timeout para documentos complejos
        )

        result = response.choices[0].message.content.strip()
        print(f"   ✅ Vision API completado: {len(result)} caracteres")
        return result

    except Exception as e:
        print(f"   ❌ Vision API falló: {str(e)}")
        return ""

def extract_text_from_pdf(file_content, api_key=None):
    """Extrae texto de PDF usando OCR + Vision AI - PRIORIDAD MÁXIMA A VISION AI"""
    print("   🔧 INICIANDO EXTRACCIÓN AVANZADA DE PDF...")
    print(f"   📊 Tamaño archivo: {len(file_content)/1024:.1f} KB")
    print(f"   🤖 Vision AI: {'HABILITADO' if api_key else 'DESHABILITADO'}")

    try:
        # Método 1: Extraer texto nativo con PyPDF2
        print("   📖 Método 1: Extracción de texto nativo...")
        native_text = ""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))

            if pdf_reader.is_encrypted:
                print("   🔒 PDF está encriptado - intentando sin contraseña...")
                try:
                    pdf_reader.decrypt("")
                except:
                    print("   ❌ No se pudo desencriptar el PDF")

            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        native_text += page_text + "\n"
                        print(f"   ✅ Página {page_num + 1}: {len(page_text)} caracteres extraídos")
                    else:
                        print(f"   ⚠️ Página {page_num + 1}: Sin texto extraíble")
                except Exception as e:
                    print(f"   ❌ Error en página {page_num + 1}: {str(e)}")
                    continue

            if native_text.strip() and len(native_text.strip()) > 100:
                print(f"   ✅ Método 1 exitoso: {len(native_text)} caracteres")
                # SIEMPRE probar Vision AI también para documentos complejos
                if api_key:
                    print("   🤖 Complementando con Vision AI para mayor precisión...")
                else:
                    return native_text
            else:
                print("   ⚠️ Método 1: Texto insuficiente, REQUIERE OCR+Vision AI...")

        except Exception as e:
            print(f"   ❌ Método 1 falló: {str(e)}")
            native_text = ""

        # Método 2: OCR optimizado para PDFs escaneados
        print("   🔍 Método 2: OCR optimizado...")
        try:
            images = None
            # OPTIMIZACIÓN: Usar configuración más eficiente
            dpi_configs = [150, 200]  # Reducir opciones DPI para mayor velocidad

            for dpi in dpi_configs:
                try:
                    print(f"   📸 Convirtiendo con DPI {dpi} optimizado...")
                    # OPTIMIZACIÓN: Usar JPEG en lugar de PNG (más rápido)
                    images = convert_from_bytes(
                        file_content, 
                        dpi=dpi, 
                        fmt='jpeg',
                        jpegopt={"quality": 85, "progressive": True}
                    )
                    print(f"   ✅ Conversión exitosa: {len(images)} páginas")
                    break
                except Exception as e:
                    print(f"   ⚠️ DPI {dpi} falló: {str(e)}")
                    continue

            if not images:
                print("   ❌ No se pudo convertir PDF a imágenes")
                return ""

            ocr_text = ""
            vision_text = ""

            # 🚀 PROCESAMIENTO HÍBRIDO INTELIGENTE: OCR + Vision AI sin límites
            print(f"   🔄 Iniciando procesamiento híbrido inteligente...")
            print(f"   📄 Total páginas a procesar: {len(images)} (SIN LÍMITES)")

            def should_use_vision_ai(page_num, ocr_result, total_pages):
                """Determina inteligentemente cuándo usar Vision AI"""
                # SIEMPRE usar Vision AI si:

                # 1. OCR extrajo poco o nada
                if not ocr_result or len(ocr_result.strip()) < 50:
                    return True, "OCR insuficiente"

                # 2. Detectar contenido complejo (tablas, formularios, números)
                complex_indicators = ['│', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼']
                numeric_density = sum(1 for char in ocr_result if char.isdigit()) / len(ocr_result)

                if any(indicator in ocr_result for indicator in complex_indicators):
                    return True, "Tablas detectadas"

                if numeric_density > 0.1:  # Más del 10% números
                    return True, "Alto contenido numérico"

                # 3. Contenido legal/contractual crítico
                legal_keywords = ['contrato', 'valor', 'presupuesto', 'nit', 'entidad', 
                                'cronograma', 'plazo', 'anexo', 'requisitos', 'firma']
                if any(keyword in ocr_result.lower() for keyword in legal_keywords):
                    return True, "Contenido legal crítico"

                # 4. Primera y última página siempre (información clave)
                if page_num == 1 or page_num == total_pages:
                    return True, "Página crítica (primera/última)"

                # 5. Páginas cada 3 para documentos largos (sampling inteligente)
                if total_pages > 10 and page_num % 3 == 0:
                    return True, "Muestreo en documento largo"

                return False, "No requerido"

            for i, image in enumerate(images):
                print(f"   📄 Procesando página {i+1}/{len(images)}...")

                # PASO 1: OCR Tradicional (siempre primero)
                try:
                    processed_image = preprocess_image_for_ocr(image)
                except Exception as e:
                    print(f"   ⚠️ Error preprocesando imagen: {str(e)}")
                    processed_image = image

                page_text = ""
                ocr_configs = [
                    r'--oem 3 --psm 6',
                    r'--oem 3 --psm 3', 
                    r'--oem 3 --psm 1',
                ]

                for config in ocr_configs:
                    try:
                        page_text = pytesseract.image_to_string(
                            processed_image, 
                            lang='spa+eng', 
                            config=config
                        )
                        if page_text.strip() and len(page_text.strip()) > 20:
                            print(f"   ✅ OCR exitoso: {len(page_text)} caracteres")
                            break
                    except Exception as e:
                        print(f"   ⚠️ OCR config {config} falló: {str(e)}")
                        continue

                if page_text.strip():
                    ocr_text += f"\n--- PÁGINA {i+1} (OCR) ---\n{page_text}\n"
                    print(f"   📝 OCR completado: {len(page_text)} caracteres")

                # PASO 2: Vision AI INTELIGENTE - cuando sea necesario
                if api_key:
                    use_vision, reason = should_use_vision_ai(i+1, page_text, len(images))

                    if use_vision:
                        print(f"   🤖 Vision AI NECESARIO para página {i+1}: {reason}")
                        try:
                            vision_page_text = extract_text_with_vision_api(image, api_key)
                            if vision_page_text and len(vision_page_text.strip()) > 15:
                                vision_text += f"\n--- PÁGINA {i+1} (Vision AI) ---\n{vision_page_text}\n"
                                print(f"   ✅ Vision AI exitoso: {len(vision_page_text)} caracteres")

                                # Comparar calidad
                                if len(vision_page_text.strip()) > len(page_text.strip()) * 1.2:
                                    print(f"   📈 Vision AI SUPERIOR: +{len(vision_page_text) - len(page_text)} chars")
                                else:
                                    print(f"   ⚖️ Vision AI complementario")

                            else:
                                print(f"   ⚠️ Vision AI: resultado mínimo")
                        except Exception as e:
                            print(f"   ❌ Vision API falló: {str(e)}")
                    else:
                        print(f"   ⚡ Vision AI omitido: OCR suficiente para esta página")
                else:
                    print(f"   ⚠️ Vision AI no disponible (configurar OPENAI_API_KEY)")

            print(f"   📊 Procesamiento híbrido completado:")
            print(f"      📝 OCR extrajo: {len(ocr_text)} caracteres")
            print(f"      🤖 Vision AI extrajo: {len(vision_text)} caracteres")

            final_text = ""
            if ocr_text.strip():
                final_text += ocr_text
                print(f"   ✅ OCR total: {len(ocr_text)} caracteres")

            if vision_text.strip():
                final_text += "\n\n=== TEXTO ADICIONAL (Vision API) ===\n" + vision_text
                print(f"   ✅ Vision API total: {len(vision_text)} caracteres")

            if final_text.strip():
                print(f"   🎉 Extracción completada: {len(final_text)} caracteres totales")
                return final_text
            else:
                print("   ❌ Ningún método logró extraer texto")
                return ""

        except Exception as e:
            print(f"   ❌ Método 2 (OCR) falló completamente: {str(e)}")
            return ""

    except Exception as e:
        print(f"   💥 Error crítico en extracción de PDF: {str(e)}")
        return ""

def extract_text_from_docx(file_content):
    """Extrae texto de archivos Word"""
    try:
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception:
        return ""

def extract_text_from_image(file_content, api_key=None):
    """Extrae texto de imágenes usando OCR"""
    try:
        image = Image.open(io.BytesIO(file_content))
        processed_image = preprocess_image_for_ocr(image)

        ocr_text = ""
        try:
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzáéíóúñüÁÉÍÓÚÑÜ.,;:()[]{}/$%-_@#&*+=<>?¿¡!|~^`"\' '
            ocr_text = pytesseract.image_to_string(processed_image, lang='spa+eng', config=custom_config)
        except Exception:
            pass

        vision_text = ""
        if api_key:
            vision_text = extract_text_with_vision_api(image, api_key)

        final_text = ""
        if ocr_text.strip():
            final_text += "=== TEXTO OCR ===\n" + ocr_text.strip() + "\n\n"

        if vision_text.strip() and vision_text != ocr_text.strip():
            final_text += "=== TEXTO VISION API ===\n" + vision_text.strip() + "\n\n"

        return final_text if final_text.strip() else ""

    except Exception:
        return ""

def process_file(file_content, content_type, filename, api_key=None):
    """Procesa cualquier tipo de archivo y extrae texto"""
    try:
        if content_type == "application/pdf":
            return extract_text_from_pdf(file_content, api_key)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return extract_text_from_docx(file_content)
        elif content_type.startswith("image/"):
            return extract_text_from_image(file_content, api_key)
        else:
            try:
                if isinstance(file_content, bytes):
                    text = file_content.decode('utf-8', errors='ignore')
                else:
                    text = str(file_content)
                return text
            except Exception:
                return ""
    except Exception:
        return ""

def chunk_text(text, max_words=3500):
    """Divide el texto en fragmentos optimizados para velocidad y calidad"""
    words = text.split()
    MAX_CHUNKS = 4  # Reducido para mayor velocidad

    # Optimización: fragmentos más grandes pero menos cantidad
    if len(words) > MAX_CHUNKS * max_words:
        max_words = len(words) // MAX_CHUNKS + 1000
        print(f"   ⚡ Optimización: fragmentos de {max_words} palabras para {MAX_CHUNKS} chunks máximo")

    chunks = []
    overlap = 200

    text_paragraphs = text.split('\n\n')
    current_chunk = ""
    current_words = 0

    for paragraph in text_paragraphs:
        paragraph_words = len(paragraph.split())

        if current_words + paragraph_words <= max_words:
            current_chunk += paragraph + "\n\n"
            current_words += paragraph_words
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            current_chunk = paragraph + "\n\n"
            current_words = paragraph_words

            if paragraph_words > max_words:
                para_words = paragraph.split()
                for i in range(0, len(para_words), max_words - overlap):
                    chunk_part = ' '.join(para_words[i:i + max_words])
                    chunks.append(chunk_part)
                current_chunk = ""
                current_words = 0

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    if len(chunks) < 2 and len(words) > max_words:
        print("   🔄 Usando fragmentación tradicional como respaldo...")
        chunks = []
        for i in range(0, len(words), max_words - overlap):
            chunk = ' '.join(words[i:i + max_words])
            chunks.append(chunk)

    if len(chunks) > MAX_CHUNKS:
        print(f"   ⚡ LÍMITE DE FRAGMENTOS: usando solo los primeros {MAX_CHUNKS} fragmentos para eficiencia")
        chunks = chunks[:MAX_CHUNKS]

    print(f"   📊 Texto dividido en {len(chunks)} fragmentos inteligentes")
    for i, chunk in enumerate(chunks, 1):
        palabras = len(chunk.split())
        print(f"      📄 Fragmento {i}: {palabras:,} palabras")

    return chunks