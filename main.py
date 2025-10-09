from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API base URL
OPENAI_API_URL = "https://free-unoffical-openai-api-sreejan.hf.space/v1/chat/completions"

@app.get("/")
async def root():
    return JSONResponse(
        content={
            "status_code": 400,
            "message": "The text parameter is required",
            "developer": "El Impaciente",
            "telegram_channel": "https://t.me/Apisimpacientes",
            "usage": "Use /chat?text=your_question"
        },
        status_code=400
    )

@app.get("/chat")
async def chat_query(text: str = ""):
    # Validar que el parámetro esté presente
    if not text or text.strip() == "":
        return JSONResponse(
            content={
                "status_code": 400,
                "message": "The text parameter is required",
                "developer": "El Impaciente",
                "telegram_channel": "https://t.me/Apisimpacientes",
                "example": "/chat?text=What is Python?"
            },
            status_code=400
        )
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Preparar la petición
            payload = {
                "model": "gpt-4-turbo",  # Modelo alternativo más estable
                "messages": [
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "max_tokens": 2048,
                "temperature": 0.7
            }
            
            # Hacer la petición
            response = await client.post(
                OPENAI_API_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                return JSONResponse(
                    content={
                        "status_code": 400,
                        "message": "Error connecting to AI service. Please try again.",
                        "developer": "El Impaciente",
                        "telegram_channel": "https://t.me/Apisimpacientes"
                    },
                    status_code=400
                )
            
            # Extraer la respuesta
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
            
            if not ai_response:
                return JSONResponse(
                    content={
                        "status_code": 400,
                        "message": "No response received from AI. Please try again.",
                        "developer": "El Impaciente",
                        "telegram_channel": "https://t.me/Apisimpacientes"
                    },
                    status_code=400
                )
            
            return JSONResponse(
                content={
                    "status_code": 200,
                    "message": ai_response,
                    "model": "gpt-4-turbo",
                    "developer": "El Impaciente",
                    "telegram_channel": "https://t.me/Apisimpacientes"
                },
                status_code=200
            )
        
    except httpx.TimeoutException:
        return JSONResponse(
            content={
                "status_code": 400,
                "message": "Request timeout. Please try again.",
                "developer": "El Impaciente",
                "telegram_channel": "https://t.me/Apisimpacientes"
            },
            status_code=400
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status_code": 400,
                "message": "Error processing request. Please try again.",
                "developer": "El Impaciente",
                "telegram_channel": "https://t.me/Apisimpacientes"
            },
            status_code=400
        )

@app.get("/health")
async def health_check():
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "ChatGPT API (GPT-4-Turbo)",
            "model": "gpt-4-turbo",
            "developer": "El Impaciente",
            "telegram_channel": "https://t.me/Apisimpacientes"
        },
        status_code=200
    )
