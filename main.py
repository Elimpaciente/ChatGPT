from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar g4f
try:
    from g4f.client import Client
    from g4f.Provider import Bing, You, Pizzagpt, GeekGpt, FreeGpt
    g4f_available = True
except ImportError:
    g4f_available = False

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "API de ChatGPT funcionando con GPT4Free",
        "developer": "El Impaciente",
        "endpoint": "/chat?text=YOUR_QUERY",
        "g4f_status": "available" if g4f_available else "not installed"
    }

@app.get("/chat")
async def chat_query(text: str = None, model: str = "gpt-3.5-turbo"):
    # Validar que el parámetro esté presente
    if not text:
        return JSONResponse(
            content={
                "status_code": 400,
                "developer": "El Impaciente",
                "message": "Se requiere el parámetro text"
            },
            status_code=400
        )
    
    # Verificar que g4f esté disponible
    if not g4f_available:
        return JSONResponse(
            content={
                "status_code": 400,
                "developer": "El Impaciente",
                "message": "GPT4Free no está instalado. Ejecuta: pip install -U g4f"
            },
            status_code=400
        )
    
    try:
        # Preparar mensajes
        messages = [{"role": "user", "content": text}]
        
        # Lista de proveedores para intentar
        providers = [None, You, Pizzagpt, GeekGpt, FreeGpt, Bing]
        max_retries = len(providers)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Esperar entre reintentos
                if attempt > 0:
                    await asyncio.sleep(2 * attempt)
                
                # Crear cliente de g4f
                client = Client()
                provider = providers[attempt]
                
                # Hacer petición a g4f
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=model,
                    messages=messages,
                    provider=provider
                )
                
                # Extraer respuesta
                message = response.choices[0].message.content
                
                return JSONResponse(
                    content={
                        "status_code": 200,
                        "developer": "El Impaciente",
                        "message": message
                    },
                    status_code=200
                )
                
            except Exception as e:
                last_error = str(e)
                # Si no es el último intento, continuar con siguiente provider
                if attempt < max_retries - 1:
                    continue
        
        # Si llegamos aquí, todos los intentos fallaron
        return JSONResponse(
            content={
                "status_code": 400,
                "developer": "El Impaciente",
                "message": f"Error al conectar con el servicio: {last_error}"
            },
            status_code=400
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "status_code": 400,
                "developer": "El Impaciente",
                "message": f"Error: {str(e)}"
            },
            status_code=400
        )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ChatGPT API via GPT4Free",
        "developer": "El Impaciente",
        "g4f_installed": g4f_available
    }

@app.get("/models")
async def list_models():
    available_models = [
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo",
        "claude-3-opus",
        "gemini-pro"
    ]
    
    return {
        "status_code": 200,
        "developer": "El Impaciente",
        "available_models": available_models,
        "usage": "/chat?text=YOUR_QUERY&model=gpt-4"
    }