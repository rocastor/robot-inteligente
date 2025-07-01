
"""
🚀 Generador de Apps Independientes por Proceso
Crea una aplicación FastAPI completa para cada proceso analizado
"""

import os
import json
import shutil
import zipfile
from datetime import datetime
from typing import Dict, Any
import tempfile

class ProcessAppGenerator:
    def __init__(self):
        self.template_structure = {
            "main.py": self.generate_main_py,
            "requirements.txt": self.generate_requirements,
            "README.md": self.generate_readme,
            "templates/index.html": self.generate_index_html,
            "templates/dashboard.html": self.generate_dashboard_html,
            "static/css/styles.css": self.generate_styles_css,
            "static/js/app.js": self.generate_app_js,
            "data/process_data.json": self.copy_process_data,
            ".replit": self.generate_replit_config,
            "pyproject.toml": self.generate_pyproject
        }

    def generate_app_for_process(self, process_data: Dict[str, Any]) -> str:
        """Genera una app completa para un proceso específico"""
        
        process_name = process_data.get('nombre_proceso', 'proceso_desconocido')
        safe_name = self.sanitize_name(process_name)
        
        print(f"🏗️ Generando app para proceso: {process_name}")
        
        # Crear directorio temporal para la app
        app_dir = f"/tmp/app_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(app_dir, exist_ok=True)
        
        # Crear estructura de carpetas
        for folder in ["templates", "static/css", "static/js", "data", "modules"]:
            os.makedirs(os.path.join(app_dir, folder), exist_ok=True)
        
        # Generar todos los archivos
        for file_path, generator_func in self.template_structure.items():
            full_path = os.path.join(app_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                content = generator_func(process_data)
                f.write(content)
        
        # Copiar módulos necesarios
        self.copy_modules(app_dir)
        
        # Crear ZIP
        zip_path = f"{app_dir}.zip"
        self.create_zip(app_dir, zip_path)
        
        print(f"✅ App generada: {zip_path}")
        return zip_path

    def sanitize_name(self, name: str) -> str:
        """Sanitiza nombres para uso en archivos"""
        import re
        return re.sub(r'[^\w\-_]', '_', name.lower())

    def generate_main_py(self, process_data: Dict[str, Any]) -> str:
        """Genera el archivo main.py personalizado"""
        process_name = process_data.get('nombre_proceso', 'Proceso')
        carpeta_original = process_data.get('carpeta_original', 'Sin carpeta')
        
        return f'''"""
🤖 {process_name} - App Individual
Aplicación FastAPI personalizada para el proceso específico
Generada automáticamente por Robot AI v2.0
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import json
import os
from datetime import datetime
import uvicorn

# Configuración de la app
app = FastAPI(
    title="{process_name} - App",
    description="Aplicación dedicada para el proceso {process_name}",
    version="1.0.0"
)

# Configurar archivos estáticos y templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Cargar datos del proceso
with open("data/process_data.json", "r", encoding="utf-8") as f:
    PROCESS_DATA = json.load(f)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal del proceso"""
    return templates.TemplateResponse("index.html", {{
        "request": request,
        "process_name": "{process_name}",
        "process_data": PROCESS_DATA
    }})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard del proceso"""
    return templates.TemplateResponse("dashboard.html", {{
        "request": request,
        "process_name": "{process_name}",
        "process_data": PROCESS_DATA
    }})

@app.get("/api/process-info")
async def get_process_info():
    """Información completa del proceso"""
    return {{
        "process_name": "{process_name}",
        "carpeta_original": "{carpeta_original}",
        "generated_at": datetime.now().isoformat(),
        "data": PROCESS_DATA
    }}

@app.get("/api/analysis")
async def get_analysis():
    """Análisis del proceso"""
    return PROCESS_DATA.get("analisis", [])

@app.get("/api/summary")
async def get_summary():
    """Resumen del proceso"""
    return {{
        "resumen": PROCESS_DATA.get("resumen", {{}}),
        "costos": PROCESS_DATA.get("costos_openai", {{}}),
        "metadatos": PROCESS_DATA.get("metadatos_proceso", {{}})
    }}

@app.get("/download/json")
async def download_json():
    """Descarga datos como JSON"""
    return FileResponse(
        path="data/process_data.json",
        filename=f"{process_name}_data.json",
        media_type="application/json"
    )

@app.get("/health")
async def health_check():
    """Estado de la aplicación"""
    return {{
        "status": "ok",
        "process": "{process_name}",
        "timestamp": datetime.now().isoformat()
    }}

if __name__ == "__main__":
    print("🚀 Iniciando app para proceso: {process_name}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )
'''

    def generate_requirements(self, process_data: Dict[str, Any]) -> str:
        """Genera requirements.txt"""
        return '''fastapi==0.104.1
uvicorn[standard]==0.24.0
jinja2==3.1.2
python-multipart==0.0.6
aiofiles==23.2.1
'''

    def generate_readme(self, process_data: Dict[str, Any]) -> str:
        """Genera README.md"""
        process_name = process_data.get('nombre_proceso', 'Proceso')
        timestamp = process_data.get('timestamp', '')
        
        return f'''# 🤖 {process_name} - App Individual

Aplicación FastAPI dedicada para el proceso **{process_name}**.

## 📊 Información del Proceso

- **Nombre**: {process_name}
- **Fecha de análisis**: {timestamp}
- **Carpeta original**: {process_data.get('carpeta_original', 'No detectada')}
- **Archivos procesados**: {process_data.get('archivos_totales', 0)}
- **Costo OpenAI**: ${process_data.get('costo_openai_usd', 0):.4f} USD

## 🚀 Cómo ejecutar

### En Replit:
1. Sube este ZIP a un nuevo Repl
2. Presiona el botón Run
3. Visita la URL generada

### Local:
```bash
pip install -r requirements.txt
python main.py
```

## 📱 Endpoints disponibles

- `/` - Página principal
- `/dashboard` - Dashboard del proceso
- `/api/process-info` - Información completa
- `/api/analysis` - Análisis detallado
- `/api/summary` - Resumen ejecutivo
- `/download/json` - Descarga datos JSON
- `/health` - Estado de la app

## 🎯 Características

✅ **Datos completos del proceso**  
✅ **Dashboard interactivo**  
✅ **API REST completa**  
✅ **Descarga de archivos**  
✅ **Interfaz responsive**  
✅ **Deploy en un click**  

---
*Generado automáticamente por Robot AI v2.0*
'''

    def generate_index_html(self, process_data: Dict[str, Any]) -> str:
        """Genera template HTML principal"""
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ process_name }} - App</title>
    <link rel="stylesheet" href="/static/css/styles.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <header class="main-header">
        <div class="container">
            <div class="header-content">
                <h1><i class="fas fa-robot"></i> {{ process_name }}</h1>
                <p>Aplicación dedicada para este proceso</p>
            </div>
            <nav class="header-nav">
                <a href="/" class="nav-link active"><i class="fas fa-home"></i> Inicio</a>
                <a href="/dashboard" class="nav-link"><i class="fas fa-chart-dashboard"></i> Dashboard</a>
                <a href="/download/json" class="nav-link"><i class="fas fa-download"></i> Descargar</a>
            </nav>
        </div>
    </header>

    <main class="main-content">
        <div class="container">
            <div class="process-overview">
                <div class="overview-card">
                    <h2><i class="fas fa-info-circle"></i> Información del Proceso</h2>
                    <div class="info-grid">
                        <div class="info-item">
                            <span class="info-label">Proceso:</span>
                            <span class="info-value">{{ process_data.metadatos_proceso.id_unico_proceso or process_name }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Fecha:</span>
                            <span class="info-value">{{ process_data.timestamp }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Archivos:</span>
                            <span class="info-value">{{ process_data.resumen.archivos_procesados_exitosamente }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Costo:</span>
                            <span class="info-value">${{ "%.4f"|format(process_data.costos_openai.costo_total_usd) }} USD</span>
                        </div>
                    </div>
                </div>

                <div class="overview-card">
                    <h2><i class="fas fa-chart-line"></i> Estadísticas</h2>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-number">{{ process_data.resumen.preguntas_analizadas }}</div>
                            <div class="stat-label">Preguntas Analizadas</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{{ process_data.resumen.respuestas_con_informacion }}</div>
                            <div class="stat-label">Respuestas Encontradas</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{{ process_data.costos_openai.tokens_totales_usados }}</div>
                            <div class="stat-label">Tokens Usados</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="analysis-preview">
                <h2><i class="fas fa-search"></i> Vista Previa del Análisis</h2>
                <div class="analysis-grid">
                    {% for item in process_data.analisis[:3] %}
                    <div class="analysis-item">
                        <h3>{{ item.pregunta }}</h3>
                        <p>{{ item.respuesta[:200] }}{% if item.respuesta|length > 200 %}...{% endif %}</p>
                        <span class="info-badge {% if item.informacion_encontrada %}found{% else %}not-found{% endif %}">
                            {% if item.informacion_encontrada %}
                                <i class="fas fa-check"></i> Información encontrada
                            {% else %}
                                <i class="fas fa-times"></i> Sin información
                            {% endif %}
                        </span>
                    </div>
                    {% endfor %}
                </div>
                <div class="view-all">
                    <a href="/dashboard" class="btn-primary">
                        <i class="fas fa-eye"></i> Ver Análisis Completo
                    </a>
                </div>
            </div>
        </div>
    </main>

    <footer class="main-footer">
        <div class="container">
            <p><i class="fas fa-robot"></i> Generado por Robot AI v2.0 | <i class="fas fa-clock"></i> {{ process_data.timestamp }}</p>
        </div>
    </footer>

    <script src="/static/js/app.js"></script>
</body>
</html>
'''

    def generate_dashboard_html(self, process_data: Dict[str, Any]) -> str:
        """Genera dashboard HTML"""
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - {{ process_name }}</title>
    <link rel="stylesheet" href="/static/css/styles.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <header class="main-header">
        <div class="container">
            <div class="header-content">
                <h1><i class="fas fa-chart-dashboard"></i> Dashboard - {{ process_name }}</h1>
            </div>
            <nav class="header-nav">
                <a href="/" class="nav-link"><i class="fas fa-home"></i> Inicio</a>
                <a href="/dashboard" class="nav-link active"><i class="fas fa-chart-dashboard"></i> Dashboard</a>
                <a href="/download/json" class="nav-link"><i class="fas fa-download"></i> Descargar</a>
            </nav>
        </div>
    </header>

    <main class="main-content">
        <div class="container">
            <div class="dashboard-grid">
                <div class="analysis-results">
                    <h2><i class="fas fa-list-check"></i> Análisis Completo</h2>
                    {% for item in process_data.analisis %}
                    <div class="analysis-card">
                        <div class="analysis-header">
                            <h3>{{ loop.index }}. {{ item.pregunta }}</h3>
                            <span class="info-badge {% if item.informacion_encontrada %}found{% else %}not-found{% endif %}">
                                {% if item.informacion_encontrada %}
                                    <i class="fas fa-check"></i> Encontrada
                                {% else %}
                                    <i class="fas fa-times"></i> No encontrada
                                {% endif %}
                            </span>
                        </div>
                        <div class="analysis-content">
                            <p>{{ item.respuesta }}</p>
                        </div>
                        {% if item.metricas_openai %}
                        <div class="analysis-metrics">
                            <span><i class="fas fa-dollar-sign"></i> ${{ "%.4f"|format(item.metricas_openai.costo_estimado) }}</span>
                            <span><i class="fas fa-coins"></i> {{ item.metricas_openai.tokens_usados }} tokens</span>
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>

                <div class="dashboard-sidebar">
                    <div class="sidebar-card">
                        <h3><i class="fas fa-chart-pie"></i> Resumen Ejecutivo</h3>
                        <div class="summary-stats">
                            <div class="summary-item">
                                <span class="summary-number">{{ process_data.resumen.archivos_recibidos }}</span>
                                <span class="summary-label">Archivos Recibidos</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-number">{{ process_data.resumen.archivos_procesados_exitosamente }}</span>
                                <span class="summary-label">Procesados</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-number">{{ process_data.resumen.caracteres_totales_extraidos|round|int }}</span>
                                <span class="summary-label">Caracteres</span>
                            </div>
                        </div>
                    </div>

                    <div class="sidebar-card">
                        <h3><i class="fas fa-money-bill"></i> Costos OpenAI</h3>
                        <div class="cost-details">
                            <div class="cost-item">
                                <span class="cost-label">Total:</span>
                                <span class="cost-value">${{ "%.4f"|format(process_data.costos_openai.costo_total_usd) }} USD</span>
                            </div>
                            <div class="cost-item">
                                <span class="cost-label">Tokens:</span>
                                <span class="cost-value">{{ process_data.costos_openai.tokens_totales_usados }}</span>
                            </div>
                            <div class="cost-item">
                                <span class="cost-label">Modelo:</span>
                                <span class="cost-value">{{ process_data.costos_openai.modelo_utilizado }}</span>
                            </div>
                        </div>
                    </div>

                    <div class="sidebar-card">
                        <h3><i class="fas fa-download"></i> Exportar Datos</h3>
                        <div class="export-buttons">
                            <a href="/download/json" class="export-btn">
                                <i class="fas fa-file-code"></i> JSON
                            </a>
                            <button onclick="window.print()" class="export-btn">
                                <i class="fas fa-print"></i> Imprimir
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script src="/static/js/app.js"></script>
</body>
</html>
'''

    def generate_styles_css(self, process_data: Dict[str, Any]) -> str:
        """Genera estilos CSS"""
        return '''/* Estilos para la app individual del proceso */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header */
.main-header {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    padding: 20px 0;
    margin-bottom: 30px;
}

.header-content h1 {
    color: #2c3e50;
    font-size: 2rem;
    margin-bottom: 8px;
}

.header-content p {
    color: #7f8c8d;
    font-size: 1.1rem;
}

.header-nav {
    display: flex;
    gap: 20px;
    margin-top: 15px;
}

.nav-link {
    color: #34495e;
    text-decoration: none;
    padding: 10px 20px;
    border-radius: 25px;
    transition: all 0.3s ease;
    background: rgba(52, 73, 94, 0.1);
}

.nav-link:hover, .nav-link.active {
    background: #3498db;
    color: white;
    transform: translateY(-2px);
}

/* Main Content */
.main-content {
    padding: 0 0 40px 0;
}

.process-overview {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    margin-bottom: 40px;
}

.overview-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    padding: 30px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(10px);
}

.overview-card h2 {
    color: #2c3e50;
    margin-bottom: 20px;
    font-size: 1.5rem;
}

.info-grid, .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
}

.info-item {
    display: flex;
    flex-direction: column;
}

.info-label {
    font-weight: 600;
    color: #7f8c8d;
    font-size: 0.9rem;
    margin-bottom: 5px;
}

.info-value {
    color: #2c3e50;
    font-size: 1.1rem;
}

.stat-item {
    text-align: center;
    padding: 20px;
    background: rgba(52, 152, 219, 0.1);
    border-radius: 10px;
}

.stat-number {
    font-size: 2rem;
    font-weight: bold;
    color: #3498db;
    display: block;
}

.stat-label {
    color: #7f8c8d;
    font-size: 0.9rem;
    margin-top: 5px;
}

/* Analysis */
.analysis-preview {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    padding: 30px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    margin-bottom: 30px;
}

.analysis-preview h2 {
    color: #2c3e50;
    margin-bottom: 25px;
    font-size: 1.5rem;
}

.analysis-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
}

.analysis-item, .analysis-card {
    background: rgba(248, 249, 250, 0.8);
    border-radius: 10px;
    padding: 20px;
    border-left: 4px solid #3498db;
}

.analysis-item h3, .analysis-card h3 {
    color: #2c3e50;
    margin-bottom: 10px;
    font-size: 1.1rem;
}

.analysis-item p {
    color: #555;
    line-height: 1.6;
    margin-bottom: 15px;
}

.info-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
}

.info-badge.found {
    background: #d4edda;
    color: #155724;
}

.info-badge.not-found {
    background: #f8d7da;
    color: #721c24;
}

.view-all {
    text-align: center;
    margin-top: 20px;
}

.btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #3498db;
    color: white;
    padding: 12px 24px;
    border-radius: 25px;
    text-decoration: none;
    font-weight: 500;
    transition: all 0.3s ease;
}

.btn-primary:hover {
    background: #2980b9;
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(52, 152, 219, 0.4);
}

/* Dashboard */
.dashboard-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 30px;
}

.analysis-results {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    padding: 30px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.analysis-card {
    margin-bottom: 20px;
    border-left: 4px solid #3498db;
}

.analysis-header {
    display: flex;
    justify-content: between;
    align-items: flex-start;
    margin-bottom: 15px;
}

.analysis-content p {
    color: #555;
    line-height: 1.6;
    margin-bottom: 15px;
}

.analysis-metrics {
    display: flex;
    gap: 15px;
    color: #7f8c8d;
    font-size: 0.9rem;
}

/* Sidebar */
.dashboard-sidebar {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.sidebar-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    padding: 25px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.sidebar-card h3 {
    color: #2c3e50;
    margin-bottom: 20px;
    font-size: 1.2rem;
}

.summary-stats {
    display: grid;
    gap: 15px;
}

.summary-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    background: rgba(52, 152, 219, 0.1);
    border-radius: 8px;
}

.summary-number {
    font-size: 1.5rem;
    font-weight: bold;
    color: #3498db;
}

.summary-label {
    color: #7f8c8d;
    font-size: 0.9rem;
}

.cost-details {
    display: grid;
    gap: 12px;
}

.cost-item {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.cost-label {
    color: #7f8c8d;
}

.cost-value {
    color: #2c3e50;
    font-weight: 500;
}

.export-buttons {
    display: grid;
    gap: 10px;
}

.export-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px;
    background: #34495e;
    color: white;
    text-decoration: none;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    transition: all 0.3s ease;
}

.export-btn:hover {
    background: #2c3e50;
    transform: translateY(-1px);
}

/* Footer */
.main-footer {
    background: rgba(44, 62, 80, 0.9);
    color: white;
    text-align: center;
    padding: 20px 0;
    margin-top: 40px;
}

/* Responsive */
@media (max-width: 768px) {
    .process-overview,
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
    
    .info-grid,
    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    .analysis-grid {
        grid-template-columns: 1fr;
    }
    
    .header-nav {
        flex-wrap: wrap;
    }
}
'''

    def generate_app_js(self, process_data: Dict[str, Any]) -> str:
        """Genera JavaScript para la app"""
        return '''// JavaScript para la app individual del proceso
document.addEventListener('DOMContentLoaded', function() {
    console.log('🤖 App del proceso cargada');
    
    // Mejorar UX con efectos
    animateCards();
    setupTooltips();
    setupSearch();
});

function animateCards() {
    const cards = document.querySelectorAll('.overview-card, .analysis-item, .analysis-card, .sidebar-card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
}

function setupTooltips() {
    const badges = document.querySelectorAll('.info-badge');
    
    badges.forEach(badge => {
        badge.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
        });
        
        badge.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
}

function setupSearch() {
    // Agregar búsqueda simple en el análisis
    const searchContainer = document.querySelector('.analysis-results');
    if (searchContainer) {
        const searchBox = document.createElement('div');
        searchBox.innerHTML = `
            <div style="margin-bottom: 20px;">
                <input type="text" 
                       placeholder="Buscar en el análisis..." 
                       id="analysisSearch"
                       style="width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px;">
            </div>
        `;
        
        const title = searchContainer.querySelector('h2');
        if (title) {
            title.after(searchBox);
            
            const searchInput = document.getElementById('analysisSearch');
            searchInput.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();
                const analysisCards = document.querySelectorAll('.analysis-card');
                
                analysisCards.forEach(card => {
                    const text = card.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        card.style.display = 'block';
                        card.style.opacity = '1';
                    } else {
                        card.style.display = searchTerm ? 'none' : 'block';
                        card.style.opacity = searchTerm ? '0.3' : '1';
                    }
                });
            });
        }
    }
}

// Función para copiar al portapapeles
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Copiado al portapapeles', 'success');
    });
}

// Sistema de notificaciones
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#2ecc71' : '#3498db'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 1000;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => document.body.removeChild(notification), 300);
    }, 3000);
}
'''

    def copy_process_data(self, process_data: Dict[str, Any]) -> str:
        """Copia los datos del proceso"""
        return json.dumps(process_data, ensure_ascii=False, indent=2)

    def generate_replit_config(self, process_data: Dict[str, Any]) -> str:
        """Genera configuración de Replit"""
        process_name = process_data.get('nombre_proceso', 'proceso')
        safe_name = self.sanitize_name(process_name)
        
        return f'''entrypoint = "main.py"
modules = ["python-3.11"]

[nix]
channel = "stable-24_05"

[deployment]
run = ["python3", "main.py"]
deploymentTarget = "cloudrun"

[workflows]
runButton = "Run {process_name} App"

[[workflows.workflow]]
name = "Run {process_name} App"
mode = "sequential"

[[workflows.workflow.tasks]]
task = "shell.exec"
args = "uvicorn main:app --host 0.0.0.0 --port 5000 --reload"
'''

    def generate_pyproject(self, process_data: Dict[str, Any]) -> str:
        """Genera pyproject.toml"""
        process_name = process_data.get('nombre_proceso', 'proceso')
        
        return f'''[project]
name = "{process_name}-app"
version = "1.0.0"
description = "App individual para {process_name}"
requires-python = ">=3.11"
dependencies = [
    "fastapi==0.104.1",
    "uvicorn[standard]==0.24.0",
    "jinja2==3.1.2",
    "python-multipart==0.0.6",
    "aiofiles==23.2.1"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
'''

    def copy_modules(self, app_dir: str):
        """Copia módulos necesarios"""
        modules_to_copy = [
            "modules/document_processor.py",
            "modules/ai_analyzer.py",
            "modules/file_generators.py"
        ]
        
        for module_path in modules_to_copy:
            if os.path.exists(module_path):
                dest_path = os.path.join(app_dir, module_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(module_path, dest_path)

    def create_zip(self, source_dir: str, zip_path: str):
        """Crea archivo ZIP de la app"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)

# Instancia global
app_generator = ProcessAppGenerator()
