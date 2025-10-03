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

# Configuración de Chataibot
CHATAIBOT_URL = "https://chataibot.ru/api/promo-chat/messages"
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
        "Referer": "https://chataibot.ru/app/free-chat",
        "Accept": "application/json",
        "Origin": "https://chataibot.ru"
    }

@app.get("/")
async def root():
    return JSONResponse(
        content={
            "status_code": 200,
            "developer": "El Impaciente"
        },
        status_code=200
    )

@app.get("/chat")
async def chat_query(text: str = ""):
    # Validar que el parámetro esté presente
    if not text or text.strip() == "":
        return JSONResponse(
            content={
                "status_code": 400,
                "developer": "El Impaciente",
                "message": "Se requiere el parámetro text"
            },
            status_code=400
        )
    
    try:
        # Preparar mensajes para Chataibot
        messages = [{"role": "user", "content": text}]
        
        # Hacer petición a Chataibot con reintentos
        max_retries = 3
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(max_retries):
                try:
                    # Esperar entre reintentos
                    if attempt > 0:
                        import asyncio
                        await asyncio.sleep(2 * attempt)
                    
                    response = await client.post(
                        CHATAIBOT_URL,
                        headers=get_headers(),
                        json={"messages": messages}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        answer = data.get("answer", "")
                        if not answer:
                            return JSONResponse(
                                content={
                                    "status_code": 400,
                                    "developer": "El Impaciente",
                                    "message": "No se recibió respuesta"
                                },
                                status_code=400
                            )
                        
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
                    
                except (httpx.TimeoutException, httpx.RequestError):
                    if attempt < max_retries - 1:
                        continue
        
        # Si llegamos aquí, todos los intentos fallaron
        return JSONResponse(
            content={
                "status_code": 400,
                "developer": "El Impaciente",
                "message": "No se pudo obtener respuesta del servicio"
            },
            status_code=400
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "status_code": 400,
                "developer": "El Impaciente",
                "message": "Error al procesar la solicitud"
            },
            status_code=400
        )
