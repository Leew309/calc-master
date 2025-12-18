from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from functools import wraps
from database import QuizDatabase
import sqlite3

try:
    from question_generators import QuestionGenerator
    print("✅ QuestionGenerator נטען בהצלחה!")
except ImportError as e:
    print(f"❌ שגיאה בייבוא QuestionGenerator: {e}")
    exit(1)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

try:
    question_gen = QuestionGenerator()
    print("✅ QuestionGenerator אותחל בהצלחה!")
    
    db = QuizDatabase()
    print("✅ מסד נתונים אותחל בהצלחה!")
except Exception as e:
    print(f"❌ שגיאה באתחול: {e}")
    exit(1)

# === Decorators (MUST BE FIRST) ===

def login_required(f):
    """דקורטור שדורש התחברות"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = session.get('session_token')
        if not session_token:
            return redirect(url_for('login'))
        
        user = db.get_user_by_session(session_token)
        if not user:
            session.clear()
            return redirect(url_for('login'))
        
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    session_token = session.get('session_token')
    if session_token:
        return db.get_user_by_session(session_token)
    return None

# === מערכת כפילויות פשוטה ===

class SimpleDuplicationPreventer:
    """מערכת פשוטה למניעת כפילויות"""
    
    def __init__(self, db):
        self.db = db
        self.session_questions = {}
        print("✅ מערכת כפילויות פשוטה הוכנה")
    
    def is_duplicate_in_session(self, user_id, question_text):
        if user_id not in self.session_questions:
            self.session_questions[user_id] = set()
        
        # בדוק שהטקסט לא ריק
        if not question_text or not isinstance(question_text, str):
            print(f"⚠️ טקסט שאלה לא תקין: {question_text}")
            return True  # נחשב ככפילות כדי לא לכלול
        
        clean_text = question_text.lower().replace(" ", "").replace("\\", "")
        
        if clean_text in self.session_questions[user_id]:
            print(f"🔄 כפילות: {question_text[:30]}...")
            return True
        
        self.session_questions[user_id].add(clean_text)
        return False
    
    def filter_session_duplicates(self, questions, user_id):
        unique_questions = []
        
        for question in questions:
            # בדוק שהשאלה לא ריקה ושהיא dictionary
            if not question or not isinstance(question, dict):
                print(f"⚠️ שאלה לא תקינה: {question}")
                continue
                
            question_text = question.get('question', '')
            if not question_text:
                print(f"⚠️ שאלה ללא טקסט: {question}")
                continue
                
            if not self.is_duplicate_in_session(user_id, question_text):
                unique_questions.append(question)
        
        print(f"📝 מתוך {len(questions)} שאלות, {len(unique_questions)} ייחודיות")
        return unique_questions
    
    def clear_session(self, user_id):
        if user_id in self.session_questions:
            del self.session_questions[user_id]
        print(f"🔄 Session נוקה למשתמש {user_id}")

duplicate_preventer = SimpleDuplicationPreventer(db)

# === הוסיפי את זה ל-app.py אחרי השורה: duplicate_preventer = QuestionDuplicationPreventer(db) ===

class SimplePersonalizedQuiz:
    """מחולל מבחנים אישיים פשוט"""
    
    def __init__(self, db, question_gen):
        self.db = db
        self.question_gen = question_gen
        print("✅ מחולל מבחנים אישיים מוכן")
    
    def get_user_weak_topic(self, user_id):
        """מצא את הנושא הכי חלש של המשתמש"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT topic, AVG(percentage) as avg_score, COUNT(*) as attempts
                FROM quiz_results 
                WHERE user_id = ?
                GROUP BY topic
                HAVING attempts >= 2
                ORDER BY avg_score ASC
                LIMIT 1
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                topic, avg_score, attempts = result
                return {
                    'topic': topic,
                    'avg_score': avg_score,
                    'attempts': attempts,
                    'needs_work': avg_score < 75
                }
            else:
                return {
                    'topic': 'derivatives',
                    'avg_score': 0,
                    'attempts': 0,
                    'needs_work': True
                }
                
        except Exception as e:
            print(f"❌ שגיאה בניתוח: {e}")
            return {'topic': 'derivatives', 'avg_score': 0, 'attempts': 0, 'needs_work': True}
    
    def generate_smart_quiz(self, user_id):
        """צור מבחן חכם למשתמש"""
        weak_area = self.get_user_weak_topic(user_id)
        
        if weak_area['needs_work']:
            main_topic = weak_area['topic']
            explanation = f"המבחן מתמקד ב{self._topic_hebrew(main_topic)} - הנושא שזקוק לחיזוק (ציון נוכחי: {weak_area['avg_score']:.1f}%)"
            main_questions = self._get_topic_questions(main_topic, 7)
            other_questions = self._get_mixed_questions(3)
            all_questions = main_questions + other_questions
            
        else:
            explanation = "הביצועים שלך טובים! מבחן מעורב מאתגר מכל הנושאים"
            all_questions = self._get_mixed_questions(10)
        
        import random
        random.shuffle(all_questions)
        
        return {
            'questions': all_questions[:10],
            'explanation': explanation,
            'focus_topic': weak_area['topic'],
            'quiz_type': 'personalized'
        }
    
    def _topic_hebrew(self, topic):
        """תרגום לעברית"""
        translations = {
            'derivatives': 'נגזרות',
            'integrals': 'אינטגרלים',
            'limits': 'גבולות', 
            'criticalpoints': 'נקודות קיצון',
            'general': 'מעורב'
        }
        return translations.get(topic, topic)
    
    def _get_topic_questions(self, topic, count):
        """קבל שאלות לנושא ספציפי"""
        try:
            if topic == 'derivatives':
                return self.question_gen.generate_derivative_questions(count)
            elif topic == 'integrals':
                return self.question_gen.generate_integral_questions(count)
            elif topic == 'limits':
                return self.question_gen.generate_limit_questions(count)
            elif topic == 'criticalpoints':
                return self.question_gen.generate_critical_points_questions(count)
            else:
                return self.question_gen.generate_mixed_questions(count)
        except:
            # fallback
            return self.question_gen.generate_mixed_questions(count)
    
    def _get_mixed_questions(self, count):
        """קבל שאלות מעורבות"""
        try:
            return self.question_gen.generate_mixed_questions(count)
        except:
            # fallback פשוט
            return self.question_gen.generate_derivative_questions(count)

smart_quiz = SimplePersonalizedQuiz(db, question_gen)


@app.route('/api/questions/personalized')
@login_required
def get_personalized_quiz():
    """מבחן אישי פשוט"""
    try:
        user_id = request.current_user['id']
        print(f"🤖 יוצר מבחן אישי למשתמש {user_id}")
        smart_quiz_data = smart_quiz.generate_smart_quiz(user_id)
        questions = smart_quiz_data.get('questions', [])
        if not questions:
            print("❌ לא נוצרו שאלות - יוצר fallback")
            questions = question_gen.generate_mixed_questions(10)
        
        if hasattr(duplicate_preventer, 'filter_unique_questions'):
            try:
                duplicate_preventer.clear_session_cache()
                questions = duplicate_preventer.filter_unique_questions(
                    questions, user_id, 'personalized', 'mixed'
                )
            except Exception as e:
                print(f"⚠️ שגיאה בסינון כפילויות: {e}")
                pass 
        
        questions = duplicate_preventer.filter_session_duplicates(questions, user_id)
        
        if len(questions) < 8:
            print("⚡ יוצר שאלות נוספות...")
            try:
                additional = smart_quiz._get_mixed_questions(10 - len(questions))
                if additional:
                    additional = duplicate_preventer.filter_session_duplicates(additional, user_id)
                    questions.extend(additional)
            except Exception as e:
                print(f"⚠️ שגיאה ביצירת שאלות נוספות: {e}")
        
        final_questions = questions[:10]
        
        valid_questions = []
        for q in final_questions:
            if q and isinstance(q, dict) and q.get('question'):
                valid_questions.append(q)
            else:
                print(f"⚠️ שאלה לא תקינה הוסרה: {q}")
        
        if len(valid_questions) < 5:
            print("❌ לא מספיק שאלות תקינות - יוצר fallback בסיסי")
            try:
                fallback_questions = question_gen.generate_derivative_questions(10)
                valid_questions = [q for q in fallback_questions if q and isinstance(q, dict) and q.get('question')][:10]
            except:
                return jsonify({"error": "שגיאה ביצירת שאלות"}), 500
        
        result = {
            'questions': valid_questions,
            'quiz_info': {
                'explanation': smart_quiz_data.get('explanation', 'מבחן מעורב כללי'),
                'focus_topic': smart_quiz_data.get('focus_topic', 'general'),
                'quiz_type': 'personalized',
                'total_questions': len(valid_questions)
            }
        }
        
        print(f"✅ מבחן אישי מוכן: {len(valid_questions)} שאלות תקינות")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ שגיאה במבחן אישי: {str(e)}")
        try:
            fallback_questions = question_gen.generate_mixed_questions(10)
            valid_fallback = [q for q in fallback_questions if q and isinstance(q, dict) and q.get('question')][:10]
            return jsonify({
                'questions': valid_fallback,
                'quiz_info': {
                    'explanation': 'מבחן מעורב כללי',
                    'focus_topic': 'general',
                    'quiz_type': 'general',
                    'total_questions': len(valid_fallback)
                }
            })
        except Exception as fallback_error:
            print(f"❌ גם fallback נכשל: {fallback_error}")
            return jsonify({"error": f"שגיאה ביצירת מבחן: {str(e)}"}), 500

@app.route('/api/personalized/analysis')
@login_required
def get_simple_analysis():
    """ניתוח פשוט של המשתמש"""
    try:
        user_id = request.current_user['id']
        weak_area = smart_quiz.get_user_weak_topic(user_id)
        
        analysis = {
            'weak_topic': weak_area['topic'],
            'weak_topic_hebrew': smart_quiz._topic_hebrew(weak_area['topic']),
            'avg_score': round(weak_area['avg_score'], 1),
            'attempts': weak_area['attempts'],
            'needs_improvement': weak_area['needs_work'],
            'recommendation': f"מומלץ להתמקד ב{smart_quiz._topic_hebrew(weak_area['topic'])}" if weak_area['needs_work'] else "הביצועים שלך טובים! המשך ככה"
        }
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        print(f"❌ שגיאה בניתוח: {str(e)}")
        return jsonify({"error": f"שגיאה בניתוח: {str(e)}"}), 500


@app.route('/')
def home():
    user = get_current_user()
    return render_template('calcmaster.html', user=user)

@app.route('/difficulty')
@login_required
def difficulty_selection():
    return render_template('difficulty_selection.html', user=request.current_user)

@app.route('/quiz')
@login_required
def quiz():
    topic = request.args.get('topic')
    if not topic:
        return redirect(url_for('home'))
    
    difficulty = request.args.get('difficulty')
    return render_template('quiz.html', user=request.current_user, topic=topic, difficulty=difficulty)

@app.route('/quiz_summary')
@login_required
def quiz_summary():
    return render_template('quiz_summary.html', user=request.current_user)

# === דפי Authentication ===

@app.route('/login')
def login():
    if get_current_user():
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/register')
def register():
    if get_current_user():
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session_token = session.get('session_token')
    if session_token:
        db.delete_session(session_token)
    session.clear()
    return redirect(url_for('home'))

# === APIs Authentication ===

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    try:
        data = request.json
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        display_name = data.get('display_name', '').strip() or None
        
        if not username or len(username) < 3:
            return jsonify({"success": False, "error": "שם משתמש חייב להכיל לפחות 3 תווים"}), 400
        
        if not email or '@' not in email:
            return jsonify({"success": False, "error": "כתובת אימייל לא תקינה"}), 400
        
        if not password or len(password) < 6:
            return jsonify({"success": False, "error": "סיסמה חייבת להכיל לפחות 6 תווים"}), 400
        
        result = db.create_user(username, email, password, display_name)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"❌ שגיאה בהרשמה: {str(e)}")
        return jsonify({"success": False, "error": "שגיאה בשרת"}), 500

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"success": False, "error": "נא למלא את כל השדות"}), 400
        
        auth_result = db.authenticate_user(username, password)
        
        if auth_result["success"]:
            user = auth_result["user"]
            session_token = db.create_session(user["id"])
            
            if session_token:
                session['session_token'] = session_token
                session['user_id'] = user["id"]
                session['username'] = user["username"]
                
                return jsonify({
                    "success": True,
                    "message": "התחברת בהצלחה!",
                    "user": {
                        "username": user["username"],
                        "display_name": user["display_name"]
                    }
                })
            else:
                return jsonify({"success": False, "error": "שגיאה ביצירת session"}), 500
        else:
            return jsonify(auth_result), 401
            
    except Exception as e:
        print(f"❌ שגיאה בהתחברות: {str(e)}")
        return jsonify({"success": False, "error": "שגיאה בשרת"}), 500

@app.route('/api/auth/me')
def api_current_user():
    user = get_current_user()
    if user:
        return jsonify({"success": True, "user": user})
    else:
        return jsonify({"success": False, "error": "לא מחובר"}), 401


@app.route('/api/questions/derivatives/basic')
@login_required
def get_derivative_basic_questions():
    try:
        user_id = request.current_user['id']
        print(f"🚀 יוצר שאלות נגזרות למשתמש {user_id}")
        
        duplicate_preventer.clear_session(user_id)
        
        questions = question_gen.generate_derivative_questions(15)
        if not questions:
            return jsonify({"error": "לא ניתן ליצור שאלות"}), 500
            
        print(f"📚 נוצרו {len(questions)} שאלות ראשוניות")
        
        unique_questions = duplicate_preventer.filter_session_duplicates(questions, user_id)
        
        if len(unique_questions) < 8:
            print("⚡ יוצר שאלות נוספות...")
            more_questions = question_gen.generate_derivative_questions(20)
            if more_questions:
                additional_unique = duplicate_preventer.filter_session_duplicates(more_questions, user_id)
                unique_questions.extend(additional_unique)
        
        final_questions = unique_questions[:10]
        
        valid_questions = [q for q in final_questions if q and isinstance(q, dict) and q.get('question')]
        
        print(f"✅ מחזיר {len(valid_questions)} שאלות נגזרות תקינות")
        return jsonify(valid_questions)
        
    except Exception as e:
        print(f"❌ שגיאה: {str(e)}")
        try:
            fallback_questions = question_gen.generate_derivative_questions(10)
            valid_fallback = [q for q in fallback_questions if q and isinstance(q, dict) and q.get('question')][:10]
            return jsonify(valid_fallback)
        except:
            return jsonify({"error": f"שגיאה ביצירת שאלות: {str(e)}"}), 500

@app.route('/api/questions/derivatives/<difficulty>')
@login_required
def get_derivative_questions_by_difficulty(difficulty):
    try:
        user_id = request.current_user['id']
        print(f"🚀 יוצר שאלות נגזרות {difficulty}")
        
        duplicate_preventer.clear_session(user_id)
        
        if difficulty == 'easy':
            questions = question_gen.derivatives.generate_easy_questions(15)
        elif difficulty == 'medium':
            questions = question_gen.derivatives.generate_medium_questions(15)
        elif difficulty == 'hard':
            questions = question_gen.derivatives.generate_hard_questions(15)
        else:
            questions = question_gen.generate_derivative_questions(15)
        
        unique_questions = duplicate_preventer.filter_session_duplicates(questions, user_id)
        final_questions = unique_questions[:10]
        
        print(f"✅ מחזיר {len(final_questions)} שאלות נגזרות {difficulty}")
        return jsonify(final_questions)
        
    except Exception as e:
        print(f"❌ שגיאה: {str(e)}")
        return jsonify({"error": f"שגיאה ביצירת שאלות: {str(e)}"}), 500

@app.route('/api/questions/integrals/basic')
@login_required
def get_integral_basic_questions():
    try:
        user_id = request.current_user['id']
        duplicate_preventer.clear_session(user_id)
        
        questions = question_gen.generate_integral_questions(15)
        unique_questions = duplicate_preventer.filter_session_duplicates(questions, user_id)
        
        final_questions = unique_questions[:10]
        print(f"✅ מחזיר {len(final_questions)} שאלות אינטגרלים")
        return jsonify(final_questions)
        
    except Exception as e:
        print(f"❌ שגיאה: {str(e)}")
        return jsonify({"error": f"שגיאה ביצירת שאלות: {str(e)}"}), 500

@app.route('/api/questions/integrals/<difficulty>')
@login_required
def get_integral_questions_by_difficulty(difficulty):
    try:
        user_id = request.current_user['id']
        duplicate_preventer.clear_session(user_id)
        
        if difficulty == 'easy':
            questions = question_gen.integrals.generate_easy_questions(15)
        elif difficulty == 'medium':
            questions = question_gen.integrals.generate_medium_questions(15)
        elif difficulty == 'hard':
            questions = question_gen.integrals.generate_hard_questions(15)
        else:
            questions = question_gen.generate_integral_questions(15)
        
        unique_questions = duplicate_preventer.filter_session_duplicates(questions, user_id)
        final_questions = unique_questions[:10]
        
        print(f"✅ מחזיר {len(final_questions)} שאלות אינטגרלים {difficulty}")
        return jsonify(final_questions)
        
    except Exception as e:
        print(f"❌ שגיאה: {str(e)}")
        return jsonify({"error": f"שגיאה ביצירת שאלות: {str(e)}"}), 500

@app.route('/api/questions/limits/basic')
@login_required
def get_limit_basic_questions():
    try:
        user_id = request.current_user['id']
        duplicate_preventer.clear_session(user_id)
        
        questions = question_gen.generate_limit_questions(15)
        unique_questions = duplicate_preventer.filter_session_duplicates(questions, user_id)
        
        final_questions = unique_questions[:10]
        print(f"✅ מחזיר {len(final_questions)} שאלות גבולות")
        return jsonify(final_questions)
        
    except Exception as e:
        print(f"❌ שגיאה: {str(e)}")
        return jsonify({"error": f"שגיאה ביצירת שאלות: {str(e)}"}), 500

@app.route('/api/questions/limits/<difficulty>')
@login_required
def get_limit_questions_by_difficulty(difficulty):
    try:
        user_id = request.current_user['id']
        duplicate_preventer.clear_session(user_id)
        
        if difficulty == 'easy':
            questions = question_gen.limits.generate_easy_questions(15)
        elif difficulty == 'medium':
            questions = question_gen.limits.generate_medium_questions(15)
        elif difficulty == 'hard':
            questions = question_gen.limits.generate_hard_questions(15)
        else:
            questions = question_gen.generate_limit_questions(15)
        
        unique_questions = duplicate_preventer.filter_session_duplicates(questions, user_id)
        final_questions = unique_questions[:10]
        
        print(f"✅ מחזיר {len(final_questions)} שאלות גבולות {difficulty}")
        return jsonify(final_questions)
        
    except Exception as e:
        print(f"❌ שגיאה: {str(e)}")
        return jsonify({"error": f"שגיאה ביצירת שאלות: {str(e)}"}), 500

@app.route('/api/questions/criticalpoints')
@login_required
def get_criticalpoints_questions():
    try:
        user_id = request.current_user['id']
        duplicate_preventer.clear_session(user_id)
        
        questions = question_gen.generate_critical_points_questions(15)
        unique_questions = duplicate_preventer.filter_session_duplicates(questions, user_id)
        
        final_questions = unique_questions[:10]
        print(f"✅ מחזיר {len(final_questions)} שאלות נקודות קיצון")
        return jsonify(final_questions)
        
    except Exception as e:
        print(f"❌ שגיאה: {str(e)}")
        return jsonify({"error": f"שגיאה ביצירת שאלות: {str(e)}"}), 500

@app.route('/api/questions/criticalpoints/<difficulty>')
@login_required
def get_criticalpoints_questions_by_difficulty(difficulty):
    try:
        user_id = request.current_user['id']
        duplicate_preventer.clear_session(user_id)
        
        if difficulty == 'easy':
            questions = question_gen.critical_points.generate_easy_questions(15)
        elif difficulty == 'medium':
            questions = question_gen.critical_points.generate_medium_questions(15)
        elif difficulty == 'hard':
            questions = question_gen.critical_points.generate_hard_questions(15)
        else:
            questions = question_gen.generate_critical_points_questions(15)
        
        unique_questions = duplicate_preventer.filter_session_duplicates(questions, user_id)
        final_questions = unique_questions[:10]
        
        print(f"✅ מחזיר {len(final_questions)} שאלות נקודות קיצון {difficulty}")
        return jsonify(final_questions)
        
    except Exception as e:
        print(f"❌ שגיאה: {str(e)}")
        return jsonify({"error": f"שגיאה ביצירת שאלות: {str(e)}"}), 500

@app.route('/api/questions/general')
@login_required
def get_general_questions():
    try:
        user_id = request.current_user['id']
        duplicate_preventer.clear_session(user_id)
        
        questions = question_gen.generate_mixed_questions(20)
        unique_questions = duplicate_preventer.filter_session_duplicates(questions, user_id)
        
        final_questions = unique_questions[:15]
        print(f"✅ מחזיר {len(final_questions)} שאלות מעורבות")
        return jsonify(final_questions)
        
    except Exception as e:
        print(f"❌ שגיאה: {str(e)}")
        return jsonify({"error": f"שגיאה ביצירת שאלות: {str(e)}"}), 500


@app.route('/api/save-result', methods=['POST'])
@login_required
def save_quiz_result():
    try:
        data = request.json
        topic = data.get('topic')
        score = data.get('score')
        total_questions = data.get('total_questions')
        time_spent = data.get('time_spent')
        details = data.get('details', {})
        
        if not all([topic, score is not None, total_questions]):
            return jsonify({"error": "חסרים נתונים חובה"}), 400
        
        user_id = request.current_user['id']
        result_id = db.save_quiz_result(user_id, topic, score, total_questions, time_spent, details)
        
        return jsonify({
            "success": True,
            "result_id": result_id,
            "message": "התוצאה נשמרה בהצלחה!"
        })
        
    except Exception as e:
        print(f"❌ שגיאה בשמירת תוצאה: {str(e)}")
        return jsonify({"error": f"שגיאה בשמירה: {str(e)}"}), 500

@app.route('/api/stats/recent')
@login_required
def get_recent_results():
    try:
        limit = request.args.get('limit', 10, type=int)
        user_id = request.current_user['id']
        results = db.get_user_recent_results(user_id, limit)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": f"שגיאה בקבלת תוצאות: {str(e)}"}), 500

@app.route('/api/stats/by-topic')
@login_required
def get_stats_by_topic():
    try:
        user_id = request.current_user['id']
        stats = db.get_user_stats_by_topic(user_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": f"שגיאה בקבלת סטטיסטיקות: {str(e)}"}), 500

@app.route('/api/stats/general')
@login_required
def get_general_stats():
    try:
        user_id = request.current_user['id']
        stats = db.get_user_general_stats(user_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": f"שגיאה בקבלת סטטיסטיקות: {str(e)}"}), 500

@app.route('/api/stats/progress')
@login_required
def get_progress_stats():
    try:
        days = request.args.get('days', 30, type=int)
        user_id = request.current_user['id']
        progress = db.get_user_progress_over_time(user_id, days)
        return jsonify(progress)
    except Exception as e:
        return jsonify({"error": f"שגיאה בקבלת התקדמות: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 מפעיל את השרת עם מערכת כפילויות פשוטה...")
    app.run(debug=True)