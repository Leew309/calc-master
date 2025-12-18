# File: view_database.py
# Database viewing tool for Calc Master project

import sqlite3
import json
from datetime import datetime

def connect_to_db():
    """Connect to the database"""
    try:
        conn = sqlite3.connect("quiz_results.db")
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def show_all_users():
    """Display all users"""
    conn = connect_to_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, username, email, display_name, created_at, last_login, is_active
            FROM users
            ORDER BY created_at DESC
        ''')
        
        users = cursor.fetchall()
        
        print("\n" + "="*80)
        print("👥 All Registered Users:")
        print("="*80)
        
        if not users:
            print("📝 No users registered yet")
            return
            
        for user in users:
            user_id, username, email, display_name, created_at, last_login, is_active = user
            status = "🟢 Active" if is_active else "🔴 Inactive"
            
            print(f"""
🆔 ID: {user_id}
👤 Username: {username}
📧 Email: {email}
🏷️ Display Name: {display_name or 'Not set'}
📅 Registered: {created_at}
🕐 Last Login: {last_login or 'Never'}
⚡ Status: {status}
{'-'*50}""")
            
    except Exception as e:
        print(f"❌ Error reading users: {e}")
    finally:
        conn.close()

def show_quiz_results(user_id=None, limit=20):
    """Display quiz results"""
    conn = connect_to_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        if user_id:
            cursor.execute('''
                SELECT qr.id, u.username, qr.topic, qr.score, qr.total_questions, 
                       qr.percentage, qr.difficulty, qr.date_taken, qr.time_spent
                FROM quiz_results qr
                JOIN users u ON qr.user_id = u.id
                WHERE qr.user_id = ?
                ORDER BY qr.date_taken DESC
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT qr.id, u.username, qr.topic, qr.score, qr.total_questions, 
                       qr.percentage, qr.difficulty, qr.date_taken, qr.time_spent
                FROM quiz_results qr
                JOIN users u ON qr.user_id = u.id
                ORDER BY qr.date_taken DESC
                LIMIT ?
            ''', (limit,))
        
        results = cursor.fetchall()
        
        print("\n" + "="*100)
        if user_id:
            cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            username = cursor.fetchone()[0]
            print(f"📊 Quiz Results for {username}:")
        else:
            print("📊 Recent Quiz Results:")
        print("="*100)
        
        if not results:
            print("📝 No quiz results yet")
            return
        
        # Table header
        print(f"{'ID':<4} {'User':<15} {'Topic':<15} {'Score':<8} {'%':<6} {'Level':<8} {'Date':<20} {'Time':<6}")
        print("-"*100)
        
        for result in results:
            result_id, username, topic, score, total, percentage, difficulty, date_taken, time_spent = result
            
            # Format topic names
            topic_display = topic.title()
            if topic == 'criticalpoints':
                topic_display = 'Critical Pts'
            
            # Format difficulty
            diff_display = difficulty.title() if difficulty else 'Mixed'
            
            # Format time
            time_str = f"{time_spent}s" if time_spent else "-"
            
            print(f"{result_id:<4} {username:<15} {topic_display:<15} {score}/{total:<6} {percentage:.1f}%  {diff_display:<8} {date_taken[:16]:<20} {time_str:<6}")
            
    except Exception as e:
        print(f"❌ Error reading results: {e}")
    finally:
        conn.close()

def show_user_stats():
    """Display user statistics"""
    conn = connect_to_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT u.username, us.total_quizzes, us.total_questions, 
                   us.total_correct, us.average_score, us.last_updated
            FROM user_stats us
            JOIN users u ON us.user_id = u.id
            ORDER BY us.average_score DESC
        ''')
        
        stats = cursor.fetchall()
        
        print("\n" + "="*80)
        print("📈 User Statistics:")
        print("="*80)
        
        if not stats:
            print("📝 No statistics available yet")
            return
        
        print(f"{'User':<15} {'Quizzes':<8} {'Questions':<9} {'Correct':<8} {'Avg%':<6} {'Last Updated':<20}")
        print("-"*80)
        
        for stat in stats:
            username, total_quizzes, total_questions, total_correct, avg_score, last_updated = stat
            
            print(f"{username:<15} {total_quizzes:<8} {total_questions:<9} {total_correct:<8} {avg_score:.1f}%  {last_updated[:16]:<20}")
            
    except Exception as e:
        print(f"❌ Error reading statistics: {e}")
    finally:
        conn.close()

def get_database_summary():
    """General database summary"""
    conn = connect_to_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        # Count users
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
        active_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Count quizzes
        cursor.execute('SELECT COUNT(*) FROM quiz_results')
        total_quizzes = cursor.fetchone()[0]
        
        # Count questions
        cursor.execute('SELECT SUM(total_questions) FROM quiz_results')
        total_questions = cursor.fetchone()[0] or 0
        
        # Average score
        cursor.execute('SELECT AVG(percentage) FROM quiz_results')
        avg_score = cursor.fetchone()[0] or 0
        
        # Most popular topic
        cursor.execute('''
            SELECT topic, COUNT(*) as count 
            FROM quiz_results 
            GROUP BY topic 
            ORDER BY count DESC 
            LIMIT 1
        ''')
        popular_topic = cursor.fetchone()
        
        # Activity by day
        cursor.execute('''
            SELECT DATE(date_taken) as date, COUNT(*) as quizzes
            FROM quiz_results 
            WHERE date_taken >= date('now', '-7 days')
            GROUP BY DATE(date_taken)
            ORDER BY date DESC
        ''')
        recent_activity = cursor.fetchall()
        
        print("\n" + "="*60)
        print("🎯 Calc Master Database Summary")
        print("="*60)
        print(f"👥 Active Users: {active_users} (out of {total_users} total)")
        print(f"📊 Total Quizzes: {total_quizzes}")
        print(f"❓ Total Questions Answered: {total_questions:,}")
        print(f"📈 Average Score: {avg_score:.1f}%")
        
        if popular_topic:
            topic_name = popular_topic[0].title()
            if popular_topic[0] == 'criticalpoints':
                topic_name = 'Critical Points'
            print(f"🔥 Most Popular Topic: {topic_name} ({popular_topic[1]} quizzes)")
        
        print("\n📅 Activity Last 7 Days:")
        if recent_activity:
            for date, count in recent_activity:
                print(f"   {date}: {count} quizzes")
        else:
            print("   No activity in the last 7 days")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
    finally:
        conn.close()

def export_data_to_csv():
    """Export data to CSV file"""
    conn = connect_to_db()
    if not conn:
        return
    
    import csv
    
    cursor = conn.cursor()
    
    try:
        # Export quiz results
        cursor.execute('''
            SELECT u.username, qr.topic, qr.score, qr.total_questions, 
                   qr.percentage, qr.difficulty, qr.date_taken, qr.time_spent
            FROM quiz_results qr
            JOIN users u ON qr.user_id = u.id
            ORDER BY qr.date_taken DESC
        ''')
        
        results = cursor.fetchall()
        
        filename = f"quiz_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Username', 'Topic', 'Score', 'Total_Questions', 'Percentage', 'Difficulty', 'Date', 'Time_Spent'])
            writer.writerows(results)
        
        print(f"✅ Data exported to file: {filename}")
        print(f"📁 Location: {filename}")
        
        # Also export user summary
        cursor.execute('''
            SELECT u.username, u.email, u.display_name, u.created_at,
                   us.total_quizzes, us.total_questions, us.total_correct, us.average_score
            FROM users u
            LEFT JOIN user_stats us ON u.id = us.user_id
            WHERE u.is_active = 1
            ORDER BY us.average_score DESC
        ''')
        
        user_data = cursor.fetchall()
        
        user_filename = f"user_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(user_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Username', 'Email', 'Display_Name', 'Registered', 'Total_Quizzes', 'Total_Questions', 'Total_Correct', 'Average_Score'])
            writer.writerows(user_data)
        
        print(f"✅ User data exported to: {user_filename}")
        
    except Exception as e:
        print(f"❌ Export error: {e}")
    finally:
        conn.close()

def search_user_by_name():
    """Search for users by username or email"""
    conn = connect_to_db()
    if not conn:
        return
    
    search_term = input("Enter username or email to search: ").strip()
    if not search_term:
        print("❌ No search term provided")
        return
    
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, username, email, display_name, created_at, last_login
            FROM users
            WHERE username LIKE ? OR email LIKE ?
            ORDER BY username
        ''', (f'%{search_term}%', f'%{search_term}%'))
        
        users = cursor.fetchall()
        
        print(f"\n🔍 Search results for '{search_term}':")
        print("-" * 60)
        
        if not users:
            print("❌ No users found")
            return
        
        for user in users:
            user_id, username, email, display_name, created_at, last_login = user
            print(f"🆔 {user_id} | 👤 {username} | 📧 {email} | 🏷️ {display_name or 'N/A'}")
        
    except Exception as e:
        print(f"❌ Search error: {e}")
    finally:
        conn.close()

def show_topic_breakdown():
    """Show detailed breakdown by topic"""
    conn = connect_to_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT topic, 
                   COUNT(*) as total_attempts,
                   AVG(percentage) as avg_score,
                   MAX(percentage) as best_score,
                   MIN(percentage) as worst_score,
                   SUM(total_questions) as total_questions,
                   SUM(score) as total_correct
            FROM quiz_results
            GROUP BY topic
            ORDER BY total_attempts DESC
        ''')
        
        topics = cursor.fetchall()
        
        print("\n" + "="*80)
        print("📚 Topic Performance Breakdown:")
        print("="*80)
        
        if not topics:
            print("📝 No quiz data available")
            return
        
        print(f"{'Topic':<15} {'Attempts':<9} {'Avg%':<6} {'Best%':<6} {'Worst%':<7} {'Questions':<10} {'Correct':<8}")
        print("-"*80)
        
        for topic_data in topics:
            topic, attempts, avg_score, best, worst, total_q, correct = topic_data
            
            topic_display = topic.title()
            if topic == 'criticalpoints':
                topic_display = 'Critical Pts'
            
            accuracy = (correct / total_q * 100) if total_q > 0 else 0
            
            print(f"{topic_display:<15} {attempts:<9} {avg_score:.1f}%  {best:.1f}%  {worst:.1f}%   {total_q:<10} {correct:<8}")
        
    except Exception as e:
        print(f"❌ Error analyzing topics: {e}")
    finally:
        conn.close()

def main_menu():
    """Main menu"""
    while True:
        print("\n" + "="*50)
        print("🗄️  Calc Master Database Manager")
        print("="*50)
        print("1. 👥 Show All Users")
        print("2. 📊 Show Recent Quiz Results")
        print("3. 📈 Show User Statistics")
        print("4. 🎯 Database Summary")
        print("5. 📚 Topic Performance Breakdown")
        print("6. 🔍 Search User by Name/Email")
        print("7. 👤 Show Specific User Results")
        print("8. 💾 Export Data to CSV")
        print("0. 🚪 Exit")
        print("-"*50)
        
        choice = input("Choose option (0-8): ").strip()
        
        if choice == '1':
            show_all_users()
        elif choice == '2':
            limit = input("How many results to show? (default: 20): ").strip()
            limit = int(limit) if limit.isdigit() else 20
            show_quiz_results(limit=limit)
        elif choice == '3':
            show_user_stats()
        elif choice == '4':
            get_database_summary()
        elif choice == '5':
            show_topic_breakdown()
        elif choice == '6':
            search_user_by_name()
        elif choice == '7':
            show_all_users()
            user_id = input("\nEnter User ID: ").strip()
            if user_id.isdigit():
                show_quiz_results(user_id=int(user_id))
            else:
                print("❌ Invalid User ID")
        elif choice == '8':
            export_data_to_csv()
        elif choice == '0':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    print("🚀 Loading Calc Master Database Manager...")
    print("📁 Database file: quiz_results.db")
    main_menu()