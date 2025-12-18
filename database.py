import sqlite3
import json
from datetime import datetime
import hashlib
import secrets
import os

class QuizDatabase:
    """מחלקה לניהול מסד נתונים של ציונים ומשתמשים"""
    
    def __init__(self, db_path="quiz_results.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """יצירת טבלאות אם הן לא קיימות"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
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
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                percentage REAL NOT NULL,
                difficulty TEXT DEFAULT 'mixed',
                date_taken TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                time_spent INTEGER,  -- בשניות
                details TEXT,  -- JSON עם פרטים נוספים
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
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
        
        #sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
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
        print("✅ מסד נתונים הוכן בהצלחה עם מערכת משתמשים!")
    
    
    def hash_password(self, password):
        """יצירת hash מאובטח לסיסמה"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt.encode('utf-8'), 
                                          100000)
        return password_hash.hex(), salt
    
    def verify_password(self, password, password_hash, salt):
        """אימות סיסמה"""
        computed_hash = hashlib.pbkdf2_hmac('sha256',
                                          password.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          100000)
        return computed_hash.hex() == password_hash
    
    def create_user(self, username, email, password, display_name=None):
        """יצירת משתמש חדש"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', 
                         (username, email))
            if cursor.fetchone():
                return {"success": False, "error": "שם משתמש או אימייל כבר קיימים"}
            
            password_hash, salt = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, display_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, salt, display_name or username))
            
            user_id = cursor.lastrowid
            
            cursor.execute('''
                INSERT INTO user_stats (user_id, total_quizzes, total_questions, total_correct, average_score)
                VALUES (?, 0, 0, 0, 0)
            ''', (user_id,))
            
            conn.commit()
            print(f"✅ משתמש חדש נוצר: {username}")
            return {"success": True, "user_id": user_id, "message": "משתמש נוצר בהצלחה!"}
            
        except sqlite3.IntegrityError as e:
            return {"success": False, "error": "שם משתמש או אימייל כבר קיימים"}
        except Exception as e:
            print(f"❌ שגיאה ביצירת משתמש: {e}")
            return {"success": False, "error": f"שגיאה ביצירת משתמש: {str(e)}"}
        finally:
            if conn:
                conn.close()
    
    def authenticate_user(self, username, password):
        """אימות משתמש"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, password_hash, salt, display_name 
                FROM users 
                WHERE username = ? AND is_active = 1
            ''', (username,))
            
            user = cursor.fetchone()
            if not user:
                return {"success": False, "error": "שם משתמש או סיסמה שגויים"}
            
            user_id, username, email, password_hash, salt, display_name = user
            
            if self.verify_password(password, password_hash, salt):
                cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', 
                             (user_id,))
                conn.commit()
                
                return {
                    "success": True,
                    "user": {
                        "id": user_id,
                        "username": username,
                        "email": email,
                        "display_name": display_name
                    }
                }
            else:
                return {"success": False, "error": "שם משתמש או סיסמה שגויים"}
                
        except Exception as e:
            print(f"❌ שגיאה באימות משתמש: {e}")
            return {"success": False, "error": "שגיאה באימות"}
        finally:
            if conn:
                conn.close()
    
    def create_session(self, user_id):
        """יצירת session למשתמש"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            session_token = secrets.token_urlsafe(32)
            
            from datetime import timedelta
            expires_at = datetime.now() + timedelta(days=30)
            
            cursor.execute('''
                INSERT INTO user_sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, session_token, expires_at))
            
            conn.commit()
            return session_token
            
        except Exception as e:
            print(f"❌ שגיאה ביצירת session: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_user_by_session(self, session_token):
        """קבלת משתמש לפי session token"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, u.email, u.display_name
                FROM users u
                JOIN user_sessions s ON u.id = s.user_id
                WHERE s.session_token = ? 
                AND s.expires_at > CURRENT_TIMESTAMP 
                AND s.is_active = 1
                AND u.is_active = 1
            ''', (session_token,))
            
            user = cursor.fetchone()
            if user:
                return {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "display_name": user[3]
                }
            return None
            
        except Exception as e:
            print(f"❌ שגיאה בקבלת משתמש: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def delete_session(self, session_token):
        """מחיקת session (התנתקות)"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE user_sessions SET is_active = 0 WHERE session_token = ?', 
                         (session_token,))
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ שגיאה במחיקת session: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    
    def save_quiz_result(self, user_id, topic, score, total_questions, time_spent=None, details=None):
        """שמירת תוצאת מבחן למשתמש ספציפי"""
        percentage = (score / total_questions) * 100 if total_questions > 0 else 0
        difficulty = details.get('difficulty', 'mixed') if details else 'mixed'
        
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO quiz_results (user_id, topic, score, total_questions, percentage, difficulty, time_spent, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, topic, score, total_questions, percentage, difficulty, time_spent, json.dumps(details) if details else None))
            
            result_id = cursor.lastrowid
            
            self._update_user_stats_in_same_connection(cursor, user_id, score, total_questions)
            
            conn.commit()
            print(f"✅ נשמר למשתמש {user_id}: {topic} - {score}/{total_questions} ({percentage:.1f}%)")
            return result_id
            
        except sqlite3.OperationalError as e:
            print(f"❌ שגיאה במסד נתונים: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def _update_user_stats_in_same_connection(self, cursor, user_id, score, total_questions):
        """עדכון סטטיסטיקות משתמש באותה חיבור - FIXED VERSION"""
        cursor.execute('''
            SELECT user_id, total_quizzes, total_questions, total_correct, average_score 
            FROM user_stats 
            WHERE user_id = ?
        ''', (user_id,))
        
        existing = cursor.fetchone()
        
        if existing:
            _, current_total_quizzes, current_total_questions, current_total_correct, _ = existing
            
            new_total_quizzes = current_total_quizzes + 1
            new_total_questions = current_total_questions + total_questions
            new_total_correct = current_total_correct + score
            new_average = (new_total_correct / new_total_questions) * 100 if new_total_questions > 0 else 0
            
            cursor.execute('''
                UPDATE user_stats SET 
                    total_quizzes = ?,
                    total_questions = ?,
                    total_correct = ?,
                    average_score = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (new_total_quizzes, new_total_questions, new_total_correct, new_average, user_id))
        else:
            average = (score / total_questions) * 100 if total_questions > 0 else 0
            cursor.execute('''
                INSERT INTO user_stats (user_id, total_quizzes, total_questions, total_correct, average_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, 1, total_questions, score, average))
    
    def get_user_recent_results(self, user_id, limit=10):
        """קבלת התוצאות האחרונות של משתמש"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT topic, score, total_questions, percentage, date_taken, time_spent, difficulty
                FROM quiz_results 
                WHERE user_id = ?
                ORDER BY date_taken DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            results = cursor.fetchall()
            
            return [{
                'topic': row[0],
                'score': row[1],
                'total_questions': row[2],
                'percentage': row[3],
                'date': row[4],
                'time_spent': row[5],
                'difficulty': row[6]
            } for row in results]
            
        except sqlite3.OperationalError as e:
            print(f"❌ שגיאה בקריאת נתונים: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_user_stats_by_topic(self, user_id):
        """סטטיסטיקות לפי נושא למשתמש ספציפי"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    topic,
                    COUNT(*) as attempts,
                    AVG(percentage) as avg_score,
                    MAX(percentage) as best_score,
                    MIN(percentage) as worst_score,
                    SUM(total_questions) as total_questions,
                    SUM(score) as total_correct
                FROM quiz_results 
                WHERE user_id = ?
                GROUP BY topic
                ORDER BY avg_score DESC
            ''', (user_id,))
            
            results = cursor.fetchall()
            
            return [{
                'topic': row[0],
                'attempts': row[1],
                'avg_score': round(row[2], 1),
                'best_score': round(row[3], 1),
                'worst_score': round(row[4], 1),
                'total_questions': row[5],
                'total_correct': row[6]
            } for row in results]
            
        except Exception as e:
            print(f"❌ שגיאה בקבלת סטטיסטיקות: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_user_general_stats(self, user_id):
        """סטטיסטיקות כלליות למשתמש ספציפי"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, total_quizzes, total_questions, total_correct, average_score 
                FROM user_stats 
                WHERE user_id = ?
            ''', (user_id,))
            stats = cursor.fetchone()
            
            if not stats:
                return {
                    'total_quizzes': 0,
                    'total_questions': 0,
                    'total_correct': 0,
                    'average_score': 0
                }
            
            return {
                'total_quizzes': stats[1],  # total_quizzes
                'total_questions': stats[2],  # total_questions
                'total_correct': stats[3],  # total_correct
                'average_score': round(stats[4], 1)  # average_score
            }
            
        except Exception as e:
            print(f"❌ שגיאה בקבלת סטטיסטיקות: {e}")
            return {
                'total_quizzes': 0,
                'total_questions': 0,
                'total_correct': 0,
                'average_score': 0
            }
        finally:
            if conn:
                conn.close()
    
    def get_user_progress_over_time(self, user_id, days=30):
        """התקדמות לאורך זמן למשתמש ספציפי"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    DATE(date_taken) as date,
                    AVG(percentage) as avg_score,
                    COUNT(*) as quizzes_taken
                FROM quiz_results 
                WHERE user_id = ? AND date_taken >= datetime('now', '-{} days')
                GROUP BY DATE(date_taken)
                ORDER BY date
            '''.format(days), (user_id,))
            
            results = cursor.fetchall()
            
            return [{
                'date': row[0],
                'avg_score': round(row[1], 1),
                'quizzes_taken': row[2]
            } for row in results]
            
        except Exception as e:
            print(f"❌ שגיאה בקבלת התקדמות: {e}")
            return []
        finally:
            if conn:
                conn.close()