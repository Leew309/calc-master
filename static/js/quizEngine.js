
let questions = [];
let currentQuestionIndex = 0;
let correctCount = 0;
let totalQuestions = 0;
let quizStartTime = null;
let currentTopic = null;
let currentDifficulty = null;

async function populateQuizFromApi(containerId, apiUrl) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
    <div class="loading-wrapper">
        <div class="loading">📚 טוען שאלות...</div>
    </div>
    `;


    quizStartTime = new Date();
    currentTopic = identifyTopicFromUrl(apiUrl);
    currentDifficulty = identifyDifficultyFromUrl(apiUrl);

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const responseData = await response.json();

        if (responseData.questions && responseData.quiz_info) {
            questions = responseData.questions;
            const descElement = document.getElementById('topic-description');
            if (descElement && responseData.quiz_info.explanation) {
                descElement.textContent = responseData.quiz_info.explanation;
            }
        } else if (Array.isArray(responseData)) {
            questions = responseData;
        } else if (responseData.error) {
            container.innerHTML = `<div class="error">${responseData.error}</div>`;
            return;
        } else {
            throw new Error("פורמט נתונים לא מוכר");
        }

        const validQuestions = questions.filter(q =>
            q && typeof q === 'object' &&
            typeof q.question === 'string' &&
            Array.isArray(q.options) &&
            q.options.length > 0 &&
            typeof q.correct === 'string'
        );

        if (validQuestions.length === 0) throw new Error("אין שאלות תקינות");

        questions = validQuestions;
        totalQuestions = questions.length;
        currentQuestionIndex = 0;
        correctCount = 0;

        showCurrentQuestion(container);
    } catch (err) {
        container.innerHTML = `
            <div class="error">
                <h3>שגיאה בטעינת השאלות</h3>
                <p>${err.message}</p>
                <button onclick="location.reload()" class="retry-btn">נסה שוב</button>
                <button onclick="location.href='/'" class="home-btn">חזור לדף הבית</button>
            </div>
        `;
    }
}

function identifyTopicFromUrl(apiUrl) {
    if (apiUrl.includes('derivatives')) return 'derivatives';
    if (apiUrl.includes('integrals')) return 'integrals';
    if (apiUrl.includes('limits')) return 'limits';
    if (apiUrl.includes('criticalpoints')) return 'criticalpoints';
    if (apiUrl.includes('general')) return 'general';
    if (apiUrl.includes('personalized')) return 'personalized';
    return 'unknown';
}

function identifyDifficultyFromUrl(apiUrl) {
    if (apiUrl.includes('/easy')) return 'easy';
    if (apiUrl.includes('/medium')) return 'medium';
    if (apiUrl.includes('/hard')) return 'hard';
    return 'mixed';
}

function showCurrentQuestion(container) {
    if (currentQuestionIndex >= totalQuestions) {
        showResults(container);
        return;
    }

    const question = questions[currentQuestionIndex];
    if (!question || !question.question || !question.options) {
        currentQuestionIndex++;
        showCurrentQuestion(container);
        return;
    }

    const questionNumber = currentQuestionIndex + 1;

    container.innerHTML = `
        <div class="quiz-card">
            <div class="progress-header">
                <div class="progress-text">שאלה ${questionNumber} מתוך ${totalQuestions}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(currentQuestionIndex / totalQuestions) * 100}%"></div>
                </div>
            </div>

            <div class="question-container">
                <h2 class="question-text">${question.question}</h2>
                <div class="options-container">
                    ${question.options.map((option, index) => `
                        <button class="option-btn" onclick="selectAnswer(${index}, '${option.replace(/'/g, "&apos;")}')">
                            <span class="option-letter">${String.fromCharCode(65 + index)}</span>
                            <span class="option-text">${option}</span>
                        </button>
                    `).join('')}
                </div>
            </div>

            <div id="feedback" class="feedback hidden"></div>
            <div class="score">נכונות: ${correctCount} | שגויות: ${currentQuestionIndex - correctCount}</div>
        </div>
    `;

    if (window.MathJax && MathJax.typesetPromise) {
        MathJax.typesetPromise([container]);
    }
}

function cleanForComparison(text) {
    return text.replace(/\s+/g, ' ').trim();
}

function selectAnswer(optionIndex, selectedOption) {
    const question = questions[currentQuestionIndex];
    if (!question) return;

    const isCorrectDirect = selectedOption === question.correct;
    const isCorrectCleaned = cleanForComparison(selectedOption) === cleanForComparison(question.correct);
    const correctOptionIndex = question.options.indexOf(question.correct);
    const isCorrectByIndex = optionIndex === correctOptionIndex;

    const isCorrect = isCorrectDirect || isCorrectCleaned || isCorrectByIndex;
    if (isCorrect) correctCount++;

    document.querySelectorAll('.option-btn').forEach(btn => btn.disabled = true);

    const feedback = document.getElementById('feedback');
    
    const detailedAnalysis = generateDetailedErrorAnalysis(
        question, 
        selectedOption, 
        isCorrect, 
        currentTopic, 
        currentDifficulty
    );

feedback.innerHTML = `
    <div class="feedback-content">
        <h3 class="feedback-main-title">${isCorrect ? '✅ תשובה נכונה!' : '❌ טעית – אבל זו הזדמנות ללמוד 🙂'}</h3>

        <div class="correct-answer highlighted-box">
            <div class="section-title">✔️ התשובה הנכונה:</div>
            <div class="explanation-text">
                <span class="math-expression">${question.correct}</span>
            </div>
        </div>

        ${!isCorrect ? `
        <div class="error-analysis-section">
            <div class="highlighted-box">
                <div class="section-title">🚫 מה בחרת:</div>
                <div class="explanation-text">
                    <span class="math-expression">${selectedOption}</span>
                </div>
            </div>

            <div class="highlighted-box">
                <div class="section-title">⚠️ למה זו טעות?</div>
                <div class="explanation-text">${detailedAnalysis.whyWrong}</div>
            </div>

            <div class="highlighted-box">
                <div class="section-title">✏️ הדרך הנכונה:</div>
                <div class="explanation-text">${detailedAnalysis.correctMethod}</div>
            </div>

            <div class="highlighted-box">
                <div class="section-title">📝 שלבי הפתרון:</div>
                <div class="explanation-text">${detailedAnalysis.stepByStep}</div>
            </div>

            <div class="highlighted-box">
                <div class="section-title">💡 רעיון מרכזי:</div>
                <div class="explanation-text">${detailedAnalysis.keyInsight}</div>
            </div>

            <div class="highlighted-box">
                <div class="section-title">⚡ טעות נפוצה:</div>
                <div class="explanation-text">${detailedAnalysis.commonMistake}</div>
            </div>

            <div class="highlighted-box">
                <div class="section-title">🛡️ איך להימנע:</div>
                <div class="explanation-text">${detailedAnalysis.howToAvoid}</div>
            </div>

            <div class="highlighted-box">
                <div class="section-title">💪 תרגול מומלץ:</div>
                <div class="explanation-text">${detailedAnalysis.practiceTip}</div>
            </div>

            <div class="highlighted-box">
                <div class="section-title">🧠 טריק לזכירה:</div>
                <div class="explanation-text">${detailedAnalysis.memoryAid}</div>
            </div>
        </div>` : `
        <div class="highlighted-box success-explanation">
            <div class="section-title">✨ למה זה נכון:</div>
            <div class="explanation-text">
                ${question.explanation || detailedAnalysis?.successReason || 'השתמשת בכלל הנכון וביצעת את החישוב בצורה מדויקת!'}
            </div>
        </div>`}

        <button onclick="nextQuestion()" class="next-btn">
            ${currentQuestionIndex >= totalQuestions - 1 ? 'סיים' : 'הבא'} →
        </button>
    </div>
`;

    feedback.classList.remove('hidden');

    if (window.MathJax && MathJax.typesetPromise) {
        MathJax.typesetPromise([feedback]);
    }
}

function generateDetailedErrorAnalysis(question, userAnswer, isCorrect, topic, difficulty) {
    if (isCorrect) {
        return {
            successReason: getSuccessExplanation(question, topic)
        };
    }

    const correctAnswer = question.correct;
    const questionText = question.question;
    
    if (topic === 'derivatives') {
        return analyzeDerivativeError(questionText, userAnswer, correctAnswer, difficulty);
    } else if (topic === 'integrals') {
        return analyzeIntegralError(questionText, userAnswer, correctAnswer, difficulty);
    } else if (topic === 'limits') {
        return analyzeLimitError(questionText, userAnswer, correctAnswer, difficulty);
    } else if (topic === 'criticalpoints') {
        return analyzeCriticalPointError(questionText, userAnswer, correctAnswer, difficulty);
    } else {
        return analyzeGenericError(questionText, userAnswer, correctAnswer, difficulty);
    }
}

function getSuccessExplanation(question, topic) {
    if (topic === 'derivatives') {
        return "זיהית נכון את סוג הפונקציה והפעלת את כלל הנגזרות המתאים!";
    } else if (topic === 'integrals') {
        return "השתמשת בשיטת האינטגרציה הנכונה וזכרת להוסיף את קבוע האינטגרציה +C!";
    } else if (topic === 'limits') {
        return "זיהית נכון את סוג הגבול והשתמשת בשיטת הפתרון המתאימה!";
    } else if (topic === 'criticalpoints') {
        return "חישבת נכון את הנגזרת ופתרת נכון את המשוואה f'(x) = 0!";
    }
    return "השתמשת בכלל המתמטי הנכון וביצעת את החישוב בדיוק!";
}

function analyzeDerivativeError(questionText, userAnswer, correctAnswer, difficulty) {
    const isPolynomial = /x\^?\d*/.test(questionText);
    const isTrigonometric = /sin|cos|tan/.test(questionText);
    const isExponential = /e\^|exp/.test(questionText);
    const isLogarithmic = /ln|log/.test(questionText);
    const isChainRule = /\([^)]+\)\^?\d*/.test(questionText) || /sin\(|cos\(|exp\(/.test(questionText);
    const isProductRule = /\*/.test(questionText.replace(/\\[^}]*}/g, ''));

    if (userAnswer.includes("0")) {
        return {
            whyWrong: "נגזרת היא 0 רק עבור קבועים מתמטיים (מספרים). כל פונקציה שיש בה x תהיה לה נגזרת שאינה 0.",
            correctMethod: isPolynomial ? "השתמש בכלל החזקה: (x^n)' = n·x^(n-1)" : 
                          isTrigonometric ? "השתמש בנגזרות הטריגונומטריות" : "זהה את סוג הפונקציה והשתמש בכלל המתאים",
            stepByStep: isPolynomial ? "1. זהה את החזקה של x\n2. הורד את החזקה כמקדם\n3. הפחת 1 מהחזקה" :
                       isTrigonometric ? "1. זהה את הפונקציה הטריגונומטרית\n2. השתמש בכלל: (sin x)' = cos x, (cos x)' = -sin x" :
                       "1. זהה את סוג הפונקציה\n2. השתמש בכלל הנגזרות המתאים",
            keyInsight: "רק מספרים (כמו 5, -3, π) יש להם נגזרת 0. כל פונקציה עם x משתנה לא תהיה לה נגזרת 0.",
            commonMistake: "חושבים שנגזרת זה תמיד 0, או מבלבלים בין נגזרת לאינטגרל.",
            howToAvoid: "תמיד שאל את עצמך: האם יש במשוואה x? אם כן, הנגזרת לא תהיה 0.",
            practiceTip: "תתרגל על הפונקציות הבסיסיות: x, x², x³, sin x, cos x, e^x עד שתזכור את הנגזרות שלהן בעל פה.",
            memoryAid: "זכור: 'נגזרת = איך הפונקציה משתנה'. אם יש x, הפונקציה משתנה!"
        };
    }

    if (isPolynomial) {
        const hasWrongPower = /x\^/.test(userAnswer) && !userAnswer.includes(correctAnswer);
        if (hasWrongPower) {
            return {
                whyWrong: "שכחת לחסר 1 מהחזקה או לא הורדת את החזקה כמקדם נכון.",
                correctMethod: "כלל החזקה: (x^n)' = n·x^(n-1). קודם הורד את n כמקדם, אחר כך שים n-1 בחזקה.",
                stepByStep: "דוגמה: (x³)' = 3·x^(3-1) = 3x²\n1. החזקה המקורית: 3\n2. מקדם חדש: 3\n3. חזקה חדשה: 3-1 = 2\n4. תוצאה: 3x²",
                keyInsight: "בכלל החזקה יש שני שלבים: הורדת החזקה כמקדם + הפחתת 1 מהחזקה.",
                commonMistake: "שוכחים להפחית 1 מהחזקה או שוכחים להוריד את החזקה כמקדם.",
                howToAvoid: "תמיד בצע את שני השלבים בסדר: 1) הורד חזקה כמקדם 2) הפחת 1 מהחזקה.",
                practiceTip: "תתרגל עם פונקציות פשוטות: x², x³, x⁴ עד שהתהליך יהפוך אוטומטי.",
                memoryAid: "זכור: 'החזקה יורדת לפני, ואז מפחיתים 1'"
            };
        }
    }

    if (isTrigonometric) {
        const wrongSign = (questionText.includes('cos') && !userAnswer.includes('-')) || 
                         (questionText.includes('sin') && userAnswer.includes('-') && !questionText.includes('cos'));
        return {
            whyWrong: wrongSign ? "שכחת את הסימן המינוס בנגזרת של cos, או הוספת מינוס שלא צריך." : 
                     "לא השתמשת בכלל הנגזרות הטריגונומטריות הנכון.",
            correctMethod: "כללי נגזרות טריגונומטריות: (sin x)' = cos x, (cos x)' = -sin x, (tan x)' = sec²x",
            stepByStep: questionText.includes('sin') ? 
                       "נגזרת של sin x:\n1. זהה: sin x\n2. הנגזרת: cos x\n3. תוצאה: cos x" :
                       "נגזרת של cos x:\n1. זהה: cos x\n2. הנגזרת: -sin x (שים לב למינוס!)\n3. תוצאה: -sin x",
            keyInsight: "בנגזרת של cos תמיד יש מינוס, בנגזרת של sin אין מינוס!",
            commonMistake: "מבלבלים בין הנגזרות של sin ו-cos, או שוכחים את המינוס ב-cos.",
            howToAvoid: "תזכור: 'cos יורד עם מינוס, sin עולה ללא מינוס'",
            practiceTip: "תכתוב 20 פעם: (sin x)' = cos x, (cos x)' = -sin x",
            memoryAid: "זכור: 'CoS = מינוס (cos צולל למטה עם מינוס)'"
        };
    }

    if (isChainRule) {
        return {
            whyWrong: "לא השתמשת בכלל השרשרת או שטעית ביישום שלו.",
            correctMethod: "כלל השרשרת: אם f(x) = g(h(x)) אז f'(x) = g'(h(x)) · h'(x)",
            stepByStep: "1. זהה פונקציה חיצונית ופנימית\n2. חשב נגזרת של החיצונית (עם הפנימית בפנים)\n3. חשב נגזרת של הפנימית\n4. הכפל את שתיהן",
            keyInsight: "כלל השרשרת = נגזרת החיצונית כפול נגזרת הפנימית",
            commonMistake: "שוכחים להכפיל בנגזרת הפנימית או מתבלבלים מי חיצונית ומי פנימית.",
            howToAvoid: "תמיד זהה מה בפנים ומה בחוץ לפני תחילת החישוב.",
            practiceTip: "תתרגל עם דוגמאות פשוטות: sin(2x), (x+1)², e^(3x)",
            memoryAid: "זכור: 'חוץ כפול פנים נגזרת' - נגזרת החיצונית כפול נגזרת הפנימית"
        };
    }

    return {
        whyWrong: "לא הפעלת נכון את כללי הנגזרות הרלוונטיים לסוג הפונקציה הזו.",
        correctMethod: "זהה את סוג הפונקציה (פולינום, טריגונומטרית, אקספוננציאלית) והשתמש בכלל המתאים.",
        stepByStep: "1. זהה סוג הפונקציה\n2. בחר כלל נגזרות מתאים\n3. יישם בקפידה\n4. בדוק התוצאה",
        keyInsight: "כל סוג פונקציה יש לו כלל נגזרת ייחודי - חשוב לזהות נכון את הסוג.",
        commonMistake: "מיישמים כלל שגוי או מתבלבלים בין כללים שונים.",
        howToAvoid: "תחזק את הזיהוי של סוגי פונקציות לפני תחילת החישוב.",
        practiceTip: "תעשה טבלה של כל כללי הנגזרות ותתרגל זיהוי מהיר של סוגי פונקציות.",
        memoryAid: "זכור: 'זיהוי נכון = פתרון נכון'"
    };
}

function analyzeIntegralError(questionText, userAnswer, correctAnswer, difficulty) {
    const isMissingC = !userAnswer.includes('C') && correctAnswer.includes('C');
    const isPolynomial = /x\^?\d*/.test(questionText);
    const isTrigonometric = /sin|cos|tan/.test(questionText);
    const isWrongPower = isPolynomial && /x\^/.test(userAnswer);
    const isSubstitution = /\d*x/.test(questionText) && !/^x[^0-9]/.test(questionText);

    if (isMissingC) {
        return {
            whyWrong: "שכחת להוסיף את קבוע האינטגרציה +C. זה חובה באינטגרלים בלתי מוגדרים!",
            correctMethod: "באינטגרל בלתי מוגדר תמיד נוסיף +C בסוף כי האינטגרל מייצג משפחה של פונקציות.",
            stepByStep: "1. חשב את האינטגרל\n2. הוסף +C בסוף\n3. כתוב את התוצאה הסופית עם ה-C",
            keyInsight: "C מייצג את כל הקבועים האפשריים - כי נגזרת של קבוע היא 0.",
            commonMistake: "שוכחים את ה-C כי חושבים שזה לא חשוב, אבל זה חלק מההגדרה של אינטגרל בלתי מוגדר.",
            howToAvoid: "תמיד כתוב +C אוטומטית מיד אחרי החישוב של האינטגרל.",
            practiceTip: "תתרגל לכתוב +C בכל אינטגרל שאתה פותר, עד שזה יהפוך הרגל.",
            memoryAid: "זכור: 'אינטגרל בלי C זה כמו משפט בלי נקודה - לא שלם!'"
        };
    }

    if (isPolynomial && isWrongPower) {
        return {
            whyWrong: "לא הפעלת נכון את כלל החזקה לאינטגרלים - שכחת להוסיף 1 לחזקה או לחלק במעריך החדש.",
            correctMethod: "כלל החזקה לאינטגרלים: ∫x^n dx = x^(n+1)/(n+1) + C",
            stepByStep: "דוגמה: ∫x² dx\n1. החזקה המקורית: 2\n2. הוסף 1: 2+1 = 3\n3. חלק במעריך החדש: x³/3\n4. הוסף C: x³/3 + C",
            keyInsight: "באינטגרל מוסיפים 1 לחזקה (הפוך מנגזרת) ואז חולקים במעריך החדש.",
            commonMistake: "שוכחים לחלק במעריך החדש או מוסיפים 1 בטעות לבסיס במקום לחזקה.",
            howToAvoid: "זכור: הוסף 1 לחזקה, אחר כך חלק במעריך החדש. תמיד בסדר הזה!",
            practiceTip: "תתרגל עם x, x², x³, x⁴ עד שתזכור: x²→x³/3, x³→x⁴/4",
            memoryAid: "זכור: 'באינטגרל החזקה עולה באחד, ואז חולקים בה'"
        };
    }

    if (isTrigonometric) {
        const wrongSign = (questionText.includes('sin') && userAnswer.includes('sin')) || 
                         (questionText.includes('cos') && !userAnswer.includes('-') && correctAnswer.includes('-'));
        return {
            whyWrong: wrongSign ? "לא שמת לב לסימן הנכון באינטגרל הטריגונומטרי." : 
                     "לא השתמשת בכלל האינטגרציה הטריגונומטרי הנכון.",
            correctMethod: "אינטגרלים טריגונומטריים: ∫sin x dx = -cos x + C, ∫cos x dx = sin x + C",
            stepByStep: questionText.includes('sin') ? 
                       "∫sin x dx:\n1. זהה: sin x\n2. האינטגרל: -cos x\n3. הוסף C: -cos x + C" :
                       "∫cos x dx:\n1. זהה: cos x\n2. האינטגרל: sin x\n3. הוסף C: sin x + C",
            keyInsight: "באינטגרל של sin יש מינוס, באינטגרל של cos אין מינוס!",
            commonMistake: "מבלבלים בין אינטגרלים של sin ו-cos, או שוכחים את המינוס ב-sin.",
            howToAvoid: "תזכור: 'sin→(-cos), cos→sin' - sin מביא מינוס, cos לא.",
            practiceTip: "תכתוב 20 פעם: ∫sin x dx = -cos x + C, ∫cos x dx = sin x + C",
            memoryAid: "זכור: 'Sin בעייתי - מביא מינוס' (sin→-cos)"
        };
    }

    if (isSubstitution) {
        return {
            whyWrong: "לא התמודדת נכון עם המקדם בפונקציה - צריך להשתמש בהחלפת משתנה או לחלק במקדם.",
            correctMethod: "כשיש מקדם (כמו 2x, 3x), יש להשתמש בהחלפת משתנה או לחלק בו.",
            stepByStep: "דוגמה: ∫sin(2x) dx\nשיטה 1: u = 2x, du = 2dx\nשיטה 2: התוצאה תחולק ב-2\nתוצאה: -cos(2x)/2 + C",
            keyInsight: "כשיש מקדם בפונקציה הפנימית, התוצאה מתחלקת במקדם הזה.",
            commonMistake: "שוכחים את המקדם ולא מתייחסים אליו בחישוב.",
            howToAvoid: "תמיד שים לב למקדמים ותחשב אותם בנפרד.",
            practiceTip: "תתרגל החלפת משתנה על דוגמאות: ∫sin(2x)dx, ∫(3x+1)²dx",
            memoryAid: "זכור: 'מקדם בפנים = חלוקה בתוצאה'"
        };
    }

    return {
        whyWrong: "לא הפעלת נכון את כללי האינטגרציה או השתמשת בשיטה לא מתאימה.",
        correctMethod: "זהה את סוג הפונקציה ובחר את שיטת האינטגרציה המתאימה: כלל החזקה, החלפת משתנה, או אינטגרציה בחלקים.",
        stepByStep: "1. זהה סוג הפונקציה\n2. בחר שיטת אינטגרציה\n3. יישם בקפידה\n4. הוסף +C\n5. בדוק עם נגזרת",
        keyInsight: "אינטגרל הוא הפעולה ההפוכה לנגזרת - תמיד אפשר לבדוק את התוצאה.",
        commonMistake: "מיישמים שיטה שגויה או שוכחים שלבים חשובים בתהליך.",
        howToAvoid: "תמיד בדוק את התוצאה על ידי נגזרת - אם נכון, הנגזרת תחזיר את הפונקציה המקורית.",
        practiceTip: "תתרגל על הפונקציות הבסיסיות ותלמד את השיטות השונות לאינטגרציה.",
        memoryAid: "זכור: 'אינטגרל + נגזרת = זהות'"
    };
}

function analyzeLimitError(questionText, userAnswer, correctAnswer, difficulty) {
    const isDirectSubstitution = difficulty === 'easy';
    const isInfinity = questionText.includes('∞') || questionText.includes('infty');
    const isZero = userAnswer === "0" && correctAnswer !== "0";
    const isIndeterminate = questionText.includes('/');
    const isTrigonometric = /sin|cos|tan/.test(questionText);

    if (isDirectSubstitution && isZero) {
        return {
            whyWrong: "בגבולות עם החלפה ישירה לא מציבים 0 אוטומטיט - צריך להציב את הערך הנתון.",
            correctMethod: "בגבולות פשוטים: מציבים את הערך שאליו x שואף במקום x בפונקציה.",
            stepByStep: "דוגמה: lim(x→2) x²+1\n1. הציב x=2: 2²+1\n2. חשב: 4+1\n3. תוצאה: 5",
            keyInsight: "אם הפונקציה רציפה בנקודה, הגבול שווה לערך הפונקציה באותה נקודה.",
            commonMistake: "חושבים שגבול זה תמיד 0 או לא מציבים את הערך הנכון.",
            howToAvoid: "תמיד בדוק: האם הפונקציה מוגדרת בנקודה? אם כן, הציב ישירות.",
            practiceTip: "תתרגל החלפה ישירה עם פולינומים פשוטים: x+1, x²-3, 2x+5",
            memoryAid: "זכור: 'רציף = הציב ישירות'"
        };
    }

    if (isInfinity) {
        return {
            whyWrong: "בגבולות לאינסוף לא התמקדת במעלות הגבוהות ביותר במונה ובמכנה.",
            correctMethod: "בגבולות לאינסוף: חלק את המונה והמכנה במעלה הגבוהה ביותר.",
            stepByStep: "דוגמה: lim(x→∞) (2x²+1)/(x²+3)\n1. מעלה גבוהה: x²\n2. חלק הכל ב-x²: (2+1/x²)/(1+3/x²)\n3. כש-x→∞: (2+0)/(1+0) = 2",
            keyInsight: "לאינסוף, רק המעלות הגבוהות משפיעות - השאר הופך ל-0.",
            commonMistake: "לא מזהים את המעלה הגבוהה או לא מבצעים את החלוקה נכון.",
            howToAvoid: "תמיד זהה קודם את המעלה הגבוהה במונה ובמכנה.",
            practiceTip: "תתרגל עם פונקציות רציונליות פשוטות ובדוק איך המעלות משפיעות.",
            memoryAid: "זכור: 'באינסוף הגדול מנצח' - המעלה הגבוהה קובעת"
        };
    }

    if (isTrigonometric) {
        return {
            whyWrong: "לא השתמשת בגבולות הטריגונומטריים המפורסמים או בהצבה לא נכונה.",
            correctMethod: "הגבול המפורסם: lim(x→0) sin(x)/x = 1. גבולות אחרים נגזרים ממנו.",
            stepByStep: "לגבול sin(x)/x:\n1. זהה את הצורה sin(משהו)/(אותו משהו)\n2. השתמש בגבול המפורסם\n3. אם יש מקדמים, טפל בהם בנפרד",
            keyInsight: "הגבול sin(x)/x = 1 הוא אחד הגבולות הבסיסיים ביותר בחשבון דיפרנציאלי.",
            commonMistake: "מנסים הצבה ישירה ב-0 במקום להשתמש בגבול המפורסם.",
            howToAvoid: "תזכור את הגבולות הטריגונומטריים המפורסמים ותזהה מתי להשתמש בהם.",
            practiceTip: "תלמד בעל פה: lim(x→0) sin(x)/x = 1, lim(x→0) (1-cos(x))/x² = 1/2",
            memoryAid: "זכור: 'Sin על X באפס שווה אחד' (sin(x)/x → 1)"
        };
    }

    if (userAnswer === "∞" && correctAnswer !== "∞") {
        return {
            whyWrong: "לא כל גבול ששואף לאינסוף נותן תוצאה אינסופית - צריך לבדוק בקפידה.",
            correctMethod: "בדוק את היחס בין מעלות המונה והמכנה, או פתור צורות אי-וודאות אם יש.",
            stepByStep: "1. בדוק אם יש צורת אי-וודאות\n2. אם כן - פתור אותה\n3. אם לא - בדוק יחסי מעלות\n4. חשב את התוצאה",
            keyInsight: "גבול יכול להיות מספר סופי, אינסוף, או לא קיים - תלוי בפונקציה.",
            commonMistake: "מניחים שגבול לאינסוף תמיד נותן אינסוף.",
            howToAvoid: "תמיד בצע את החישוב המלא ואל תנחש על בסיס אינטואיציה.",
            practiceTip: "תתרגל גבולות עם תוצאות שונות: 0, מספרים, אינסוף.",
            memoryAid: "זכור: 'גבול = תוצאה מדויקת, לא ניחוש'"
        };
    }

    return {
        whyWrong: "לא זיהית נכון את סוג הגבול או לא השתמשת בשיטת הפתרון המתאימה.",
        correctMethod: "זהה תחילה אם זה גבול ישיר, צורת אי-וודאות, או גבול לאינסוף, ואז פעל בהתאם.",
        stepByStep: "1. נסה הצבה ישירה\n2. אם יוצא 0/0 או ∞/∞ - פתור אי-וודאות\n3. אם גבול לאינסוף - חלק במעלה גבוהה\n4. חשב תוצאה",
        keyInsight: "כל סוג גבול דורש גישה שונה - חשוב לזהות נכון את הסוג.",
        commonMistake: "מנסים שיטה אחת לכל הגבולות במקום להתאים לסוג הספציפי.",
        howToAvoid: "תתרגל זיהוי מהיר של סוגי גבולות שונים.",
        practiceTip: "תעשה רשימה של סוגי הגבולות השונים והשיטות המתאימות לכל סוג.",
        memoryAid: "זכור: 'זיהוי נכון = שיטה נכונה = תוצאה נכונה'"
    };
}

function analyzeCriticalPointError(questionText, userAnswer, correctAnswer, difficulty) {
    const noPoints = userAnswer === "אין נקודות קיצון";
    const wrongPoints = userAnswer.includes("x =") && correctAnswer.includes("x =") && userAnswer !== correctAnswer;
    const zeroOnly = userAnswer === "x = 0" && !correctAnswer.includes("0");

    if (noPoints && correctAnswer !== "אין נקודות קיצון") {
        return {
            whyWrong: "יש נקודות קיצון לפונקציה הזו, אבל לא מצאת אותן. אולי לא חישבת נכון את הנגזרת או לא פתרת את המשוואה.",
            correctMethod: "שלב 1: חשב f'(x). שלב 2: פתור f'(x) = 0. שלב 3: בדוק שהפתרונות אמיתיים.",
            stepByStep: "דוגמה: f(x) = x²\n1. f'(x) = 2x\n2. פתור: 2x = 0 → x = 0\n3. נקודת קיצון: x = 0",
            keyInsight: "רוב הפונקציות הפולינומיות (חוץ מקווים ישרים) יש להן נקודות קיצון.",
            commonMistake: "מוותרים מהר מדי כשהמשוואה נראית מורכבת, או לא מחשבים נכון את הנגזרת.",
            howToAvoid: "אל תוותר! בצע כל שלב בקפידה ובדוק את החישובים.",
            practiceTip: "תתרגל על פונקציות פשוטות קודם: x², x³-3x, ואז עבור למורכבות יותר.",
            memoryAid: "זכור: 'אם יש x בחזקה 2 ומעלה, כנראה יש קיצון'"
        };
    }

    if (zeroOnly) {
    return {
        whyWrong: "מצאת רק את x=0 אבל יש נקודות קיצון נוספות. לא פתרת את המשוואה f'(x)=0 לגמרי.",
        correctMethod: "אחרי שמקבלים את הנגזרת, צריך לפתור את המשוואה f'(x)=0 בצורה שלמה.",
        stepByStep: "דוגמה: f'(x) = 3x²-3 = 0\n1. 3x²-3 = 0\n2. 3x² = 3\n3. x² = 1\n4. x = ±1\nתוצאה: x = -1, x = 1",
        keyInsight: "משוואות ריבועיות ומעוקבות יכולות להיות להן יותר מפתרון אחד",
        commonMistake: "עוצרים אחרי שמוצאים פתרון אחד ולא מחפשים את כל הפתרונות",
        howToAvoid: "תמיד פתור את המשוואה לגמרי ובדוק שמצאת את כל הפתרונות האפשריים",
        practiceTip: "התרגל על פתרון משוואות ריבועיות, מעוקבות ומשוואות עם נוסחאות",
        memoryAid: "זכור: 'משוואה = כל הפתרונות, לא רק הראשון'"
    };
}

    if (wrongPoints) {
        return {
            whyWrong: "חישבת את הנגזרת אבל טעית בפתרון המשוואה f'(x) = 0.",
            correctMethod: "אחרי חישוב הנגזרת, פתור בזהירות את המשוואה f'(x) = 0.",
            stepByStep: "1. חשב f'(x) בקפידה\n2. השווה ל-0: f'(x) = 0\n3. פתור את המשוואה (פרק, העבר אגפים, וכו')\n4. בדוק את הפתרון בהצבה חזרה",
            keyInsight: "פתרון משוואות דורש שיטתיות ודיוק - טעות קטנה יכולה לשנות את כל התוצאה.",
            commonMistake: "טעויות חישוב בפתרון המשוואה: שכחה להעביר אגפים, שגיאות בפירוק, או בחישוב שורשים.",
            howToAvoid: "בצע כל שלב בנפרד, בדוק את החישוב, והצב חזרה לוודא שהפתרון נכון.",
            practiceTip: "תתחזק בפתרון משוואות: ליניאריות, ריבועיות, ומשוואות עם מכפלות.",
            memoryAid: "זכור: 'בדוק עם הצבה חזרה' - תמיד וודא שהפתרון עובד"
        };
    }

    return {
        whyWrong: "יש בעיה בחישוב הנגזרת או בפתרון המשוואה f'(x) = 0.",
        correctMethod: "תהליך דו-שלבי: 1) חישוב נגזרת מדויק 2) פתרון מלא של המשוואה f'(x) = 0.",
        stepByStep: "1. חשב f'(x) בצורה נכונה\n2. השווה ל-0: f'(x) = 0\n3. פתור את המשוואה לגמרי\n4. בדוק את כל הפתרונות",
        keyInsight: "נקודות קיצון = נקודות שבהן הנגזרת מתאפסת. שני שלבים ושניהם חייבים להיות מדויקים.",
        commonMistake: "טעויות בחישוב הנגזרת או בפתרון המשוואה, או שלא פותרים את המשוואה לגמרי.",
        howToAvoid: "בצע כל שלב בנפרד, בדוק כל חישוב, ותמיד פתור את המשוואה לגמרי.",
        practiceTip: "תתרגל בנפרד: חישוב נגזרות + פתרון משוואות, ואז שלב את השניים.",
        memoryAid: "זכור: 'נגזרת נכונה + פתרון מלא = נקודות קיצון נכונות'"
    };
}

function analyzeGenericError(questionText, userAnswer, correctAnswer, difficulty) {
    return {
        whyWrong: "התשובה שבחרת אינה נכונה על פי הכללים המתמטיים הרלוונטיים לסוג השאלה.",
        correctMethod: "זהה את סוג הבעיה (נגזרת, אינטגרל, גבול, נקודות קיצון) והשתמש בכללים המתאימים.",
        stepByStep: "1. קרא היטב את השאלה\n2. זהה את סוג הבעיה\n3. זכור את הכללים הרלוונטיים\n4. יישם בצורה שיטתית\n5. בדוק את התוצאה",
        keyInsight: "כל סוג בעיה במתמטיקה יש לו כללים וטכניקות ייחודיים - חשוב לזהות נכון את הסוג.",
        commonMistake: "לא קוראים בקפידה את השאלה או מתבלבלים בין סוגי בעיות שונים.",
        howToAvoid: "תמיד קרא את השאלה פעמיים לפני תחילת הפתרון וזהה את סוג הבעיה.",
        practiceTip: "תתרגל זיהוי מהיר של סוגי בעיות והכללים המתאימים לכל סוג.",
        memoryAid: "זכור: 'זיהוי נכון של הבעיה = מחצית מהפתרון'"
    };
}

function nextQuestion() {
    currentQuestionIndex++;
    const container = document.querySelector('.quiz-card').parentElement;
    showCurrentQuestion(container);
}

function showResults(container) {
    const timeSpent = quizStartTime ? Math.round((new Date() - quizStartTime) / 1000) : null;
    const percentage = Math.round((correctCount / totalQuestions) * 100);

    saveQuizResult(currentTopic, correctCount, totalQuestions, timeSpent, percentage);

    // הכנת ציון וחוות דעת
    let gradeInfo = getGradeInfo(percentage);

    container.innerHTML = `
        <div class="results">
            <h1>🎉 סיימת את המבחן!</h1>
            <div class="final-score" style="color: ${gradeInfo.color};">
                ${percentage}%
            </div>
            <div class="grade-text" style="color: ${gradeInfo.color}; font-size: 1.4rem; font-weight: bold; margin: 10px 0;">
                ${gradeInfo.grade}
            </div>
            <div class="score-details">
                ✅ ${correctCount} נכונות | ❌ ${totalQuestions - correctCount} שגויות
                ${timeSpent ? `<br>⏱️ זמן: ${formatTime(timeSpent)}` : ''}
            </div>
            
            ${percentage < 70 ? `
            <div class="improvement-section">
                <h3>💪 איך להשתפר:</h3>
                <div class="improvement-tips">
                    ${generateImprovementTips(currentTopic, percentage)}
                </div>
            </div>` : `
            <div class="success-section">
                <h3>🌟 כל הכבוד!</h3>
                <p>הביצועים שלך מעולים! המשך ללמוד ולהתפתח.</p>
            </div>`}
            
            <div class="result-actions">
                <button onclick="location.reload()" class="restart-btn">שאלון חדש</button>
                <button onclick="location.href='/'" class="home-btn">דף הבית</button>
                <button onclick="location.href='/quiz_summary'" class="stats-btn">📊 הסטטיסטיקות שלי</button>
            </div>
        </div>
    `;
}

function getGradeInfo(percentage) {
    if (percentage >= 95) {
        return { grade: "מעולה ביותר! 🏆", color: "#FFD700" };
    } else if (percentage >= 90) {
        return { grade: "מעולה! ⭐", color: "#10b981" };
    } else if (percentage >= 80) {
        return { grade: "טוב מאוד! 👍", color: "#3b82f6" };
    } else if (percentage >= 70) {
        return { grade: "טוב! 👌", color: "#f59e0b" };
    } else if (percentage >= 60) {
        return { grade: "עובר 📚", color: "#ef4444" };
    } else {
        return { grade: "צריך שיפור 💪", color: "#dc2626" };
    }
}

function generateImprovementTips(topic, percentage) {
    const baseTips = [
        "חזור על התיאוריה של הנושא",
        "תרגל יותר שאלות דומות", 
        "בדוק את השגיאות שעשית במבחן הזה"
    ];

    const topicSpecificTips = {
        'derivatives': [
            "תלמד בעל פה את כללי הנגזרות הבסיסיים",
            "תרגל על כלל השרשרת עם דוגמאות פשוטות",
            "תמיד בדוק את התוצאה עם נגזרת של פונקציה פשוטה"
        ],
        'integrals': [
            "תמיד זכור להוסיף +C באינטגרלים בלתי מוגדרים",
            "תרגל על כלל החזקה לאינטגרלים",
            "תלמד את האינטגרלים הבסיסיים בעל פה"
        ],
        'limits': [
            "תרגל זיהוי של צורות אי-וודאות",
            "תלמד את הגבולות הטריגונומטריים המפורסמים",
            "תתרגל על גבולות לאינסוף"
        ],
        'criticalpoints': [
            "תרגל חישוב נגזרות בקפידה",
            "תלמד לפתור משוואות ריבועיות ומעוקבות",
            "תמיד בדוק את הפתרון על ידי הצבה"
        ]
    };

    const tips = [...baseTips, ...(topicSpecificTips[topic] || [])];
    
    return tips.slice(0, 3).map(tip => `<div class="tip-item">• ${tip}</div>`).join('');
}

async function saveQuizResult(topic, score, totalQuestions, timeSpent, percentage) {
    try {
        const response = await fetch('/api/save-result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic, score, total_questions: totalQuestions, time_spent: timeSpent,
                details: { percentage, difficulty: currentDifficulty || 'mixed', date: new Date().toISOString() }
            })
        });
        if (response.ok) {
            const result = await response.json();
            console.log('✅ תוצאה נשמרה:', result);
        } else {
            console.error('❌ שגיאה בשמירת תוצאה');
        }
    } catch (error) {
        console.error('❌ שגיאה בשמירת תוצאה:', error);
    }
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    } else {
        return `${seconds} שניות`;
    }   
    
function analyzeGenericError(questionText, userAnswer, correctAnswer, difficulty) {
    return {
        whyWrong: "התשובה שבחרת אינה נכונה על פי הכללים המתמטיים הרלוונטיים לסוג השאלה.",
        correctMethod: "זהה את סוג הבעיה (נגזרת, אינטגרל, גבול, נקודות קיצון) והשתמש בכללים המתאימים.",
        stepByStep: "1. קרא היטב את השאלה\n2. זהה את סוג הבעיה\n3. זכור את הכללים הרלוונטיים\n4. יישם בצורה שיטתית\n5. בדוק את התוצאה",
        keyInsight: "כל סוג בעיה במתמטיקה יש לו כללים וטכניקות ייחודיים - חשוב לזהות נכון את הסוג.",
        commonMistake: "לא קוראים בקפידה את השאלה או מתבלבלים בין סוגי בעיות שונים.",
        howToAvoid: "תמיד קרא את השאלה פעמיים לפני תחילת הפתרון וזהה את סוג הבעיה.",
        practiceTip: "תתרגל זיהוי מהיר של סוגי בעיות והכללים המתאימים לכל סוג.",
        memoryAid: "זכור: 'זיהוי נכון של הבעיה = מחצית מהפתרון'"
    };
}

function nextQuestion() {
    currentQuestionIndex++;
    const container = document.querySelector('.quiz-card').parentElement;
    showCurrentQuestion(container);
}

function showResults(container) {
    const timeSpent = quizStartTime ? Math.round((new Date() - quizStartTime) / 1000) : null;
    const percentage = Math.round((correctCount / totalQuestions) * 100);

    saveQuizResult(currentTopic, correctCount, totalQuestions, timeSpent, percentage);

    // הכנת ציון וחוות דעת
    let gradeInfo = getGradeInfo(percentage);

    container.innerHTML = `
        <div class="results">
            <h1>🎉 סיימת את המבחן!</h1>
            <div class="final-score" style="color: ${gradeInfo.color};">
                ${percentage}%
            </div>
            <div class="grade-text" style="color: ${gradeInfo.color}; font-size: 1.4rem; font-weight: bold; margin: 10px 0;">
                ${gradeInfo.grade}
            </div>
            <div class="score-details">
                ✅ ${correctCount} נכונות | ❌ ${totalQuestions - correctCount} שגויות
                ${timeSpent ? `<br>⏱️ זמן: ${formatTime(timeSpent)}` : ''}
            </div>
            
            ${percentage < 70 ? `
            <div class="improvement-section">
                <h3>💪 איך להשתפר:</h3>
                <div class="improvement-tips">
                    ${generateImprovementTips(currentTopic, percentage)}
                </div>
            </div>` : `
            <div class="success-section">
                <h3>🌟 כל הכבוד!</h3>
                <p>הביצועים שלך מעולים! המשך ללמוד ולהתפתח.</p>
            </div>`}
            
            <div class="result-actions">
                <button onclick="location.reload()" class="restart-btn">שאלון חדש</button>
                <button onclick="location.href='/'" class="home-btn">דף הבית</button>
                <button onclick="location.href='/quiz_summary'" class="stats-btn">📊 הסטטיסטיקות שלי</button>
            </div>
        </div>
    `;
}

function getGradeInfo(percentage) {
    if (percentage >= 95) {
        return { grade: "מעולה ביותר! 🏆", color: "#FFD700" };
    } else if (percentage >= 90) {
        return { grade: "מעולה! ⭐", color: "#10b981" };
    } else if (percentage >= 80) {
        return { grade: "טוב מאוד! 👍", color: "#3b82f6" };
    } else if (percentage >= 70) {
        return { grade: "טוב! 👌", color: "#f59e0b" };
    } else if (percentage >= 60) {
        return { grade: "עובר 📚", color: "#ef4444" };
    } else {
        return { grade: "צריך שיפור 💪", color: "#dc2626" };
    }
}

function generateImprovementTips(topic, percentage) {
    const baseTips = [
        "חזור על התיאוריה של הנושא",
        "תרגל יותר שאלות דומות", 
        "בדוק את השגיאות שעשית במבחן הזה"
    ];

    const topicSpecificTips = {
        'derivatives': [
            "תלמד בעל פה את כללי הנגזרות הבסיסיים",
            "תרגל על כלל השרשרת עם דוגמאות פשוטות",
            "תמיד בדוק את התוצאה עם נגזרת של פונקציה פשוטה"
        ],
        'integrals': [
            "תמיד זכור להוסיף +C באינטגרלים בלתי מוגדרים",
            "תרגל על כלל החזקה לאינטגרלים",
            "תלמד את האינטגרלים הבסיסיים בעל פה"
        ],
        'limits': [
            "תרגל זיהוי של צורות אי-וודאות",
            "תלמד את הגבולות הטריגונומטריים המפורסמים",
            "תתרגל על גבולות לאינסוף"
        ],
        'criticalpoints': [
            "תרגל חישוב נגזרות בקפידה",
            "תלמד לפתור משוואות ריבועיות ומעוקבות",
            "תמיד בדוק את הפתרון על ידי הצבה"
        ]
    };

    const tips = [...baseTips, ...(topicSpecificTips[topic] || [])];
    
    return tips.slice(0, 3).map(tip => `<div class="tip-item">• ${tip}</div>`).join('');
}

async function saveQuizResult(topic, score, totalQuestions, timeSpent, percentage) {
    try {
        const response = await fetch('/api/save-result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic, score, total_questions: totalQuestions, time_spent: timeSpent,
                details: { percentage, difficulty: currentDifficulty || 'mixed', date: new Date().toISOString() }
            })
        });
        if (response.ok) {
            const result = await response.json();
            console.log('✅ תוצאה נשמרה:', result);
        } else {
            console.error('❌ שגיאה בשמירת תוצאה');
        }
    } catch (error) {
        console.error('❌ שגיאה בשמירת תוצאה:', error);
    }
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')} דקות`;
    } else {
        return `${seconds} שניות`;
    }
}
}

