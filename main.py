from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from g4f.client import Client

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar cliente g4f
client = Client()

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
        # Usar g4f con GPT-4
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": text}]
        )
        
        # Extraer respuesta
        ai_response = response.choices[0].message.content
        
        if not ai_response or ai_response.strip() == "":
            return JSONResponse(
                content={
                    "status_code": 400,
                    "message": "No response received. Please try again.",
                    "developer": "El Impaciente",
                    "telegram_channel": "https://t.me/Apisimpacientes"
                },
                status_code=400
            )
        
        return JSONResponse(
            content={
                "status_code": 200,
                "message": ai_response,
                "developer": "El Impaciente",
                "telegram_channel": "https://t.me/Apisimpacientes"
            },
            status_code=200
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
            "service": "ChatGPT API via g4f",
            "developer": "El Impaciente",
            "telegram_channel": "https://t.me/Apisimpacientes"
        },
        status_code=200
    )
