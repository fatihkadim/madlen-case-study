# 🧙‍♂️ Madlen AI Gateway

## Case Study Hakkında

Bu proje, **Madlen Case Study** kapsamında geliştirilmiştir.

Amaç; **OpenRouter** üzerinden farklı yapay zeka modellerini tek bir arayüz altında kullanabilen, **yerel olarak çalışan** bir sohbet uygulamasını uçtan uca tasarlamak ve aynı zamanda **OpenTelemetry ile izlenebilir (observable) bir backend mimarisi** kurmaktır.

Proje bir "production ürünü" olmaktan ziyade;

* sistem tasarımı,
* teknik kararların gerekçelendirilmesi,
* observability yaklaşımı,
* geliştirici deneyimi (DX)

üzerine odaklanan bir **engineering case study** olarak ele alınmıştır.

---

## 🎯 Projenin Amacı

Bu çalışmanın temel amacı, LLM tabanlı bir sistem geliştirirken sadece "çalışan" bir uygulama üretmek değil;
aynı zamanda:

* Dış servis bağımlılıklarının (OpenRouter) nasıl izlenebilir hale getirileceğini
* Model bazlı performans farklarının nasıl gözlemlenebileceğini
* Hata durumlarının sistem seviyesinde nasıl anlamlandırılabileceğini

somut bir örnek üzerinden göstermektir.

---

## 🚀 Genel Bakış

**Madlen AI Gateway**, kullanıcıların OpenRouter üzerinden sunulan farklı yapay zeka modelleriyle sohbet edebildiği, web tabanlı bir uygulamadır.

Uygulama iki ana bileşenden oluşur:

* **Backend API**: FastAPI ile geliştirilmiş, OpenRouter entegrasyonu ve OpenTelemetry instrumentation içeren servis
* **Frontend UI**: React + TypeScript ile geliştirilmiş, kullanıcıya sohbet ve model seçimi imkanı sunan arayüz

Tüm sistem yerel ortamda çalışacak şekilde tasarlanmıştır.

---

## ✨ Özellikler

### Temel Özellikler

* **Multi‑Model AI Desteği**
  OpenRouter üzerinden birden fazla ücretsiz yapay zeka modeline erişim ve aktif model seçimi. Vision destekli modeller 📷 ikonu ile işaretlenir.

* **Sohbet Arayüzü**
  Kullanıcının mesaj gönderip model yanıtlarını gerçek zamanlı olarak görebildiği modern chat UI
  - **Markdown Rendering**: Kod blokları syntax highlighting ile görüntülenir
  - **Copy Button**: Her mesajın üzerine hover edildiğinde kopyalama butonu
  - **Glassmorphism**: Şeffaf blur efektleri ve smooth animasyonlar

* **Kalıcı Sohbet Geçmişi**
  Mesajların SQLite veritabanında saklanması ve sayfa yenilendiğinde korunması
  - **Clear Chat**: Sidebar'da geçmişi temizleme butonu

* **OpenTelemetry ile Observability**
  API çağrıları ve dış servis isteklerinin Jaeger üzerinden izlenebilmesi

### Opsiyonel (Bonus)

* **Multi‑Modal Destek**
  Vision destekli modellerle resim yükleyerek soru sorabilme

---

## 🛠️ Teknoloji Stack

### Backend

* **FastAPI** – Async destekli, modern Python web framework
* **Python 3.8+**
* **SQLite** – Hafif, yerel veritabanı
* **OpenTelemetry** – Distributed tracing
* **Uvicorn** – ASGI server

### Frontend

* **React**
* **TypeScript**
* **Vite** – Development server & build tool
* **Axios** – API iletişimi
* **react-markdown** – Markdown rendering
* **highlight.js** – Syntax highlighting

### Altyapı

* **Docker & Docker Compose** – Jaeger kurulumu
* **Jaeger** – OpenTelemetry backend

---

## 🧠 Teknik Seçimler ve Gerekçeler

### Backend – FastAPI

Backend tarafında **FastAPI** tercih edilmiştir.

Bu projenin temel gereksinimleri arasında;

* dış servislerle (OpenRouter) yoğun HTTP iletişimi,
* async request desteği,
* observability entegrasyonu

ön plandaydı.

FastAPI, async/await yapısını doğal olarak desteklemesi sayesinde dış servis çağrılarının bloklamadan yönetilmesini sağladı. Ayrıca Pydantic tabanlı request/response doğrulaması, API katmanında hataların erken aşamada yakalanmasına yardımcı oldu.

Otomatik OpenAPI (Swagger) dokümantasyonu, geliştirme sürecinde test ve debug açısından ciddi bir hız kazandırdı.

Alternatif olarak Flask düşünülebilirdi; ancak async yapı ve OpenTelemetry entegrasyonunun FastAPI tarafında daha temiz ve sürdürülebilir olması nedeniyle bu proje kapsamında FastAPI tercih edildi.

---

### OpenTelemetry & Observability Yaklaşımı

OpenTelemetry entegrasyonu bu projenin **merkezinde** yer almaktadır.

Amaç sadece API’nin çalışması değil;

* OpenRouter çağrılarının ne kadar sürdüğünü görmek
* Hangi aşamada hata oluştuğunu tespit edebilmek
* Model bazlı performans farklarını ölçebilmek

olmuştur.

Bu doğrultuda:

* Her sohbet isteği için bir **trace** oluşturulmuştur
* OpenRouter çağrıları ayrı **span** olarak işaretlenmiştir
* Kullanılan model bilgisi span attribute olarak eklenmiştir

Bu sayede Jaeger üzerinden tek bir sohbet isteğinin uçtan uca yolculuğu izlenebilmektedir.

---

### Hata Yönetimi ve Sağlamlık

Uygulama, beklenmedik durumlara karşı temel seviyede dayanıklı olacak şekilde tasarlanmıştır.

* OpenRouter API hataları backend tarafında yakalanır
* Anlamlı HTTP hata kodları frontend’e iletilir
* Kullanıcı arayüzünde loading ve error durumları açıkça gösterilir
* Hata oluşan istekler Jaeger üzerinde **error span** olarak görüntülenebilir

---

### Geliştirici Deneyimi (DX)

Kurulum ve çalıştırma sürecinin mümkün olduğunca basit olması hedeflenmiştir.

Bu amaçla:

* SQLite kullanılarak ek veritabanı kurulumu gereksiz hale getirilmiştir
* Jaeger, Docker Compose ile tek komutla ayağa kaldırılabilir
* Ortam değişkenleri `.env` dosyası üzerinden yönetilir

Bu sayede proje, farklı sistemlerde minimum konfigürasyon ile çalıştırılabilir.

---

## 🧪 Testler Hakkında

Bu case study kapsamında otomasyon testleri eklenmemiştir.

Süre kısıtı nedeniyle öncelik;

* sistem tasarımı,
* OpenTelemetry entegrasyonu,
* uçtan uca çalışan bir mimarinin kurulması

olarak belirlenmiştir.

---

## 📦 Kurulum

### Ön Gereksinimler

* Python 3.8+
* Node.js 18+
* Docker Desktop
* Git

### OpenRouter API Key

1. OpenRouter üzerinden ücretsiz bir API anahtarı alın
2. Proje kök dizininde `.env` dosyası oluşturun

```env
OPEN_ROUTER_API_KEY=sk-or-v1-xxxxxxxx
```

---

### Kurulum Adımları

```bash
# Projeyi klonlayın
git clone https://github.com/fatihkadim/madlen-case-study.git
cd madlen-case-study

# Backend Kurulumu
cd backend
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt

# Frontend Kurulumu
cd ../frontend
npm install

# Jaeger Kurulumu (Ana dizine dönerek)
cd ..
docker-compose up -d
```

---

## ▶️ Uygulamayı Çalıştırma

```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend
cd frontend
npm run dev
```

* Frontend: [http://localhost:5173](http://localhost:5173)
* Backend API: [http://localhost:8000](http://localhost:8000)
* Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
* Jaeger UI: [http://localhost:16686](http://localhost:16686)

---

## 🔍 Jaeger ile Trace İzleme

1. Frontend üzerinden bir mesaj gönderin
2. Jaeger UI’yi açın
3. Service olarak `madlen-backend-api` seçin
4. Oluşan trace’i inceleyin

Her trace içerisinde:

* API çağrısı
* OpenRouter isteği
* Veritabanı işlemleri

ayrı span’ler olarak görüntülenir.

---

## 📁 Proje Yapısı

```
madlen/
├── backend/
│   ├── main.py                 # FastAPI app & API endpoints
│   ├── database.py             # SQLite operations
│   ├── requirements.txt
│  
│
├── frontend/
│   ├── src/
│   │   ├── components/         # Chat UI, Model selector
│   │   ├── services/           # API client (Axios)
│   │   ├── types/              # TypeScript types
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   │
│   ├── public/                 # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── .gitignore
│
├── docker-compose.yml          # Jaeger setup
├── .env                        # Environment variables (gitignored)
├── .gitignore
└── README.md

```

---

## 📌 Son Notlar

Bu proje, LLM tabanlı sistemlerde **observability-first** bir yaklaşımın nasıl uygulanabileceğini göstermek amacıyla hazırlanmıştır.

Özellikle;

* dış servis bağımlılıkları,
* performans analizi,
* hata ayıklama

gibi konuların OpenTelemetry ile nasıl görünür hale getirilebileceği hedeflenmiştir.

---

