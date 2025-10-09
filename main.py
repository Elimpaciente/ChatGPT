from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
from datetime import datetime

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
    import random
    return {
        "Content-Type": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://chataibot.ru/app/free-chat",
        "Accept": "application/json",
        "Origin": "https://chataibot.ru"
    }

def response_needs_web_search(response: str) -> bool:
    """Detecta si la respuesta indica que necesita información actualizada"""
    outdated_indicators = [
        'october 2023',
        'october 2021',
        'as of 2023',
        'as of 2021',
        'as of my last update',
        'my knowledge cutoff',
        'real-time information',
        'real-time capabilities',
        'real-time data',
        'current information',
        'latest information',
        'up-to-date information',
        "i don't have access to real-time",
        'i cannot provide current',
        "i don't have real time information",
        'my training data',
        'knowledge cutoff',
        'last update'
    ]
    
    response_lower = response.lower()
    return any(indicator in response_lower for indicator in outdated_indicators)

async def search_web(query: str) -> str:
    """Realiza búsqueda web usando DuckDuckGo"""
    try:
        # Agregar año actual para resultados más actuales
        search_query = f"{query} 2025"
        url = f"https://api.duckduckgo.com/?q={search_query}&format=json&no_html=1&skip_disambig=1"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers={"User-Agent": USER_AGENTS[0]})
            
            if response.status_code == 200:
                data = response.json()
                
                # Intentar obtener información del Abstract
                if data.get("AbstractText") and len(data["AbstractText"]) > 30:
                    return data["AbstractText"]
                
                # Intentar obtener información de Answer
                if data.get("Answer") and len(data["Answer"]) > 10:
                    return data["Answer"]
                
                # Intentar obtener de RelatedTopics
                if data.get("RelatedTopics") and len(data["RelatedTopics"]) > 0:
                    first_topic = data["RelatedTopics"][0]
                    if isinstance(first_topic, dict) and first_topic.get("Text"):
                        return first_topic["Text"]
        
        return None
        
    except Exception as e:
        print(f"Error en búsqueda web: {str(e)}")
        return None

async def search_wikipedia(query: str) -> str:
    """Búsqueda alternativa en Wikipedia"""
    try:
        # Limpiar la consulta
        clean_query = query.replace("who is", "").replace("what is", "").replace("current", "").strip()
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_query}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers={"User-Agent": USER_AGENTS[0]})
            
            if response.status_code == 200:
                data = response.json()
                if data.get("extract") and len(data["extract"]) > 30:
                    return data["extract"]
        
        return None
        
    except Exception as e:
        print(f"Error en Wikipedia: {str(e)}")
        return None

async def get_web_search_results(query: str) -> str:
    """Obtiene resultados de búsqueda web de múltiples fuentes"""
    print(f"🔍 Buscando información actualizada para: {query}")
    
    # Intentar DuckDuckGo primero
    result = await search_web(query)
    if result:
        print("✅ Información encontrada en DuckDuckGo")
        return result
    
    # Intentar Wikipedia como alternativa
    result = await search_wikipedia(query)
    if result:
        print("✅ Información encontrada en Wikipedia")
        return result
    
    # Si todo falla, devolver mensaje genérico
    print("❌ No se encontró información actualizada")
    return f"Por favor verifica fuentes oficiales o sitios de noticias recientes para obtener la información más actualizada sobre '{query}'."

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "API de ChatGPT con búsqueda web integrada",
        "developer": "El Impaciente",
        "features": ["chat_ai", "web_search", "real_time_info"],
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
        # Preparar mensajes para Chataibot
        messages = [{"role": "user", "content": text}]
        
        search_used = False
        search_info = None
        ai_response = None
        api_working = True
        
        # Hacer petición a Chataibot con reintentos
        max_retries = 3
        last_error = None
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(max_retries):
                try:
                    # Esperar entre reintentos
                    if attempt > 0:
                        await asyncio.sleep(2 * attempt)
                    
                    response = await client.post(
                        CHATAIBOT_URL,
                        headers=get_headers(),
                        json={"messages": messages}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        ai_response = data.get("answer", "No se recibió respuesta")
                        break
                    
                    # Si es 403 y no es el último intento, continuar
                    if response.status_code == 403 and attempt < max_retries - 1:
                        continue
                    
                    last_error = f"HTTP {response.status_code}"
                    
                except httpx.TimeoutException:
                    last_error = "Timeout en la petición"
                except httpx.RequestError as e:
                    last_error = f"Error de conexión: {str(e)}"
        
        # Si no se obtuvo respuesta de la API
        if not ai_response:
            api_working = False
            print(f"API falló: {last_error}")
        
        # Verificar si necesita búsqueda web
        if api_working and ai_response and response_needs_web_search(ai_response):
            print("🔍 Respuesta desactualizada detectada, buscando información actual...")
            search_used = True
            
            search_results = await get_web_search_results(text)
            
            if search_results:
                # Reemplazar respuesta con información actualizada
                ai_response = search_results
                search_info = "Información obtenida mediante búsqueda web"
            else:
                search_info = "Búsqueda web realizada pero sin resultados concluyentes"
        
        # Si la API no funcionó, intentar búsqueda web como alternativa
        if not api_working:
            search_results = await get_web_search_results(text)
            if search_results:
                search_used = True
                ai_response = search_results
                search_info = "Respuesta obtenida completamente de búsqueda web"
            else:
                ai_response = "Lo siento, temporalmente no puedo procesar tu solicitud. Por favor intenta de nuevo en un momento."
        
        return JSONResponse(
            content={
                "status_code": 200,
                "developer": "El Impaciente",
                "message": ai_response,
                "web_search_used": search_used,
                "search_info": search_info,
                "ai_api_status": "working" if api_working else "fallback_mode",
                "timestamp": datetime.now().isoformat()
            },
            status_code=200
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "status_code": 500,
                "developer": "El Impaciente",
                "message": f"Error interno: {str(e)}",
                "web_search_used": False,
                "timestamp": datetime.now().isoformat()
            },
            status_code=500
        )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ChatGPT API con búsqueda web",
        "features": ["chatbot", "web_search", "wikipedia_fallback"],
        "developer": "El Impaciente",
        "timestamp": datetime.now().isoformat()
    }
