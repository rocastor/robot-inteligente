
# 🤖 Robot AI - Sistema Inteligente de Análisis de Documentos

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange.svg)](https://openai.com)
[![Google Drive](https://img.shields.io/badge/Google%20Drive-Integrado-yellow.svg)](https://drive.google.com)

## 🚀 Descripción

Robot AI es un sistema avanzado de análisis automático de documentos que utiliza inteligencia artificial para extraer, procesar y analizar información de archivos PDF, imágenes y documentos de texto. 

### ✨ Características Principales

- 🔍 **Extracción Inteligente**: OCR + Vision AI para máxima precisión
- 🤖 **Análisis con IA**: OpenAI GPT-4o-mini para análisis profundo
- ☁️ **Almacenamiento en la Nube**: Integración completa con Google Drive
- 📊 **Reportes Automáticos**: Generación de PDF, Excel y JSON
- 🏢 **Sistema Rocastor**: Gestión avanzada de plantillas y documentos
- 📱 **Dashboard Interactivo**: Interfaz moderna y responsive
- ⚡ **Procesamiento Paralelo**: Análisis optimizado de múltiples preguntas

## 🛠️ Tecnologías

- **Backend**: FastAPI + Python 3.11+
- **IA**: OpenAI GPT-4o-mini, Vision AI
- **OCR**: Tesseract, PyMuPDF, pdf2image
- **Almacenamiento**: Google Drive API
- **Frontend**: HTML5, CSS3, JavaScript moderno
- **Reportes**: ReportLab (PDF), OpenPyXL (Excel)

## 📦 Instalación

1. **Clonar el repositorio**:
```bash
git clone https://github.com/TU_USUARIO/robot-inteligente.git
cd robot-inteligente
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**:
```bash
# Crear archivo .env
OPENAI_API_KEY=tu_api_key_de_openai
GOOGLE_CREDENTIALS=tu_credencial_json_de_google_drive
```

4. **Ejecutar la aplicación**:
```bash
python main.py
```

La aplicación estará disponible en `http://localhost:5000`

## 🔧 Configuración

### OpenAI API Key
1. Obtén tu API key desde [OpenAI Platform](https://platform.openai.com/api-keys)
2. Agrégala a tu archivo `.env` como `OPENAI_API_KEY`

### Google Drive
1. Crea un proyecto en [Google Cloud Console](https://console.cloud.google.com)
2. Habilita la Google Drive API
3. Descarga las credenciales JSON
4. Agrégalas como `GOOGLE_CREDENTIALS` en tu `.env`

## 📚 Uso

### 1. Dashboard Principal
Accede a `/dashboard` para ver estadísticas y métricas en tiempo real.

### 2. Procesamiento de Documentos
- Sube archivos PDF, imágenes o documentos
- El sistema extraerá automáticamente el texto
- Análisis inteligente con preguntas personalizables
- Resultados guardados en Google Drive

### 3. Sistema Rocastor
Gestión avanzada de plantillas y documentos en `/documentos-rocastor`.

### 4. Panel de Filtros
Administración de procesos y datos en `/panel-filtros`.

## 🔗 API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Página principal |
| `/api` | GET | Información de la API |
| `/health` | GET | Estado del sistema |
| `/procesar` | POST | Procesar documentos |
| `/dashboard` | GET | Dashboard interactivo |
| `/panel-filtros` | GET | Panel de gestión |
| `/lista-procesos` | GET | Listar procesos |

## 📊 Módulos

- **`ai_analyzer.py`**: Análisis con OpenAI GPT-4o-mini
- **`document_processor.py`**: Extracción de texto avanzada
- **`google_drive_client.py`**: Integración con Google Drive
- **`file_generators.py`**: Generación de reportes
- **`rocastor_manager.py`**: Sistema de gestión Rocastor
- **`analytics.py`**: Análisis financiero y métricas

## 🌟 Características Avanzadas

### Vision AI
- Análisis inteligente de imágenes y documentos escaneados
- Extracción de texto de calidad superior
- Reconocimiento de tablas y estructuras complejas

### Procesamiento Paralelo
- Análisis simultáneo de múltiples preguntas
- Optimización de costos de OpenAI
- Fragmentación inteligente de documentos grandes

### Almacenamiento Híbrido
- Google Drive como almacenamiento principal
- Backup local automático
- Enlaces directos para fácil acceso

## 🔒 Seguridad

- Variables de entorno para credenciales sensibles
- Validación de archivos de entrada
- Límites de tamaño y tipo de archivo
- Encriptación en tránsito con Google Drive

## 📈 Métricas y Monitoreo

- Dashboard en tiempo real
- Costos de OpenAI por proceso
- Estadísticas de uso de almacenamiento
- Análisis de rendimiento

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👨‍💻 Autor

Desarrollado con 💜 por el equipo Robot AI

## 🔗 Enlaces

- [Documentación Completa](https://github.com/TU_USUARIO/robot-inteligente/wiki)
- [Reportar Bugs](https://github.com/TU_USUARIO/robot-inteligente/issues)
- [Solicitar Features](https://github.com/TU_USUARIO/robot-inteligente/issues/new)

---

⭐ ¡No olvides dar una estrella al proyecto si te ha sido útil!
