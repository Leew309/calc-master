from .derivatives import DerivativesGenerator
from .integrals import IntegralsGenerator
from .limits import LimitsGenerator
from .critical_points import CriticalPointsGenerator

# מחלקה ראשית שמאחדת את כולם
class QuestionGenerator:
    def __init__(self):
        self.derivatives = DerivativesGenerator()
        self.integrals = IntegralsGenerator()
        self.limits = LimitsGenerator()
        self.critical_points = CriticalPointsGenerator()
        print("✅ כל מחוללי השאלות מוכנים!")
    
    def generate_derivative_questions(self, count=10):
        return self.derivatives.generate_questions(count)
    
    def generate_integral_questions(self, count=10):
        return self.integrals.generate_questions(count)
    
    def generate_limit_questions(self, count=10):
        return self.limits.generate_questions(count)
    
    def generate_critical_points_questions(self, count=10):
        return self.critical_points.generate_questions(count)
    
    def generate_mixed_questions(self, count=15):
        derivatives = self.generate_derivative_questions(4)
        integrals = self.generate_integral_questions(4)
        limits = self.generate_limit_questions(4)
        critical = self.generate_critical_points_questions(3)
        
        import random
        all_questions = derivatives + integrals + limits + critical
        random.shuffle(all_questions)
        return all_questions[:count]