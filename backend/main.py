import os
import requests
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import database
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource

# 1. Ortam Değişkenlerini Yükle (.env)
load_dotenv()
API_KEY = os.getenv("OPEN_ROUTER_API_KEY")

if not API_KEY:
    print("UYARI: OPEN_ROUTER_API_KEY bulunamadı! .env dosyanı kontrol et.")

# Jaeger Ayarları
# Servis ismini burada belirliyoruz, Jaeger'de bu isimle görünecek.
resource = Resource.create({"service.name": "madlen-backend-api"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Docker'daki Jaeger'e (port 4317) veri gönderecek ayar
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

database.init_db()

# 3. FastAPI Uygulamasını Başlat
app = FastAPI(title="Madlen AI Gateway")

# Frontend'in (React) bağlanabilmesi için CORS izni
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Güvenlik için normalde domain yazılır ama case study için '*' (hepsi) kalsın.
    allow_methods=["*"],
    allow_headers=["*"],
)

# FastAPI uygulamasını otomatik olarak izlemeye al
FastAPIInstrumentor.instrument_app(app)

#Veri Modelleri

class Message(BaseModel):
    role: str
    content: str
    image: Optional[str] = None

class ChatRequest(BaseModel):
    model: str
    messages: List[Message] # Geçmiş konuşmalar buraya gelecek
    image: Optional[str] = None

#Endpointler

@app.get("/")
def read_root():
    return {"status": "calisiyor", "message": "Madlen Backend Hazir"}

@app.get("/history")
def get_history():
    #Kayıtlı tüm sohbet geçmişini getirir.
    return database.get_all_messages()

@app.delete("/history")
def clear_history():
    # tüm sohbet gecmisini siler
    database.clear_all_messages()
    return {"status": "success", "message": "Tüm geçmiş silindi"}

@app.get("/models")
def get_models():
    #OpenRouter'dan anlık olarak ücretsiz modelleri çeker.
    url = "https://openrouter.ai/api/v1/models"
    
    def supports_vision(model_data):
        #Model'in vision (resim) desteği olup olmadığını kontrol eder.
        architecture = model_data.get("architecture", {})
        modality = architecture.get("modality", "")
        if "image" in modality.lower() or "vision" in modality.lower():
            return True
        
        # 2. Model ID'sinde bilinen vision anahtar kelimeleri
        model_id = model_data.get("id", "").lower()
        vision_keywords = ["vision", "gpt-4o", "gpt-4-turbo", "claude-3", "gemini-pro-vision", "gemini-1.5"]
        if any(keyword in model_id for keyword in vision_keywords):
            return True
        
        # Model adında vision geçiyorsa
        model_name = model_data.get("name", "").lower()
        if "vision" in model_name:
            return True
        
        return False
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()["data"]
        
        # Sadece "ücretsiz" modelleri filtreler
        # OpenRouter'da fiyatı '0' olanlar ücretsizdir.
        free_models = []
        for model in data:
            pricing = model.get("pricing", {})
            prompt_price = float(pricing.get("prompt", -1))
            completion_price = float(pricing.get("completion", -1))
            
            # Fiyatı 0 olanları veya ID'sinde ':free' geçenleri alıyoruz
            if (prompt_price == 0 and completion_price == 0) or ":free" in model["id"]:
                free_models.append({
                    "id": model["id"],
                    "name": model["name"],
                    "supports_vision": supports_vision(model)
                })
        
        # Listeyi isme göre sıralıyoruz
        free_models = sorted(free_models, key=lambda x: x["name"])
        
        return free_models

    except Exception as e:
        print(f"Model listesi çekilemedi: {e}")
        # API çökerse yedek olarak statik liste dön (Fallback)
        return [
            {"id": "google/gemma-2-9b-it:free", "name": "Google Gemma 2 (Free)", "supports_vision": False},
            {"id": "meta-llama/llama-3-8b-instruct:free", "name": "Llama 3 (Free)", "supports_vision": False},
        ]
@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    # 1. OpenRouter API Ayarları
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "Madlen AI Case Study"
    }

    # 2. Mesaj Formatlama (Resim ve Metin Ayrımı)
    formatted_messages = []
    
    # Son mesaj hariç önceki geçmişi alıyoruz (Sadece metin olarak - Token tasarrufu için)
    for msg in request.messages[:-1]:
        formatted_messages.append({"role": msg.role, "content": msg.content})

    # Son mesajı alıyoruz (Kullanıcının şu an yazdığı)
    last_msg = request.messages[-1]
    
    if request.image:
        # Eğer resim yüklendiyse OpenRouter "Vision" formatına çeviriyoruz
        user_message_payload = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": last_msg.content
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": request.image 
                    }
                }
            ]
        }
    else:
        # Resim yoksa sadece metin gönderiyoruz
        user_message_payload = {
            "role": "user", 
            "content": last_msg.content
        }
    
    # Son mesajı listeye ekliyoruz
    formatted_messages.append(user_message_payload)

    # 3. OpenTelemetry İzleme ve API Çağrısı
    with tracer.start_as_current_span("openrouter_external_call") as span:
        try:
            # Trace içine bilgi notu düşüyoruz
            span.set_attribute("ai.model", request.model)
            span.set_attribute("has_image", bool(request.image))

            payload = {
                "model": request.model,
                "messages": formatted_messages
            }

            # İsteği Gönderiyoruz
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status() # Hata varsa durdur ve except bloğuna git

            # Cevabı İşle
            data = response.json()
            ai_content = data["choices"][0]["message"]["content"]

            #VERİTABANI KAYDI (YENİ)
            # Cevap başarılıysa hem soruyu hem cevabı veritabanına işliyoruz
            
            # A) Kullanıcı mesajını kaydet
            database.add_message(
                role="user", 
                content=last_msg.content, 
                image=request.image
            )

            # B) Yapay Zeka cevabını kaydet
            database.add_message(
                role="assistant", 
                content=ai_content,
                image=None
            )
            # ----------------------------------

            return {"role": "assistant", "content": ai_content}

        except Exception as e:
            # Hata olursa Jaeger'a bildir ve Frontend'e hata döndür
            span.record_exception(e)
            print(f"Hata oluştu: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))