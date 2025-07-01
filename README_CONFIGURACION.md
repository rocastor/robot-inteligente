
# 🔧 Configuración de Robot AI

Robot AI está diseñado para ser completamente portable y funcionar en cualquier entorno. Este documento explica todas las formas de configurar el robot.

## 🚀 Configuración Rápida

### Opción 1: Script Automático (Recomendado)
```bash
python setup_robot.py
```

### Opción 2: Configuración Manual
1. Copia `config_example.json` a `config.json`
2. Completa las claves API requeridas
3. Ejecuta `python main.py`

## 📋 Fuentes de Configuración (Por Prioridad)

Robot AI busca configuración en este orden:

### 1. Variables de Entorno
```bash
export OPENAI_API_KEY="sk-tu-api-key-aqui"
export GOOGLE_CREDENTIALS='{"type":"service_account",...}'
```

### 2. Archivo config.json
```json
{
  "openai_api_key": "sk-tu-api-key-aqui",
  "google_credentials": {
    "type": "service_account",
    "project_id": "tu-project-id",
    ...
  }
}
```

### 3. Archivos JSON Individuales
- `google_credentials.json`
- `service_account.json`
- `credentials.json`
- `google_service_account.json`

### 4. Replit Secrets (Solo en Replit)
- `OPENAI_API_KEY`
- `GOOGLE_CREDENTIALS`

## 🔑 Configuración de OpenAI

### Obtener API Key
1. Ve a [OpenAI Platform](https://platform.openai.com/api-keys)
2. Crea una nueva API Key
3. Copia la clave (empieza con `sk-`)

### Configurar
- **Variable de entorno**: `OPENAI_API_KEY=sk-tu-clave`
- **config.json**: `"openai_api_key": "sk-tu-clave"`

## ☁️ Configuración de Google Drive

### Crear Service Account
1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Crea un proyecto o selecciona uno existente
3. Habilita la Google Drive API
4. Crea un Service Account
5. Genera y descarga las credenciales JSON

### Configurar
- **Variable de entorno**: `GOOGLE_CREDENTIALS='{"type":"service_account",...}'`
- **config.json**: Pega el JSON completo en `google_credentials`
- **Archivo individual**: Guarda como `google_credentials.json`

## 🌍 Despliegue en Diferentes Entornos

### En Replit
- Usa Replit Secrets para las claves
- O crea `config.json` con las credenciales

### En Servidor Local
- Variables de entorno o `config.json`
- Asegúrate de que el puerto 5000 esté disponible

### En Docker
```dockerfile
ENV OPENAI_API_KEY=sk-tu-clave
ENV GOOGLE_CREDENTIALS='{"type":"service_account",...}'
```

### En Heroku/Railway/Render
- Configura las variables de entorno en el panel de control
- O incluye `config.json` en el deploy

## 🔒 Seguridad

### ✅ Buenas Prácticas
- Nunca subas credenciales a repositorios públicos
- Usa variables de entorno en producción
- Mantén `config.json` en `.gitignore`
- Rota las claves periódicamente

### ❌ Evitar
- Hardcodear claves en el código
- Subir archivos de credenciales a GitHub
- Compartir claves en chats o emails

## 🔍 Verificación de Configuración

### Verificar Estado
```bash
python -c "from config import config_manager; print(config_manager.get_configuration_status())"
```

### Health Check
```bash
curl http://localhost:5000/health
```

### Logs de Configuración
Al iniciar, Robot AI muestra qué configuración encontró:
```
✅ OpenAI API Key encontrado en variables de entorno
✅ Google Credentials encontrado en config.json
✅ OpenAI API Key válido
✅ Google Drive Service Account válido
```

## 🆘 Solución de Problemas

### OpenAI No Configurado
```
❌ OpenAI API Key no configurado
```
**Solución**: Configura `OPENAI_API_KEY` en cualquiera de las fuentes

### Google Drive Error
```
❌ Google Drive Credentials no configurado
```
**Solución**: Configura `GOOGLE_CREDENTIALS` con un Service Account válido

### JSON Inválido
```
❌ Google Credentials no es JSON válido
```
**Solución**: Verifica que el JSON esté bien formateado

### Permisos Insuficientes
```
❌ Error de conexión: insufficient authentication scopes
```
**Solución**: Verifica que el Service Account tenga acceso a Google Drive

## 📞 Soporte

Si tienes problemas:
1. Ejecuta `python setup_robot.py` para reconfigurar
2. Verifica el health check en `/health`
3. Revisa los logs de inicio del robot
4. Consulta este README para configuración específica

¡Robot AI está diseñado para ser fácil de configurar y usar en cualquier lugar! 🚀
