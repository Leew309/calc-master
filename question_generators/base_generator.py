from sympy import symbols, diff, integrate, latex, sin, cos, tan, exp, log, sqrt, solve, limit
import random

class BaseQuestionGenerator:    
    def __init__(self):
        self.x = symbols('x')
        print(f"✅ {self.__class__.__name__} מוכן!")
    
    def format_question(self, question_text, options, correct_answer, explanation, question_id=None):
        return {
            "id": question_id,
            "question": question_text,
            "options": options,
            "correct": correct_answer,
            "explanation": explanation
        }
    
    def generate_wrong_answers(self, correct_answer, common_wrongs=None):
        if common_wrongs is None:
            common_wrongs = ["\\( 0 \\)", "\\( 1 \\)", "\\( x \\)", "\\( 2x \\)"]
        
        wrong_answers = []
        for wrong in common_wrongs:
            if wrong != correct_answer:
                wrong_answers.append(wrong)
        
        return wrong_answers[:3]  
    
    def shuffle_options(self, correct_answer, wrong_answers):
        all_options = [correct_answer] + wrong_answers
        random.shuffle(all_options)
        return all_options