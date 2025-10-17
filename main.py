from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
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

# Configuración de Puter.js API
PUTER_API_URL = "https://api.puter.com/drivers/call"
PUTER_APP_ID = "puter-chat-completion"

def get_headers():
    """Headers para Puter.js API"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "API de ChatGPT funcionando con Puter.js",
        "developer": "El Impaciente",
        "endpoint": "/chat?text=YOUR_QUERY",
        "models": "gpt-4o, gpt-4o-mini, claude-3.5-sonnet"
    }

@app.get("/chat")
async def chat_query(text: str = None, model: str = "gpt-4o-mini"):
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
    
    try:
        # Preparar payload para Puter.js
        payload = {
            "interface": "puter-chat-completion",
            "method": "complete",
            "args": {
                "messages": [
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "model": model
            }
        }
        
        # Hacer petición a Puter.js con reintentos
        max_retries = 3
        last_error = None
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(max_retries):
                try:
                    # Esperar entre reintentos
                    if attempt > 0:
                        await asyncio.sleep(2 * attempt)
                    
                    response = await client.post(
                        PUTER_API_URL,
                        headers=get_headers(),
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extraer el mensaje de la respuesta
                        message = data.get("result", {}).get("message", {}).get("content", "No se recibió respuesta")
                        
                        return JSONResponse(
                            content={
                                "status_code": 200,
                                "developer": "El Impaciente",
                                "message": message
                            },
                            status_code=200
                        )
                    
                    # Si es 403 o 429 y no es el último intento, continuar
                    if response.status_code in [403, 429] and attempt < max_retries - 1:
                        continue
                    
                    last_error = f"HTTP {response.status_code}"
                    
                except httpx.TimeoutException:
                    last_error = "Timeout en la petición"
                except httpx.RequestError as e:
                    last_error = f"Error de conexión: {str(e)}"
        
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
        "service": "ChatGPT API via Puter.js",
        "developer": "El Impaciente"
    }

@app.get("/models")
async def list_models():
    return {
        "status_code": 200,
        "developer": "El Impaciente",
        "available_models": [
            "gpt-4o",
            "gpt-4o-mini",
            "claude-3.5-sonnet"
        ],
        "usage": "/chat?text=YOUR_QUERY&model=gpt-4o"
    }