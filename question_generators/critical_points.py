from .base_generator import BaseQuestionGenerator
from sympy import diff, latex, solve, sin, cos, exp, log, pi, simplify
import random

class CriticalPointsGenerator(BaseQuestionGenerator):
    
    def __init__(self):
        super().__init__()
        
        # רמת קושי קלה 🟢 - פונקציות ריבועיות ומעוקבות פשוטות
        self.easy_functions = [
            (self.x**2, "x = 0", "פרבולה פשוטה"),
            (self.x**2 + 2*self.x, "x = -1", "פרבולה עם הזזה"),
            (self.x**2 - 4*self.x + 3, "x = 2", "פרבולה עם מינימום"),
            (-self.x**2 + 4*self.x - 3, "x = 2", "פרבולה הפוכה עם מקסימום"),
            (self.x**2 + 6*self.x + 8, "x = -3", "פרבולה עם מינימום"),
            (-self.x**2 + 2*self.x + 1, "x = 1", "פרבולה הפוכה"),
            (2*self.x**2 - 8*self.x + 6, "x = 2", "פרבולה עם מקדם"),
            (self.x**2 - 6*self.x + 5, "x = 3", "פרבולה"),
            (-2*self.x**2 + 4*self.x, "x = 1", "פרבולה הפוכה עם מקדם"),
            (self.x**2 + 4*self.x - 5, "x = -2", "פרבולה עם מינימום")
        ]
        
        # רמת קושי בינונית 🟡 - פונקציות מעוקבות ופולינומים מדרגה 4
        self.medium_functions = [
            (self.x**3 - 3*self.x**2, "x = 0, 2", "מעוקב פשוט"),
            (self.x**3 - 3*self.x, "x = -1, 1", "מעוקב עם שתי נקודות"),
            (self.x**3 + 3*self.x**2 - 9*self.x, "x = -3, 1", "מעוקב עם מקדמים"),
            (self.x**3 - 6*self.x**2 + 9*self.x, "x = 1, 3", "מעוקב מורכב"),
            (self.x**4 - 4*self.x**2, "x = -√2, 0, √2", "פולינום מדרגה 4"),
            (self.x**4 - 2*self.x**2 + 1, "x = -1, 0, 1", "פולינום זוגי"),
            (2*self.x**3 - 6*self.x**2 + 6*self.x, "x = 1", "מעוקב עם נקודת פיתול"),
            (self.x**3 - 12*self.x + 16, "x = -2, 2", "מעוקב עם שורש"),
            (-self.x**3 + 3*self.x**2, "x = 0, 2", "מעוקב שלילי"),
            (self.x**4 - 8*self.x**2 + 16, "x = -2, 0, 2", "פולינום מדרגה 4 מורכב")
        ]
        
        # רמת קושי קשה 🔴 - פונקציות עם אקספוננט, לוגריתם וטריגונומטריה
        self.hard_functions = [
            (self.x*exp(-self.x), "x = 1", "מכפלה עם אקספוננט"),
            (self.x**2*exp(-self.x), "x = 0, 2", "פולינום כפול אקספוננט"),
            (self.x - log(self.x), "x = 1", "מכפלה עם לוגריתם"), 
            (log(self.x) - self.x, "x = 1", "לוגריתם מינוס ליניארי"),
            (self.x**2*log(self.x), "x = 1/√e", "פולינום כפול לוגריתם"),
            (exp(self.x) - self.x, "x = 0", "אקספוננט מינוס ליניארי"),
            (sin(self.x) + cos(self.x), "x = 3π/4 + 2πn", "סכום טריגונומטרי"),
            (self.x*sin(self.x), "x = tan(x)", "מכפלה טריגונומטרית מורכבת"),
            (self.x**2/(self.x**2 + 1), "x = 0", "פונקציית רציונלית"),
            (log(self.x**2 + 1), "x = 0", "לוגריתם של פולינום")
        ]
        
        # שם הרמות
        self.difficulty_names = {
            'easy': 'קל 🟢',
            'medium': 'בינוני 🟡', 
            'hard': 'קשה 🔴'
        }
    
    def generate_questions(self, count=10, difficulty='mixed'):
        """יוצר שאלות נקודות קיצון לפי רמת קושי"""
        questions = []
        
        # בחירת פונקציות לפי רמת קושי
        if difficulty == 'easy':
            functions_pool = self.easy_functions
        elif difficulty == 'medium':
            functions_pool = self.medium_functions
        elif difficulty == 'hard':
            functions_pool = self.hard_functions
        else:  # mixed
            functions_pool = self.easy_functions + self.medium_functions + self.hard_functions
        
        for i in range(count):
            if len(functions_pool) > 0:
                func_data = random.choice(functions_pool)
                func, expected_answer, method = func_data
                current_difficulty = self._identify_function_difficulty(func_data)
            else:
                func = self.x**2
                expected_answer = "x = 0"
                method = "פרבולה פשוטה"
                current_difficulty = 'easy'
            
            try:
                derivative = diff(func, self.x)
                
                # ניסיון לפתור את המשוואה f'(x) = 0
                try:
                    critical_points = solve(derivative, self.x)
                    if critical_points:
                        # המרה לפורמט יפה
                        points_str = self._format_critical_points(critical_points)
                        if points_str and points_str != "אין פתרון":
                            calculated_answer = points_str
                        else:
                            calculated_answer = expected_answer
                    else:
                        calculated_answer = "אין נקודות קיצון"
                except:
                    calculated_answer = expected_answer
                    
            except:
                calculated_answer = expected_answer
                derivative = diff(func, self.x)
            
            print(f"פונקציה: {latex(func)} | נקודות: {calculated_answer} | קושי: {current_difficulty}")
            
            wrong_answers = self._generate_wrong_answers(calculated_answer, current_difficulty)
            all_options = self.shuffle_options(calculated_answer, wrong_answers)
            explanation = self._generate_detailed_explanation(func, derivative, calculated_answer, method, current_difficulty)
            
            question = self.format_question(
                question_text=f"מהן נקודות הקיצון של \\( f(x) = {latex(func)} \\)? ({self.difficulty_names[current_difficulty]})",
                options=all_options,
                correct_answer=calculated_answer,
                explanation=explanation,
                question_id=i + 1
            )
            
            questions.append(question)
        
        return questions
    
    def _identify_function_difficulty(self, func_data):
        """זיהוי רמת הקושי של פונקציה"""
        if func_data in self.easy_functions:
            return 'easy'
        elif func_data in self.medium_functions:
            return 'medium'
        elif func_data in self.hard_functions:
            return 'hard'
        else:
            return 'easy'
    
    def _format_critical_points(self, points):
        """עיצוב נקודות קיצון לפורמט יפה"""
        if not points:
            return "אין נקודות קיצון"
        
        try:
            formatted_points = []
            for point in points:
                point_simplified = simplify(point)
                if point_simplified.is_real:
                    formatted_points.append(str(point_simplified))
            
            if formatted_points:
                return "x = " + ", ".join(formatted_points)
            else:
                return "אין נקודות קיצון ממשיות"
                
        except:
            return "אין פתרון"
    
    def _generate_detailed_explanation(self, func, derivative, result, method, difficulty):
        """יצירת הסבר מפורט לפי רמת קושי"""
        base_explanation = f"\\( f'(x) = {latex(derivative)} \\) מתאפסת ב-{result}"
        
        if difficulty == 'easy':
            return base_explanation + f". {method} - נגזרת פולינום ופתירת משוואה ליניארית/ריבועית פשוטה."
        
        elif difficulty == 'medium':
            return base_explanation + f". {method} - פתירת משוואה מעוקבת או פולינום מדרגה גבוהה."
        
        elif difficulty == 'hard':
            if 'אקספוננט' in method:
                return base_explanation + f". {method} - שימוש בכלל המכפלה עם פונקציות אקספוננציאליות."
            elif 'לוגריתם' in method:
                return base_explanation + f". {method} - שימוש בכלל המכפלה עם פונקציות לוגריתמיות."
            elif 'טריגונומטרי' in method:
                return base_explanation + f". {method} - פתירת משוואות טריגונומטריות."
            else:
                return base_explanation + f". {method} - פונקציות מורכבות הדורשות שיטות אנליטיות מתקדמות."
        
        return base_explanation
    
    def _generate_wrong_answers(self, correct_answer, difficulty):
        """יוצר תשובות שגויות לנקודות קיצון לפי רמת קושי"""
        
        if difficulty == 'easy':
            # שגיאות פשוטות בפונקציות ריבועיות
            wrong_options = [
                "x = 0", "x = 1", "x = -1", "x = 2", "x = -2", 
                "x = 3", "x = -3", "אין נקודות קיצון"
            ]
        
        elif difficulty == 'medium':
            # שגיאות בפונקציות מעוקבות
            wrong_options = [
                "x = 0", "x = 1", "x = -1", "x = 2", "x = -2",
                "x = 0, 1", "x = -1, 1", "x = 1, 2", "x = -2, 2",
                "אין נקודות קיצון"
            ]
        
        elif difficulty == 'hard':
            # שגיאות בפונקציות מורכבות
            wrong_options = [
                "x = 0", "x = 1", "x = e", "x = 1/e", "x = π/2",
                "x = ln(2)", "אין נקודות קיצון", "x = √2", 
                "x = π/4", "לא ניתן לחישוב"
            ]
        
        else:
            wrong_options = ["x = 0", "x = 1", "x = -1", "אין נקודות קיצון"]
        
        wrong_answers = [w for w in wrong_options if w != correct_answer]
        return random.sample(wrong_answers, min(3, len(wrong_answers)))
    
    def generate_easy_questions(self, count=10):
        return self.generate_questions(count, 'easy')
    
    def generate_medium_questions(self, count=10):
        return self.generate_questions(count, 'medium')
    
    def generate_hard_questions(self, count=10):
        return self.generate_questions(count, 'hard')