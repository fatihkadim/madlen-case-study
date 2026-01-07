import sqlite3

DB_NAME = "madlen.db"

def init_db():
    """Veritabanını ve tabloyu oluşturur (Eğer yoksa)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Mesajlar tablosunu oluşturuyoruz
    # id: Sıra numarası
    # role: Kim yazdı? (user veya assistant)
    # content: Mesaj ne?
    # image: Varsa resim verisi (Base64)
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            image TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_message(role: str, content: str, image: str = None):
    """Yeni bir mesajı veritabanına kaydeder."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO messages (role, content, image) VALUES (?, ?, ?)",
              (role, content, image))
    conn.commit()
    conn.close()

def get_all_messages():
    """Tüm sohbet geçmişini kronolojik sırayla getirir."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Veriye sözlük gibi (row['content']) erişmek için
    c = conn.cursor()
    c.execute("SELECT role, content, image FROM messages ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    
    # Veriyi Frontend'in anlayacağı formata (List of Dict) çeviriyoruz
    messages = []
    for row in rows:
        messages.append({
            "role": row["role"],
            "content": row["content"],
            "image": row["image"] if row["image"] else None
        })
    return messages

def clear_all_messages():
    """Tüm mesajları veritabanından siler."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM messages")
    conn.commit()
    conn.close()