from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import random

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de ChatSandbox
CHATSANDBOX_URL = "https://chatsandbox.com/api/chat"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

def get_headers():
    """Obtiene headers aleatorios para la petición"""
    return {
        "Content-Type": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json"
    }

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "API de ChatGPT funcionando",
        "developer": "El Impaciente",
        "endpoint": "/chat?text=YOUR_QUERY"
    }

@app.get("/chat")
async def chat_query(text: str = None):
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
        # Preparar payload para ChatSandbox
        payload = {
            "messages": [text],
            "character": "openai-gpt-4o"
        }
        
        # Hacer petición a ChatSandbox con reintentos
        max_retries = 3
        last_error = None
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(max_retries):
                try:
                    # Esperar entre reintentos
                    if attempt > 0:
                        import asyncio
                        await asyncio.sleep(2 * attempt)
                    
                    response = await client.post(
                        CHATSANDBOX_URL,
                        headers=get_headers(),
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extraer la respuesta del formato de ChatSandbox
                        answer = data.get("response", data.get("message", str(data)))
                        
                        return JSONResponse(
                            content={
                                "status_code": 200,
                                "developer": "El Impaciente",
                                "message": answer
                            },
                            status_code=200
                        )
                    
                    # Si es 403 y no es el último intento, continuar
                    if response.status_code == 403 and attempt < max_retries - 1:
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
        "service": "ChatGPT API via ChatSandbox",
        "developer": "El Impaciente"
    }