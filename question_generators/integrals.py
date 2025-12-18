from .base_generator import BaseQuestionGenerator
from sympy import integrate, diff, latex, sin, cos, exp, log, sqrt, simplify, pi, atan, ln
import random

class IntegralsGenerator(BaseQuestionGenerator):    
    def __init__(self):
        super().__init__()
        
        # רמת קושי קלה 🟢 - אינטגרלים בסיסיים
        self.easy_functions = [
            self.x, self.x**2, self.x**3, self.x**4,
            2*self.x, 3*self.x**2, 4*self.x**3,
            sin(self.x), cos(self.x), exp(self.x),
            1/self.x,  # ln(x)
            1, 2, 3  # קבועים
        ]
        
        # רמת קושי בינונית 🟡 - חזרות עם החלפת משתנה פשוטה
        self.medium_functions = [
            2*self.x + 1,  # ∫(2x+1) dx
            (2*self.x + 1)**2,  # ∫(2x+1)² dx
            (self.x**2 + 1)**2,  # ∫(x²+1)² dx
            sin(2*self.x), cos(2*self.x),  # ∫sin(2x) dx
            exp(2*self.x), exp(-self.x),   # ∫e^(2x) dx
            1/(2*self.x + 1),  # ∫1/(2x+1) dx
            self.x*exp(self.x**2),  # ∫x·e^(x²) dx
            self.x/(self.x**2 + 1),  # ∫x/(x²+1) dx - החלפת משתנה
            2*self.x/(self.x**2 + 1)**2  # ∫2x/(x²+1)² dx
        ]
        
        # רמת קושי קשה 🔴 - אינטגרציה בחלקים ושיטות מתקדמות
        self.hard_functions = [
            self.x*sin(self.x),     # ∫x·sin(x) dx - בחלקים
            self.x*cos(self.x),     # ∫x·cos(x) dx - בחלקים  
            self.x*exp(self.x),     # ∫x·e^x dx - בחלקים
            self.x**2*exp(self.x),  # ∫x²·e^x dx - בחלקים פעמיים
            log(self.x),            # ∫ln(x) dx - בחלקים
            self.x*log(self.x),     # ∫x·ln(x) dx - בחלקים
            1/(self.x**2 + 1),      # ∫1/(x²+1) dx = arctan(x)
            1/sqrt(1 - self.x**2),  # ∫1/√(1-x²) dx = arcsin(x)
            exp(self.x)*sin(self.x) # ∫e^x·sin(x) dx - בחלקים מורכב
        ]
        
        # שם הרמות
        self.difficulty_names = {
            'easy': 'קל 🟢',
            'medium': 'בינוני 🟡', 
            'hard': 'קשה 🔴'
        }
    
    def normalize_expression(self, expr):
        """מנרמל ביטוי לפורמט עקבי"""
        try:
            simplified = simplify(expr)
            return simplified
        except:
            return expr
    
    def generate_questions(self, count=10, difficulty='mixed'):
        questions = []
        
        if difficulty == 'easy':
            functions_pool = self.easy_functions
        elif difficulty == 'medium':
            functions_pool = self.medium_functions
        elif difficulty == 'hard':
            functions_pool = self.hard_functions
        else:  # mixed
            functions_pool = self.easy_functions + self.medium_functions + self.hard_functions
        
        for i in range(count):
            func = random.choice(functions_pool)
            current_difficulty = self._identify_difficulty(func)
            
            try:
                correct_integral = integrate(func, self.x)
                correct_integral = self.normalize_expression(correct_integral)
                correct_latex = f"\\( {latex(correct_integral)} + C \\)"
                
                print(f"פונקציה: {latex(func)} | קושי: {current_difficulty}")
                print(f"אינטגרל: {latex(correct_integral)} + C")
                
                wrong_answers = self._generate_smart_wrong_answers(func, correct_integral, current_difficulty)
                all_options = self.shuffle_options(correct_latex, wrong_answers)
                explanation = self._generate_detailed_explanation(func, correct_integral, current_difficulty)
                
                question = self.format_question(
                    question_text=f"מה האינטגרל של \\( \\int {latex(func)} \\, dx \\)? ({self.difficulty_names[current_difficulty]})",
                    options=all_options,
                    correct_answer=correct_latex,
                    explanation=explanation,
                    question_id=i + 1
                )
                
                questions.append(question)
                
            except Exception as e:
                print(f"שגיאה בחישוב אינטגרל של {latex(func)}: {e}")
                questions.append(self._create_simple_integral_question(i + 1))
        
        return questions
    
    def _identify_difficulty(self, func):
        """זיהוי רמת הקושי של פונקציה"""
        if func in self.easy_functions:
            return 'easy'
        elif func in self.medium_functions:
            return 'medium'
        elif func in self.hard_functions:
            return 'hard'
        else:
            return 'easy'  # ברירת מחדל

    def _generate_detailed_explanation(self, func, integral, difficulty):
        """יצירת הסבר מפורט לפי רמת קושי"""
        base_explanation = f"האינטגרל של \\( {latex(func)} \\) הוא \\( {latex(integral)} + C \\)"
        
        func_str = str(func)
        
        if difficulty == 'easy':
            if func == self.x:
                return base_explanation + ". כלל החזקה: \\( \\int x^n dx = \\frac{x^{n+1}}{n+1} + C \\)"
            elif 'sin' in func_str:
                return base_explanation + ". \\( \\int \\sin(x) dx = -\\cos(x) + C \\)"
            elif 'cos' in func_str:
                return base_explanation + ". \\( \\int \\cos(x) dx = \\sin(x) + C \\)"
            elif 'exp' in func_str:
                return base_explanation + ". \\( \\int e^x dx = e^x + C \\)"
            elif '1/x' in func_str:
                return base_explanation + ". \\( \\int \\frac{1}{x} dx = \\ln|x| + C \\)"
        
        elif difficulty == 'medium':
            if 'sin(2' in func_str or 'cos(2' in func_str:
                return base_explanation + ". החלפת משתנה: \\( u = 2x, du = 2dx \\)"
            elif 'exp(2' in func_str:
                return base_explanation + ". החלפת משתנה: \\( u = 2x, du = 2dx \\)"
            elif '2*x + 1' in func_str:
                return base_explanation + ". החלפת משתנה: \\( u = 2x + 1, du = 2dx \\)"
            else:
                return base_explanation + ". שימוש בהחלפת משתנה או כלל השרשרת הפוך"
        
        elif difficulty == 'hard':
            if '*sin(' in func_str or '*cos(' in func_str or '*exp(' in func_str:
                return base_explanation + ". שימוש באינטגרציה בחלקים: \\( \\int u dv = uv - \\int v du \\)"
            elif 'log(' in func_str:
                return base_explanation + ". שימוש באינטגרציה בחלקים עם \\( u = \\ln(x), dv = dx \\)"
            elif 'x**2 + 1' in func_str:
                return base_explanation + ". אינטגרל טריגונומטרי: \\( \\int \\frac{1}{x^2+1} dx = \\arctan(x) + C \\)"
            else:
                return base_explanation + ". שימוש בשיטות אינטגרציה מתקדמות"
        
        return base_explanation

    def _generate_smart_wrong_answers(self, func, correct_integral, difficulty):
        """יוצר תשובות שגויות חכמות לאינטגרלים - ללא כפילויות"""
        wrong_answers = []
        correct_latex = f"\\( {latex(correct_integral)} + C \\)"
        
        try:
            derivative = diff(func, self.x)
            derivative = self.normalize_expression(derivative)
            derivative_latex = f"\\( {latex(derivative)} + C \\)"
            if derivative_latex != correct_latex:
                wrong_answers.append(derivative_latex)
        except:
            pass
        
        func_latex = f"\\( {latex(func)} + C \\)"
        if func_latex != correct_latex and func_latex not in wrong_answers:
            wrong_answers.append(func_latex)
        
        if difficulty == 'easy':
            if func == self.x**2:
                candidate = "\\( x^3 + C \\)"  
                if candidate not in wrong_answers and candidate != correct_latex:
                    wrong_answers.append(candidate)
            elif func == self.x:
                candidate = "\\( x^2 + C \\)"  
                if candidate not in wrong_answers and candidate != correct_latex:
                    wrong_answers.append(candidate)
            elif func == 3*self.x**2:
                candidate = "\\( 3x^3 + C \\)"  
                if candidate not in wrong_answers and candidate != correct_latex:
                    wrong_answers.append(candidate)
        
        elif difficulty == 'medium':
            if 'sin(2' in str(func):
                candidate = "\\( -\\cos(2x) + C \\)" 
                if candidate not in wrong_answers and candidate != correct_latex:
                    wrong_answers.append(candidate)
            elif 'cos(2' in str(func):
                candidate = "\\( \\sin(2x) + C \\)"  
                if candidate not in wrong_answers and candidate != correct_latex:
                    wrong_answers.append(candidate)
        
        elif difficulty == 'hard':
            if '*' in str(func):
                candidate = "\\( 0 + C \\)"  
                if candidate not in wrong_answers and candidate != correct_latex:
                    wrong_answers.append(candidate)
        
        common_wrong = [
            "\\( 0 + C \\)", 
            "\\( 1 + C \\)", 
            "\\( x + C \\)", 
            "\\( x^2 + C \\)",
            "\\( \\frac{x^2}{2} + C \\)",
            "\\( 2x + C \\)",
            "\\( -x + C \\)",
            "\\( \\sin(x) + C \\)",
            "\\( \\cos(x) + C \\)",
            "\\( e^x + C \\)",
            "\\( \\ln(x) + C \\)"
        ]
        
        for wrong in common_wrong:
            if len(wrong_answers) >= 3:
                break
            if wrong not in wrong_answers and wrong != correct_latex:
                wrong_answers.append(wrong)
        
        while len(wrong_answers) < 3:
            backup_answers = [
                f"\\( {random.randint(1,5)}x + C \\)",
                f"\\( \\frac{{x^{random.randint(2,4)}}}{{{random.randint(2,4)}}} + C \\)",
                f"\\( {random.randint(1,3)}x^{random.randint(2,3)} + C \\)",
                "\\( -\\sin(x) + C \\)",
                "\\( -\\cos(x) + C \\)"
            ]
            for backup in backup_answers:
                if backup not in wrong_answers and backup != correct_latex:
                    wrong_answers.append(backup)
                    break
            if len(wrong_answers) >= 3:
                break
        
        return wrong_answers[:3]  

    def shuffle_options(self, correct_answer, wrong_answers):
 
        unique_wrong = []
        for wrong in wrong_answers:
            if wrong != correct_answer and wrong not in unique_wrong:
                unique_wrong.append(wrong)
        
        while len(unique_wrong) < 3:
            backup = f"\\( {random.randint(1,10)} + C \\)"
            if backup != correct_answer and backup not in unique_wrong:
                unique_wrong.append(backup)
        
        all_options = [correct_answer] + unique_wrong[:3]
        random.shuffle(all_options)
        return all_options

    def _create_simple_integral_question(self, question_id):
        """יוצר שאלה פשוטה במקרה של שגיאה"""
        return self.format_question(
            question_text="מה האינטגרל של \\( \\int x \\, dx \\)? (קל 🟢)",
            options=["\\( \\frac{x^2}{2} + C \\)", "\\( x^2 + C \\)", "\\( 1 + C \\)", "\\( 2x + C \\)"],
            correct_answer="\\( \\frac{x^2}{2} + C \\)",
            explanation="האינטגרל של \\( x \\) הוא \\( \\frac{x^2}{2} + C \\). כלל החזקה: \\( \\int x^n dx = \\frac{x^{n+1}}{n+1} + C \\)",
            question_id=question_id
        )

    def generate_easy_questions(self, count=10):
        return self.generate_questions(count, 'easy')

    def generate_medium_questions(self, count=10):
        return self.generate_questions(count, 'medium')

    def generate_hard_questions(self, count=10):
        return self.generate_questions(count, 'hard')