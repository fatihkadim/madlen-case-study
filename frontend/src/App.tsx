// Kütüphane importları

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';
import './App.css';

// Tip tanımları
interface Model {
  id: string;
  name: string;
  supports_vision?: boolean;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  image?: string;
}

function App() {
  // State Tanımları
  const [models, setModels] = useState<Model[]>([]);                 // Tüm modeller
  const [filteredModels, setFilteredModels] = useState<Model[]>([]);// Arama sonucu modeller
  const [selectedModel, setSelectedModel] = useState<string>('');    // Seçili model ID
  const [searchTerm, setSearchTerm] = useState('');                 // Model arama inputu

  // Sohbet yönetimi
  const [messages, setMessages] = useState<Message[]>([]);          // Mesaj geçmişi
  const [input, setInput] = useState('');                           // Kullanıcı inputu
  const [selectedImage, setSelectedImage] = useState<string | null>(null); // Yüklenmiş resim

  // UI durumları
  const [loading, setLoading] = useState(false);                    // API çağrısı yapılıyor mu?
  const [error, setError] = useState<string | null>(null);          // Hata mesajı

  // Ref'ler (DOM elementlerine erişim)
  const fileInputRef = useRef<HTMLInputElement>(null);              // Resim upload inputu
  const messagesEndRef = useRef<HTMLDivElement>(null);             // Scroll için en alt element

  // Sayfa yüklendiğinde modelleri ve geçmişi çek
  useEffect(() => {
    // Model listesini backend'den çek
    axios.get('http://127.0.0.1:8000/models')
      .then(res => {
        setModels(res.data);                              // Modelleri kaydet
        setFilteredModels(res.data);                      // Filtrelenmiş listeyi doldur
        if (res.data.length > 0) setSelectedModel(res.data[0].id); // İlk modeli seç
      })
      .catch(() => setError("Modeller yüklenemedi."));

    // Sohbet geçmişini veritabanından çek
    axios.get('http://127.0.0.1:8000/history')
      .then(res => {
        setMessages(res.data);                            // Geçmişi state'e yükle
      })
      .catch(err => console.error("Geçmiş yüklenemedi. Backend çalışıyor mu?", err));

  }, []); // Sadece ilk yüklemede çalış

  // Model arama filtresi
  useEffect(() => {
    const results = models.filter(model =>
      model.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredModels(results);  // Arama sonuçlarını güncelle
  }, [searchTerm, models]);

  // Otomatik scroll (yeni mesaj gelince)
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); // Yumuşak kaydır
  }, [messages, loading]); // Mesaj veya loading değişince çalış

  // Resim yükleme fonksiyonu
  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setSelectedImage(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  // Panoya kopyala (toast bildirim ile)
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    const tempDiv = document.createElement('div');
    tempDiv.textContent = '✓ Kopyalandı!';
    tempDiv.style.cssText = 'position:fixed;top:20px;right:20px;background:#10a37f;color:white;padding:12px 20px;border-radius:88px;z-index:9999;animation:fadeOut 2s forwards';
    document.body.appendChild(tempDiv);
    setTimeout(() => tempDiv.remove(), 2000);
  };

  // Sohbet geçmişini temizle
  const clearChat = async () => {
    if (!confirm('Tüm sohbet geçmişi silinecek. Emin misiniz?')) return;

    try {
      await axios.delete('http://127.0.0.1:8000/history');
      setMessages([]);
    } catch (err) {
      setError('Geçmiş temizlenemedi.');
    }
  };

  // Mesaj gönderme fonksiyonu
  const sendMessage = async () => {
    if ((!input.trim() && !selectedImage) || !selectedModel) return;

    const userMessage: Message = { role: 'user', content: input, image: selectedImage || undefined };
    const updatedMessages = [...messages, userMessage];

    setMessages(updatedMessages);
    setInput('');
    setSelectedImage(null);
    setLoading(true);
    setError(null);

    try {
      // Backend'e POST isteği gönder
      const response = await axios.post('http://127.0.0.1:8000/chat', {
        model: selectedModel,
        messages: updatedMessages,
        image: userMessage.image
      });
      // AI cevabını mesajlara ekle
      setMessages([...updatedMessages, response.data]);
    } catch (err: any) {
      setError("Hata oluştu. Model cevap veremedi.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-layout">

      {/*Sidebar*/}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>🧙‍♂️ Madlen AI</h2>
          <input
            type="text"
            placeholder="Model ara..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-box"
          />
        </div>

        <div className="model-list">
          {filteredModels.map(model => (
            <button
              key={model.id}
              className={`model-item ${selectedModel === model.id ? 'active' : ''}`}
              onClick={() => setSelectedModel(model.id)}
            >
              <span className="model-icon">.</span>
              <span className="model-name">{model.name.replace('(free)', '')}</span>
              {model.supports_vision && <span className="vision-badge" title="Resim desteği var">📷</span>}
            </button>
          ))}
        </div>

        <div className="sidebar-footer">
          <p className="status">🟢 Sistem: Online</p>
          <button className="clear-chat-btn" onClick={clearChat} title="Sohbet Geçmişini Temizle">
            🗑️ Geçmişi Temizle
          </button>
        </div>
      </aside>

      {/*Chat Alanı */}
      <main className="chat-container">
        <div className="chat-header">
          <h3>{models.find(m => m.id === selectedModel)?.name || 'Model Seçiniz'}</h3>
        </div>

        <div className="messages-area">
          {messages.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">👋</div>
              <h3>Hoş Geldin!</h3>
              <p>Sol taraftan bir model seç ve sohbete başla.</p>
            </div>
          )}

          {messages.map((msg, index) => (
            <div key={index} className={`message-row ${msg.role}`}>
              <div className={`message-bubble ${msg.role}`}>
                {msg.image && <img src={msg.image} className="msg-img" alt="attachment" />}
                <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
                  {msg.content}
                </ReactMarkdown>
                <button
                  className="copy-btn"
                  onClick={() => copyToClipboard(msg.content)}
                  title="Kopyala"
                >
                  📋
                </button>
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-row assistant">
              <div className="message-bubble assistant typing">
                <span>•</span><span>•</span><span>•</span>
              </div>
            </div>
          )}

          {error && <div className="error-toast">{error}</div>}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          {selectedImage && (
            <div className="preview-box">
              <img src={selectedImage} alt="preview" />
              <button onClick={() => setSelectedImage(null)}>✕</button>
            </div>
          )}

          <div className="input-wrapper">
            <input
              type="file"
              accept="image/*"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={handleImageUpload}
            />
            <button className="attach-btn" onClick={() => fileInputRef.current?.click()}>📎</button>

            <input
              type="text"
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Mesajınızı yazın..."
              disabled={loading}
            />

            <button className="send-btn" onClick={sendMessage} disabled={loading}>
              →
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;