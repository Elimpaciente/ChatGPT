from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import random
import asyncio

chat_history = [] # Historial de la conversación

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de ChatSandbox API
CHATSANDBOX_URL = "https://chatsandbox.com/api/chat"
CHATSANDBOX_CHARACTER = "openai-gpt-4o" # Usaremos openai-gpt-4o como personaje por defecto
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
        "Referer": "https://chatsandbox.com/chat/" + CHATSANDBOX_CHARACTER, # Referer dinámico
        "Accept": "application/json",
        "Origin": "https://chatsandbox.com"
    }

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "API de ChatGPT funcionando",
        "developer": "El Impaciente",
        "endpoint": "/chat?text=YOUR_QUERY"
    }

@app.post("/chat")
async def chat_query(request: dict):
    # Validar que el parámetro esté presente
    text = request.get("text")
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
        # Preparar mensajes para ChatSandbox
        # Añadir el mensaje del usuario al historial
        chat_history.append({"role": "user", "content": text})
        
        # Usar el historial completo para la petición
        messages_payload = chat_history
        
        # Hacer petición a ChatSandbox con reintentos
        max_retries = 3
        last_error = None
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(max_retries):
                try:
                    # Esperar entre reintentos
                    if attempt > 0:
                        await asyncio.sleep(2 * attempt)
                    
                    response = await client.post(
                        CHATSANDBOX_URL,
                        headers=get_headers(),
                        json={
                            "messages": messages_payload,
                            "character": CHATSANDBOX_CHARACTER
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.text.strip() # La respuesta de ChatSandbox es un string.
                        
                        # La respuesta de ChatSandbox es un string, no un JSON. Necesitamos extraer el texto.
                        # Asumimos que la respuesta exitosa es el texto directamente, como en las pruebas anteriores.
                        # Si la API de ChatSandbox devolviera un JSON con un campo específico (ej. 'answer'), se ajustaría aquí.
                        # Por ahora, tratamos la respuesta como el mensaje directo.
                        
                        return JSONResponse(
                            content={
                                "status_code": 200,
                                "developer": "El Impaciente",
                                "message": data # La respuesta directa del chatbot
                            })

                        # Añadir la respuesta del chatbot al historial
                        chat_history.append({"role": "assistant", "content": data.strip()}) # Guardar la respuesta limpia en el historial

                        return JSONResponse(
                            content={
                                "status_code": 200,
                                "developer": "El Impaciente",
                                "message": data.strip() # Devolver la respuesta limpia al usuario
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
        "service": "ChatGPT API via ChatSandbox.com",
        "developer": "El Impaciente"
    }