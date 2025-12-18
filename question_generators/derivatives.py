from .base_generator import BaseQuestionGenerator
from sympy import diff, latex, sin, cos, tan, exp, log, sqrt, integrate, simplify, nsimplify
import random

class DerivativesGenerator(BaseQuestionGenerator):
    """מחולל שאלות נגזרות עם רמות קושי"""
    
    def __init__(self):
        super().__init__()
        
        # רמת קושי קלה 🟢
        self.easy_functions = [
            self.x**2, self.x**3, self.x**4, self.x**5,
            2*self.x, 3*self.x**2, 4*self.x**3, 5*self.x**4,
            sin(self.x), cos(self.x), exp(self.x), log(self.x)
        ]
        
        # רמת קושי בינונית 🟡 (כלל שרשרת)
        self.medium_functions = [
            sin(2*self.x), cos(3*self.x), sin(self.x**2), cos(self.x**2),
            exp(2*self.x), exp(self.x**2), log(2*self.x), log(self.x**2),
            (self.x**2 + 1)**2, (self.x**2 + 1)**3, (2*self.x + 3)**2,
            sqrt(self.x**2 + 1), sqrt(2*self.x + 1)
        ]
        
        # רמת קושי קשה 🔴 (כלל מכפלה ומנה)
        self.hard_functions = [
            self.x*sin(self.x), self.x*cos(self.x), self.x*exp(self.x),
            self.x**2*sin(self.x), self.x**2*exp(self.x),
            sin(self.x)*cos(self.x), self.x*log(self.x),
            (self.x**2 + 1)/self.x, self.x/(self.x**2 + 1),
            sin(self.x)/self.x, exp(self.x)/self.x,
            log(self.x**2 + 1), self.x**2*log(self.x)
        ]
        
        # שם הרמות
        self.difficulty_names = {
            'easy': 'קל 🟢',
            'medium': 'בינוני 🟡', 
            'hard': 'קשה 🔴'
        }
    
    def normalize_expression(self, expr):
        try:
            simplified = simplify(expr)
            simplified = nsimplify(simplified, rational=False)
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
            
            correct_derivative = diff(func, self.x)
            correct_derivative = self.normalize_expression(correct_derivative)
            correct_latex = f"\\( {latex(correct_derivative)} \\)"
            
            print(f"פונקציה: {latex(func)} | קושי: {current_difficulty}")
            print(f"נגזרת: {latex(correct_derivative)}")
            
            wrong_answers = self._generate_smart_wrong_answers(func, correct_derivative)
            all_options = self.shuffle_options(correct_latex, wrong_answers)
            explanation = self._generate_detailed_explanation(func, correct_derivative, current_difficulty)
            
            question = self.format_question(
                question_text=f"מה הנגזרת של \\( f(x) = {latex(func)} \\)? ({self.difficulty_names[current_difficulty]})",
                options=all_options,
                correct_answer=correct_latex,
                explanation=explanation,
                question_id=i + 1
            )
            
            questions.append(question)
        
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
            return 'medium'  
    
    def _generate_detailed_explanation(self, func, derivative, difficulty):
        """יצירת הסבר מפורט לפי רמת קושי"""
        base_explanation = f"הנגזרת של \\( {latex(func)} \\) היא \\( {latex(derivative)} \\)"
        
        if difficulty == 'easy':
            if func == self.x**2:
                return base_explanation + ". כלל החזקה: \\( (x^n)' = n \\cdot x^{n-1} \\)"
            elif str(func).startswith('sin'):
                return base_explanation + ". הנגזרת של sin(x) היא cos(x)"
            elif str(func).startswith('cos'):
                return base_explanation + ". הנגזרת של cos(x) היא -sin(x)"
        
        elif difficulty == 'medium':
            return base_explanation + ". שימוש בכלל השרשרת: \\( (f(g(x)))' = f'(g(x)) \\cdot g'(x) \\)"
        
        elif difficulty == 'hard':
            if '*' in str(func):
                return base_explanation + ". שימוש בכלל המכפלה: \\( (u \\cdot v)' = u' \\cdot v + u \\cdot v' \\)"
            elif '/' in str(func):
                return base_explanation + ". שימוש בכלל המנה: \\( (u/v)' = \\frac{u' \\cdot v - u \\cdot v'}{v^2} \\)"
        
        return base_explanation
    
    def _generate_smart_wrong_answers(self, func, correct_derivative):
        """יוצר תשובות שגויות חכמות לנגזרות"""
        wrong_answers = []
        
        try:
            second_deriv = diff(func, self.x, 2)
            second_deriv = self.normalize_expression(second_deriv)
            if second_deriv != correct_derivative:
                wrong_answers.append(f"\\( {latex(second_deriv)} \\)")
        except:
            wrong_answers.append("\\( 0 \\)")
        
        if func != correct_derivative:
            normalized_func = self.normalize_expression(func)
            wrong_answers.append(f"\\( {latex(normalized_func)} \\)")
        else:
            wrong_answers.append("\\( x \\)")
        
        try:
            integral_func = integrate(func, self.x)
            integral_func = self.normalize_expression(integral_func)
            if integral_func != correct_derivative:
                wrong_answers.append(f"\\( {latex(integral_func)} \\)")
        except:
            wrong_answers.append("\\( x^2 \\)")
        
        common_wrong = ["\\( 0 \\)", "\\( 1 \\)", "\\( x \\)", "\\( 2x \\)"]
        for wrong in common_wrong:
            if len(wrong_answers) < 3 and wrong not in wrong_answers:
                wrong_answers.append(wrong)
        
        return wrong_answers[:3]
    
    def generate_easy_questions(self, count=10):
        return self.generate_questions(count, 'easy')
    
    def generate_medium_questions(self, count=10):
        return self.generate_questions(count, 'medium')
    
    def generate_hard_questions(self, count=10):
        return self.generate_questions(count, 'hard')