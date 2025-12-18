import sqlite3

def check_database_structure():
    """בדיקת מבנה הטבלאות במסד הנתונים"""
    try:
        conn = sqlite3.connect("quiz_results.db")
        cursor = conn.cursor()
        
        print("🔍 בודק מבנה הטבלאות...")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_stats';")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ הטבלה user_stats לא קיימת!")
            return
        
        print("✅ הטבלה user_stats קיימת")
        
        cursor.execute("PRAGMA table_info(user_stats);")
        columns = cursor.fetchall()
        
        print("\n📋 מבנה הטבלה user_stats:")
        print("אינדקס | שם עמודה | סוג | NOT NULL | ברירת מחדל | מפתח ראשי")
        print("-" * 80)
        for col in columns:
            print(f"{col[0]:6} | {col[1]:12} | {col[2]:8} | {col[3]:8} | {col[4]:12} | {col[5]:6}")
        
        cursor.execute("SELECT COUNT(*) FROM user_stats;")
        count = cursor.fetchone()[0]
        print(f"\n📊 כמות רשומות בטבלה: {count}")
        
        if count > 0:
            print("\n🔍 דוגמה לרשומה ראשונה:")
            cursor.execute("SELECT * FROM user_stats LIMIT 1;")
            sample = cursor.fetchone()
            if sample:
                for i, value in enumerate(sample):
                    col_name = columns[i][1] if i < len(columns) else f"col_{i}"
                    print(f"  {col_name}: {value}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ שגיאה בבדיקת מסד הנתונים: {e}")

def recreate_database():
    """יצירה מחדש של מסד הנתונים"""
    import os
    
    print("🗑️ מוחק מסד נתונים קיים...")
    if os.path.exists("quiz_results.db"):
        os.remove("quiz_results.db")
        print("✅ מסד נתונים ישן נמחק")
    
    conn = sqlite3.connect("quiz_results.db")
    cursor = conn.cursor()
    
    print("🏗️ יוצר טבלאות חדשות...")
    
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            display_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            percentage REAL NOT NULL,
            difficulty TEXT DEFAULT 'mixed',
            date_taken TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            time_spent INTEGER,
            details TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            total_quizzes INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 0,
            total_correct INTEGER DEFAULT 0,
            average_score REAL DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ מסד נתונים חדש נוצר בהצלחה!")

if __name__ == "__main__":
    print("🔧 כלי אבחון מסד נתונים - Calc Master")
    print("=" * 50)
    
    print("\n1️⃣ בודק מבנה נוכחי:")
    check_database_structure()
    
    print("\n" + "=" * 50)
    recreate = input("\n❓ האם לבצע יצירה מחדש של מסד הנתונים? (y/N): ")
    
    if recreate.lower() in ['y', 'yes', 'כן']:
        print("\n2️⃣ יוצר מסד נתונים חדש:")
        recreate_database()
        
        print("\n3️⃣ בודק מבנה חדש:")
        check_database_structure()
        
        print("\n✅ הפעל עכשיו את השרת: python app.py")
    else:
        print("\n👍 בוטל. נסה להפעיל את השרת ולראות אם הבעיה נפתרה.")