from .base_generator import BaseQuestionGenerator
from sympy import latex, sin, cos, exp, sqrt, limit, oo, log, tan, simplify, sympify
import random

class LimitsGenerator(BaseQuestionGenerator):
    """מחולל שאלות גבולות עם רמות קושי"""
    
    def __init__(self):
        super().__init__()
        
        # רמת קושי קלה 🟢 - חזרות ישירות (רציפות)
        self.easy_cases = [
            (2*self.x + 3, 2, "7", "חזרה ישירה"),
            (self.x**2, 3, "9", "חזרה ישירה"),
            (self.x**2 + 2*self.x, 1, "3", "חזרה ישירה"),
            (3*self.x - 1, 2, "5", "חזרה ישירה"),
            (self.x + 5, 1, "6", "חזרה ישירה"),
            (self.x**2 - 4, 1, "-3", "חזרה ישירה"),
            (2*self.x**2 + 1, 2, "9", "חזרה ישירה"),
            (-self.x + 4, 3, "1", "חזרה ישירה"),
            (self.x**3, 2, "8", "חזרה ישירה"),
            (4*self.x - 7, 3, "5", "חזרה ישירה")
        ]
        
        # רמת קושי בינונית 🟡 - צורות אי-וודאות פשוטות 0/0
        self.medium_cases = [
            ((self.x**2 - 1)/(self.x - 1), 1, "2", "פישוט x+1"),
            ((self.x**2 - 4)/(self.x - 2), 2, "4", "פישוט x+2"),
            ((self.x**2 - 9)/(self.x - 3), 3, "6", "פישוט x+3"),
            ((self.x**3 - 8)/(self.x - 2), 2, "12", "פישוט x²+2x+4"),
            ((2*self.x**2 - 8)/(self.x - 2), 2, "8", "פישוט 2(x+2)"),
            # גבולות טריגונומטריים בסיסיים
            (sin(self.x)/self.x, 0, "1", "גבול טריגונומטרי מפורסם"),
            ((1 - cos(self.x))/self.x**2, 0, "1/2", "גבול טריגונומטרי"),
            # גבולות עם שורשים
            ((sqrt(self.x + 1) - 1)/self.x, 0, "1/2", "רציונליזציה"),
            ((sqrt(self.x + 4) - 2)/(self.x), 0, "1/4", "רציונליזציה")
        ]
        
        # רמת קושי קשה 🔴 - L'Hospital, גבולות לאינסוף, צורות מורכבות
        self.hard_cases = [
            ((self.x**2 + 1)/(2*self.x**2 + 3), oo, "1/2", "גבול לאינסוף - חלוקה בחזקה הגבוהה"),
            ((3*self.x**3 + 2*self.x)/(self.x**3 - 1), oo, "3", "גבול לאינסוף"),
            ((self.x + 1)/(self.x**2 + 1), oo, "0", "מונה מדרגה נמוכה"),
            ((2*self.x**2)/(self.x + 1), oo, "∞", "מונה מדרגה גבוהה"),
            # L'Hospital cases
            (exp(self.x)/self.x, oo, "∞", "L'Hospital"),
            (log(self.x)/self.x, oo, "0", "L'Hospital"),
            (self.x*exp(-self.x), oo, "0", "L'Hospital"),
            (1/self.x, 0, "±∞", "גבול צדדי"),
            (abs(self.x)/self.x, 0, "±1", "גבול צדדי"),
            ((exp(self.x) - 1)/self.x, 0, "1", "L'Hospital או טור טיילור")
        ]
        
        self.difficulty_names = {
            'easy': 'קל 🟢',
            'medium': 'בינוני 🟡', 
            'hard': 'קשה 🔴'
        }
    
    def generate_questions(self, count=10, difficulty='mixed'):
        """יוצר שאלות גבולות לפי רמת קושי"""
        questions = []
        
        if difficulty == 'easy':
            cases_pool = self.easy_cases
        elif difficulty == 'medium':
            cases_pool = self.medium_cases
        elif difficulty == 'hard':
            cases_pool = self.hard_cases
        else:  # mixed
            cases_pool = self.easy_cases + self.medium_cases + self.hard_cases
        
        for i in range(count):
            if len(cases_pool) > 0:
                case = random.choice(cases_pool)
                func, point, expected_answer, method = case
                current_difficulty = self._identify_case_difficulty(case)
            else:
                func = 2*self.x + 1
                point = 1
                expected_answer = "3"
                method = "חזרה ישירה"
                current_difficulty = 'easy'
            
            try:
                if point == oo:
                    calculated_result = limit(func, self.x, oo)
                    point_str = "\\infty"
                else:
                    calculated_result = limit(func, self.x, point)
                    point_str = str(point)
                
                if calculated_result is not None and str(calculated_result) != 'nan':
                    correct_answer = str(calculated_result)
                    if correct_answer == 'oo':
                        correct_answer = "∞"
                    elif correct_answer == '-oo':
                        correct_answer = "-∞"
                else:
                    correct_answer = expected_answer
                    
            except:
                correct_answer = expected_answer
                point_str = str(point) if point != oo else "\\infty"
            
            print(f"פונקציה: {latex(func)} | נקודה: {point} | תוצאה: {correct_answer} | קושי: {current_difficulty}")
            
            question_text = f"חשב את הגבול: \\( \\lim_{{x \\to {point_str}}} {latex(func)} \\) ({self.difficulty_names[current_difficulty]})"
            wrong_answers = self._generate_wrong_answers(correct_answer, current_difficulty)
            all_options = self.shuffle_options(correct_answer, wrong_answers)
            explanation = self._generate_detailed_explanation(func, point, correct_answer, method, current_difficulty)
            
            question = self.format_question(
                question_text=question_text,
                options=all_options,
                correct_answer=correct_answer,
                explanation=explanation,
                question_id=i + 1
            )
            
            questions.append(question)
        
        return questions
    
    def _identify_case_difficulty(self, case):
        """זיהוי רמת הקושי של מקרה"""
        if case in self.easy_cases:
            return 'easy'
        elif case in self.medium_cases:
            return 'medium'
        elif case in self.hard_cases:
            return 'hard'
        else:
            return 'easy'
    
    def _generate_detailed_explanation(self, func, point, result, method, difficulty):
        point_str = str(point) if point != oo else "\\infty"
        base_explanation = f"כאשר \\( x \\to {point_str} \\), הגבול של \\( {latex(func)} \\) הוא \\( {result} \\)"
        
        if difficulty == 'easy':
            return base_explanation + f". {method} - הפונקציה רציפה בנקודה זו."
        
        elif difficulty == 'medium':
            if "פישוט" in method:
                return base_explanation + f". צורת אי-וודאות 0/0, פותרים על ידי {method}."
            elif "טריגונומטרי" in method:
                return base_explanation + ". שימוש בגבול טריגונומטרי מפורסם."
            elif "רציונליזציה" in method:
                return base_explanation + ". פותרים על ידי רציונליזציה של המונה."
            else:
                return base_explanation + f". {method}."
        
        elif difficulty == 'hard':
            if point == oo:
                return base_explanation + ". בגבולות לאינסוף, מחלקים במעלה הגבוהה ביותר."
            elif "L'Hospital" in method:
                return base_explanation + ". צורת אי-וודאות, פותרים עם כלל לופיטל."
            elif "צדדי" in method:
                return base_explanation + ". צריך לבדוק גבולות צדדיים."
            else:
                return base_explanation + f". {method}."
        
        return base_explanation
    
    def _generate_wrong_answers(self, correct_answer, difficulty):
        """יוצר תשובות שגויות לגבולות לפי רמת קושי"""
        
        if difficulty == 'easy':
            wrong_options = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "-1", "-2"]
        
        elif difficulty == 'medium':
            wrong_options = ["0", "1", "∞", "לא קיים", "1/2", "2", "-1", "1/3", "3"]
        
        elif difficulty == 'hard':
            wrong_options = ["0", "1", "∞", "-∞", "לא קיים", "1/2", "-1/2", "e", "ln(2)"]
        
        else:
            wrong_options = ["0", "1", "2", "∞", "לא קיים", "-1"]
        
        wrong_answers = [w for w in wrong_options if w != correct_answer]
        return random.sample(wrong_answers, min(3, len(wrong_answers)))
    
    def generate_easy_questions(self, count=10):
        return self.generate_questions(count, 'easy')
    
    def generate_medium_questions(self, count=10):
        return self.generate_questions(count, 'medium')
    
    def generate_hard_questions(self, count=10):
        return self.generate_questions(count, 'hard')