import os, json, datetime, random, hashlib, uuid
from io import BytesIO
from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mocktest_pro.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'change-in-production'
db = SQLAlchemy(app)

EXPORT_PASSWORD_HASH = hashlib.sha256('121520'.encode()).hexdigest()
IMPORT_PASSWORD_HASH = hashlib.sha256('121520'.encode()).hexdigest()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), unique=True, index=True)
    username = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), index=True)
    subcategory = db.Column(db.String(100))
    test_number = db.Column(db.Integer, default=1)
    question = db.Column(db.Text)
    options = db.Column(db.Text)
    correct = db.Column(db.Integer)
    explanation = db.Column(db.Text, default='')

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category = db.Column(db.String(50))
    subcategory = db.Column(db.String(100))
    total = db.Column(db.Integer)
    correct = db.Column(db.Integer)
    wrong = db.Column(db.Integer)
    skipped = db.Column(db.Integer)
    pct = db.Column(db.Float)
    time_sec = db.Column(db.Integer)
    mode = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class WeakQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    wrong_count = db.Column(db.Integer, default=1)
    last_wrong = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class UserStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    xp = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    last_active = db.Column(db.Date, default=datetime.date.today)

def get_next_test_slot(category, subcategory):
    """Smart auto-fill logic: fill incomplete tests first before creating new ones"""
    all_tests = db.session.query(
        Question.test_number,
        func.count(Question.id).label('count')
    ).filter_by(category=category, subcategory=subcategory).group_by(
        Question.test_number
    ).order_by(Question.test_number).all()
    
    if not all_tests:
        return 1, 0
    
    for test_num, count in all_tests:
        if count < 20:
            return test_num, count
    
    last_test_num = all_tests[-1][0]
    return last_test_num + 1, 0

with app.app_context():
    db.create_all()
    if Question.query.count() == 0:
        samples = {
            "G.K.": {
                "World Geography": [
                    {"question":"What is the capital of India?","options":["Mumbai","New Delhi","Kolkata","Chennai"],"correct":1,"explanation":"New Delhi is the capital of India."},
                    {"question":"In which country are the Taurus Mountains located?","options":["India","Turkey","Pakistan","Iran"],"correct":1,"explanation":"The Taurus Mountains are located in Turkey."},
                    {"question":"On which continent is the Nile River located?","options":["Asia","Africa","Europe","Australia"],"correct":1,"explanation":"The Nile River is in Africa."},
                    {"question":"Which is the largest continent by area?","options":["Africa","Asia","Europe","North America"],"correct":1,"explanation":"Asia is the largest continent by area."},
                    {"question":"What is the height of Mount Everest?","options":["8848 m","8611 m","7850 m","9200 m"],"correct":0,"explanation":"Mount Everest is 8848 meters high."},
                    {"question":"Which is the largest ocean in the world?","options":["Atlantic","Indian","Arctic","Pacific"],"correct":3,"explanation":"The Pacific Ocean is the largest."},
                    {"question":"Which is the longest river in India?","options":["Ganga","Yamuna","Godavari","Brahmaputra"],"correct":0,"explanation":"The Ganga is the longest river in India."},
                    {"question":"Where is the Thar Desert located?","options":["Rajasthan","Gujarat","Punjab","Haryana"],"correct":0,"explanation":"The Thar Desert is mainly located in Rajasthan."},
                    {"question":"The Sunda Strait is between which two islands?","options":["Java and Sumatra","Borneo and Sulawesi","Java and Bali","Sumatra and Kalimantan"],"correct":0,"explanation":"The Sunda Strait is between Java and Sumatra."},
                    {"question":"In which country is the Gobi Desert located?","options":["India","China","Mongolia","Russia"],"correct":2,"explanation":"The Gobi Desert is located in Mongolia and China."},
                    {"question":"The Arabian Sea is located to the south of?","options":["India","Pakistan","Iran","Arabian Peninsula"],"correct":3,"explanation":"The Arabian Sea is south of the Arabian Peninsula."},
                    {"question":"Into which sea does the Danube River flow?","options":["Black Sea","Mediterranean Sea","Caspian Sea","Atlantic"],"correct":0,"explanation":"The Danube flows into the Black Sea."},
                    {"question":"Which isthmus connects Asia and Africa?","options":["Suez","Panama","Gibraltar","Bosphorus"],"correct":0,"explanation":"The Suez Isthmus connects Asia and Africa."},
                    {"question":"Which is the longest river in North America?","options":["Mississippi","Missouri","Amazon","Colorado"],"correct":1,"explanation":"The Missouri-Mississippi system is the longest."},
                    {"question":"In which country is Mount Kilimanjaro located?","options":["Kenya","Tanzania","Uganda","Rwanda"],"correct":1,"explanation":"Mount Kilimanjaro is in Tanzania."},
                    {"question":"What is the largest lake in the world?","options":["Caspian Sea","Superior","Victoria","Baikal"],"correct":0,"explanation":"The Caspian Sea is the largest lake."},
                    {"question":"Angel Falls is located on which river?","options":["Nile","Amazon","Congo","Orinoco"],"correct":3,"explanation":"Angel Falls is on a tributary of the Orinoco River."},
                    {"question":"The Great Barrier Reef is located near which country?","options":["Australia","New Zealand","Fiji","Papua New Guinea"],"correct":0,"explanation":"It is off the eastern coast of Australia."},
                    {"question":"What is the highest mountain peak in Europe?","options":["Elbrus","Mont Blanc","Matterhorn","Grossglockner"],"correct":0,"explanation":"Mount Elbrus is the highest."},
                    {"question":"Through how many countries does the Tropic of Cancer pass?","options":["12","16","18","20"],"correct":1,"explanation":"The Tropic of Cancer passes through 16 countries."}
                ],
                "Indian History": [
                    {"question":"Who was the first Prime Minister of India?","options":["Jawaharlal Nehru","Mahatma Gandhi","Sardar Patel","Dr. Rajendra Prasad"],"correct":0,"explanation":"Jawaharlal Nehru was the first PM."},
                    {"question":"Who built the Taj Mahal?","options":["Akbar","Shah Jahan","Babur","Aurangzeb"],"correct":1,"explanation":"Shah Jahan built the Taj Mahal."},
                    {"question":"In which year did the revolt of 1857 take place?","options":["1856","1857","1858","1859"],"correct":1,"explanation":"The revolt took place in 1857."},
                    {"question":"When did India gain independence?","options":["1945","1946","1947","1948"],"correct":2,"explanation":"India gained independence on August 15, 1947."},
                    {"question":"To which dynasty did Ashoka belong?","options":["Maurya","Gupta","Chola","Mughal"],"correct":0,"explanation":"Ashoka belonged to the Maurya dynasty."},
                    {"question":"When was the Constitution of India implemented?","options":["Nov 26, 1949","Jan 26, 1950","Aug 15, 1947","Oct 2, 1950"],"correct":1,"explanation":"It was implemented on January 26, 1950."},
                    {"question":"Who was the founder of Sikhism?","options":["Guru Nanak","Guru Gobind Singh","Guru Angad","Guru Arjun"],"correct":0,"explanation":"Guru Nanak founded Sikhism."},
                    {"question":"In which year was the First Battle of Panipat fought?","options":["1526","1556","1761","1857"],"correct":0,"explanation":"It was fought in 1526."},
                    {"question":"Who started the Din-i-Ilahi?","options":["Akbar","Jahangir","Shah Jahan","Aurangzeb"],"correct":0,"explanation":"Akbar started the Din-i-Ilahi."},
                    {"question":"When did the Quit India Movement start?","options":["1940","1942","1945","1947"],"correct":1,"explanation":"It started in 1942."},
                    {"question":"When was Mahatma Gandhi born?","options":["1869","1879","1889","1899"],"correct":0,"explanation":"He was born on October 2, 1869."},
                    {"question":"Who was Akbar's regent?","options":["Bairam Khan","Todar Mal","Man Singh","Abul Fazl"],"correct":0,"explanation":"Bairam Khan was Akbar's regent."},
                    {"question":"Along the banks of which river did the Harappan civilization develop?","options":["Ganga","Yamuna","Indus","Godavari"],"correct":2,"explanation":"It developed along the Indus River."},
                    {"question":"When was the British East India Company established in India?","options":["1600","1605","1610","1620"],"correct":0,"explanation":"It was established in 1600."},
                    {"question":"Who established the Swarajya?","options":["Gokhale","Tilak","Shivaji","Rana Pratap"],"correct":2,"explanation":"Shivaji established the Swarajya."},
                    {"question":"Where was the first cotton mill set up in India?","options":["Mumbai","Ahmedabad","Kanpur","Surat"],"correct":0,"explanation":"It was set up in Mumbai in 1854."},
                    {"question":"When did the partition of Bengal take place?","options":["1905","1906","1907","1908"],"correct":0,"explanation":"It took place in 1905."},
                    {"question":"When did the Simon Commission arrive in India?","options":["1927","1928","1929","1930"],"correct":1,"explanation":"It arrived in 1928."},
                    {"question":"When did the Jallianwala Bagh massacre take place?","options":["1917","1918","1919","1920"],"correct":2,"explanation":"It took place in 1919."},
                    {"question":"Who wrote the Indian national anthem Jana Gana Mana?","options":["Rabindranath Tagore","Bankim Chandra","Subhash Chandra","Mahatma Gandhi"],"correct":0,"explanation":"Rabindranath Tagore wrote it."}
                ]
            },
            "Maths": {
                "Algebra": [
                    {"question":"If x + 5 = 12, what is x?","options":["5","6","7","8"],"correct":2,"explanation":"x = 12 - 5 = 7."},
                    {"question":"Solve: 3x = 21","options":["6","7","8","9"],"correct":1,"explanation":"x = 21 / 3 = 7."},
                    {"question":"What is the value of 2^3?","options":["6","8","16","32"],"correct":1,"explanation":"2 * 2 * 2 = 8."},
                    {"question":"Expand (x+2)(x+3)","options":["x^2+5x+6","x^2+6x+5","x^2+5x+5","x^2+6x+6"],"correct":0,"explanation":"x^2 + 3x + 2x + 6 = x^2 + 5x + 6."},
                    {"question":"If 2x - 4 = 10, what is x?","options":["5","6","7","8"],"correct":2,"explanation":"2x = 14 => x = 7."},
                    {"question":"What is the square root of 81?","options":["8","9","10","11"],"correct":1,"explanation":"9 * 9 = 81."},
                    {"question":"Factorize: x^2 - 9","options":["(x-3)(x+3)","(x-3)(x-3)","(x+3)(x+3)","(x-9)(x+1)"],"correct":0,"explanation":"Difference of squares: a^2 - b^2 = (a-b)(a+b)."},
                    {"question":"Solve for y: y/4 = 10","options":["20","30","40","50"],"correct":2,"explanation":"y = 10 * 4 = 40."},
                    {"question":"What is 5! (5 factorial)?","options":["20","60","120","240"],"correct":2,"explanation":"5 * 4 * 3 * 2 * 1 = 120."},
                    {"question":"If a = 2 and b = 3, what is a^2 + b^2?","options":["12","13","14","15"],"correct":1,"explanation":"4 + 9 = 13."},
                    {"question":"Simplify: 5x - 2x + 3x","options":["4x","5x","6x","7x"],"correct":2,"explanation":"5 - 2 + 3 = 6."},
                    {"question":"What is the y-intercept of y = 2x + 4?","options":["2","4","-2","-4"],"correct":1,"explanation":"The constant term is the y-intercept."},
                    {"question":"Solve: 4(x - 2) = 8","options":["3","4","5","6"],"correct":1,"explanation":"4x - 8 = 8 => 4x = 16 => x = 4."},
                    {"question":"What is the degree of the polynomial 3x^2 + 5x - 1?","options":["1","2","3","4"],"correct":1,"explanation":"The highest power is 2."},
                    {"question":"If x^2 = 49, what is a possible value of x?","options":["6","7","8","9"],"correct":1,"explanation":"7 * 7 = 49."},
                    {"question":"What is 10% of x = 5? Find x.","options":["25","50","75","100"],"correct":1,"explanation":"10/100 * x = 5 => x = 50."},
                    {"question":"Solve: -3x < 12","options":["x > -4","x < -4","x > 4","x < 4"],"correct":0,"explanation":"Dividing by a negative flips the inequality sign."},
                    {"question":"What is the slope of y = 4x - 3?","options":["3","4","-3","-4"],"correct":1,"explanation":"The coefficient of x is the slope."},
                    {"question":"Combine like terms: 7a - 3b + 2a + 5b","options":["9a + 2b","9a - 2b","7a + 2b","9a + 8b"],"correct":0,"explanation":"7a + 2a = 9a; -3b + 5b = 2b."},
                    {"question":"Solve for x: 2x + 3 = 3x - 2","options":["3","4","5","6"],"correct":2,"explanation":"3 + 2 = 3x - 2x => 5 = x."}
                ]
            }
        }
        
        for cat, subs in samples.items():
            for sub, qs in subs.items():
                test_num = 1
                count = 0
                for q in qs:
                    if count >= 20:
                        test_num += 1
                        count = 0
                    db.session.add(Question(
                        category=cat, subcategory=sub, test_number=test_num,
                        question=q['question'], options=json.dumps(q['options']),
                        correct=q['correct'], explanation=q.get('explanation', '')
                    ))
                    count += 1
        db.session.commit()

def update_user_stats(user_id, correct_count):
    stats = UserStats.query.filter_by(user_id=user_id).first()
    if not stats:
        stats = UserStats(user_id=user_id, xp=0, streak=1, last_active=datetime.date.today())
        db.session.add(stats)
    
    today = datetime.date.today()
    if stats.last_active != today:
        yesterday = today - datetime.timedelta(days=1)
        if stats.last_active == yesterday:
            stats.streak += 1
        else:
            stats.streak = 1
        stats.last_active = today
    
    stats.xp += correct_count * 10
    db.session.commit()

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', 'Guest').strip()
    user_id = data.get('user_id')
    
    user = None
    if user_id:
        user = User.query.filter_by(user_id=user_id).first()
        
    if not user:
        new_user_id = str(uuid.uuid4())
        user = User(user_id=new_user_id, username=username)
        db.session.add(user)
        db.session.commit()
        
        stats = UserStats(user_id=user.id, xp=0, streak=1)
        db.session.add(stats)
        db.session.commit()
    else:
        if user.username != username and username != "Guest":
            user.username = username
            db.session.commit()
            
    return jsonify({'user_id': user.user_id, 'username': user.username})

@app.route('/api/categories')
def get_categories():
    cats = db.session.query(Question.category).distinct().all()
    return jsonify(sorted([c[0] for c in cats]))

@app.route('/api/subcategories')
def get_subcategories():
    category = request.args.get('category')
    if not category: return jsonify([])
    subs = db.session.query(Question.subcategory).filter(Question.category == category).distinct().all()
    result = []
    for sub in subs:
        count = Question.query.filter_by(category=category, subcategory=sub[0]).count()
        result.append({"name": sub[0], "count": count})
    return jsonify(sorted(result, key=lambda x: x['name']))

@app.route('/api/tests')
def get_tests():
    category = request.args.get('category')
    subcategory = request.args.get('subcategory')
    if not category or not subcategory: return jsonify([])
    
    max_test = db.session.query(db.func.max(Question.test_number)).filter(
        Question.category == category, Question.subcategory == subcategory
    ).scalar() or 0
    
    tests = []
    for i in range(1, max_test + 1):
        count = Question.query.filter_by(category=category, subcategory=subcategory, test_number=i).count()
        if count > 0:
            tests.append({"test_number": i, "count": count})
    return jsonify(tests)

@app.route('/api/start-test', methods=['POST'])
def start_test():
    data = request.json
    user_uuid = data.get('user_id')
    user = User.query.filter_by(user_id=user_uuid).first()
    if not user: return jsonify({'error': 'User not found'}), 404
    
    category = data.get('category')
    subcategory = data.get('subcategory')
    test_number = data.get('test_number')
    mode = data.get('mode', 'specific')
    
    if mode == 'all':
        questions = Question.query.filter_by(category=category, subcategory=subcategory).all()
        timer_min = max(1, len(questions) // 2)
    else:
        questions = Question.query.filter_by(category=category, subcategory=subcategory, test_number=test_number).all()
        timer_min = 10
        
    if not questions:
        return jsonify({'error': 'No questions found'}), 404
        
    random.shuffle(questions)
    
    result = []
    for q in questions:
        opts = json.loads(q.options)
        correct_idx = q.correct
        indices = list(range(4))
        random.shuffle(indices)
        new_opts = [opts[i] for i in indices]
        new_correct = indices.index(correct_idx)
        
        result.append({
            'id': q.id, 'category': q.category, 'subcategory': q.subcategory,
            'question': q.question, 'options': new_opts,
            'correct': new_correct, 'explanation': q.explanation
        })
        
    return jsonify({'questions': result, 'timer_min': timer_min, 'mode': mode})

@app.route('/api/submit-test', methods=['POST'])
def submit_test():
    data = request.json
    user_uuid = data.get('user_id')
    user = User.query.filter_by(user_id=user_uuid).first()
    if not user: return jsonify({'error': 'User not found'}), 404
    
    answers = data.get('answers', [])
    category = data.get('category', '')
    subcategory = data.get('subcategory', '')
    mode = data.get('mode', 'specific')
    time_sec = data.get('time_sec', 0)
    
    correct = wrong = skipped = 0
    for a in answers:
        q = Question.query.get(a['question_id'])
        if not q: continue
        sel = a.get('selected')
        if sel is None:
            skipped += 1
        elif sel == q.correct:
            correct += 1
        else:
            wrong += 1
            weak = WeakQuestion.query.filter_by(user_id=user.id, question_id=q.id).first()
            if not weak:
                db.session.add(WeakQuestion(user_id=user.id, question_id=q.id, wrong_count=1))
            else:
                weak.wrong_count += 1
                weak.last_wrong = datetime.datetime.utcnow()
                
    update_user_stats(user.id, correct)
    
    total = len(answers)
    pct = round(correct/total*100, 2) if total else 0
    
    attempt = TestResult(
        user_id=user.id, category=category, subcategory=subcategory,
        total=total, correct=correct, wrong=wrong, skipped=skipped,
        pct=pct, time_sec=time_sec, mode=mode
    )
    db.session.add(attempt)
    db.session.commit()
    
    return jsonify({
        'correct': correct, 'wrong': wrong, 'skipped': skipped,
        'total': total, 'pct': pct, 'xp_earned': correct * 10
    })

@app.route('/api/weak-questions')
def weak_questions():
    user_uuid = request.args.get('user_id')
    user = User.query.filter_by(user_id=user_uuid).first()
    if not user: return jsonify([])
    
    weaks = WeakQuestion.query.filter_by(user_id=user.id).order_by(WeakQuestion.wrong_count.desc()).all()
    result = []
    for w in weaks:
        q = Question.query.get(w.question_id)
        if q:
            result.append({
                'id': q.id, 'category': q.category, 'subcategory': q.subcategory,
                'question': q.question, 'options': json.loads(q.options),
                'correct': q.correct, 'explanation': q.explanation,
                'wrong_count': w.wrong_count
            })
    return jsonify(result)

@app.route('/api/stats')
def user_stats():
    user_uuid = request.args.get('user_id')
    user = User.query.filter_by(user_id=user_uuid).first()
    if not user: return jsonify({'total_questions':0, 'total_tests':0, 'avg_pct':0, 'weak_count':0, 'xp':0, 'streak':0})
    
    total_q = Question.query.count()
    attempts = TestResult.query.filter_by(user_id=user.id).all()
    total_tests = len(attempts)
    avg_pct = round(sum(a.pct for a in attempts)/total_tests, 1) if total_tests else 0
    weak_count = WeakQuestion.query.filter_by(user_id=user.id).count()
    
    stats = UserStats.query.filter_by(user_id=user.id).first()
    xp = stats.xp if stats else 0
    streak = stats.streak if stats else 0
    
    return jsonify({
        'total_questions': total_q, 'total_tests': total_tests, 'avg_pct': avg_pct, 
        'weak_count': weak_count, 'xp': xp, 'streak': streak
    })

@app.route('/api/leaderboard')
def leaderboard():
    results = db.session.query(
        User.username,
        func.sum(TestResult.total).label('total_attempted'),
        func.sum(TestResult.correct).label('total_correct')
    ).join(TestResult, User.id == TestResult.user_id)\
     .group_by(User.id)\
     .having(func.sum(TestResult.total) > 0)\
     .all()
     
    data = []
    for r in results:
        if r.total_attempted and r.total_attempted > 0:
            acc = round((r.total_correct / r.total_attempted) * 100, 1)
            data.append({
                'username': r.username,
                'score_text': f"{r.total_attempted}Q = {r.total_correct}",
                'accuracy': acc,
                'total_correct': r.total_correct,
                'total_attempted': r.total_attempted
            })
        
    data.sort(key=lambda x: (-x['accuracy'], -x['total_correct']))
    for i, d in enumerate(data):
        d['rank'] = i + 1
        
    return jsonify(data)

@app.route('/api/questions')
def get_questions():
    qs = Question.query.all()
    return jsonify([{
        'id': q.id, 'category': q.category, 'subcategory': q.subcategory,
        'question': q.question, 'options': json.loads(q.options),
        'correct': q.correct, 'explanation': q.explanation
    } for q in qs])

@app.route('/api/questions/<int:qid>', methods=['DELETE'])
def delete_question(qid):
    q = Question.query.get(qid)
    if not q: return jsonify({'error':'Not found'}), 404
    WeakQuestion.query.filter_by(question_id=qid).delete()
    db.session.delete(q)
    db.session.commit()
    return jsonify({'status':'ok'})

@app.route('/api/add-question', methods=['POST'])
def add_question():
    data = request.json
    category = data.get('category')
    subcategory = data.get('subcategory')
    
    test_num, _ = get_next_test_slot(category, subcategory)
            
    q = Question(
        category=category, subcategory=subcategory, test_number=test_num,
        question=data['question'], options=json.dumps(data['options']),
        correct=int(data['correct']), explanation=data.get('explanation', '')
    )
    db.session.add(q)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/import-questions', methods=['POST'])
def import_questions():
    data = request.json
    password = data.get('password', '')
    if hashlib.sha256(password.encode()).hexdigest() != IMPORT_PASSWORD_HASH:
        return jsonify({'error': 'Invalid password'}), 401
        
    category = data.get('category')
    subcategory = data.get('subcategory')
    questions = data.get('questions', [])
    
    if not questions:
        return jsonify({'error': 'No questions provided'}), 400
        
    current_test_num, count_in_current = get_next_test_slot(category, subcategory)
            
    objects = []
    for q in questions:
        if count_in_current >= 20:
            current_test_num += 1
            count_in_current = 0
            
        objects.append(Question(
            category=category, subcategory=subcategory, test_number=current_test_num,
            question=q['question'], options=json.dumps(q['options']),
            correct=int(q['correct']), explanation=q.get('explanation', '')
        ))
        count_in_current += 1
        
    db.session.add_all(objects)
    db.session.commit()
    return jsonify({'status': 'ok', 'added': len(objects)})

@app.route('/api/clear-all', methods=['DELETE'])
def clear_all_questions():
    WeakQuestion.query.delete()
    Question.query.delete()
    db.session.commit()
    return jsonify({'status':'ok'})

@app.route('/api/export-all', methods=['POST'])
def export_all():
    data = request.json or {}
    password = data.get('password', '')
    if hashlib.sha256(password.encode()).hexdigest() != EXPORT_PASSWORD_HASH:
        return jsonify({'error': 'Invalid password'}), 401
    qs = Question.query.all()
    export_data = []
    for q in qs:
        export_data.append({
            'category': q.category, 'subcategory': q.subcategory, 'question': q.question,
            'options': json.loads(q.options), 'correct': q.correct,
            'explanation': q.explanation
        })
    json_output = json.dumps(export_data, ensure_ascii=False, indent=2)
    bio = BytesIO(json_output.encode('utf-8'))
    bio.seek(0)
    return send_file(
        bio, mimetype='application/json', as_attachment=True,
        download_name=f'questions_export_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    )

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>MockTest Pro</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg:#f8faff; --card:rgba(255,255,255,0.75); --sunk:#edf2f9; --text:#1e2030; --text2:#5b5d6b; --muted:#9295a1;
      --line:#dce0e8; --line2:#c4c9d4; --brand:#4f46e5; --brand2:#f97316;
      --ok:#10b981; --oksoft:#d1fae5; --err:#ef4444; --errsoft:#fee2e2; --warn:#f59e0b; --warnsoft:#fef3c7;
      --shadow:0 1px 3px #0000000d,0 1px 2px #0000000a; --shadowMd:0 4px 12px #0000000f; --shadowLg:0 12px 32px #00000014;
      --radius:16px; --font:'Plus Jakarta Sans',sans-serif; --mono:'JetBrains Mono',monospace;
    }
    [data-theme="dark"] {
      --bg:#0f1123; --card:rgba(26,29,46,0.75); --sunk:#151828; --text:#f1f2f6; --text2:#b0b4c2; --muted:#777b8e;
      --line:#272b3a; --line2:#3a3f55; --brand:#818cf8; --brand2:#fb923c;
      --ok:#34d399; --oksoft:rgba(52,211,153,.15); --err:#f87171; --errsoft:rgba(248,113,113,.15);
      --warnsoft:rgba(245,158,11,.15);
    }
    *{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
    body{font-family:var(--font);background:linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);color:var(--text);min-height:100vh;line-height:1.5;transition:background .3s,color .3s;overflow-x:hidden}
    [data-theme="dark"] body { background: linear-gradient(135deg, #0f1123 0%, #1a1d2e 100%); }
    .container{width:100%;max-width:1200px;margin:0 auto;padding:0 16px;position:relative;z-index:2}
    button{font-family:inherit;cursor:pointer;border:0;background:none;color:inherit;transition: transform 0.1s ease, background 0.2s}
    button:active { transform: scale(0.96); }
    input,textarea,select{font-family:inherit;font-size:16px;color:var(--text);width:100%}
    a{color:var(--brand);text-decoration:none}
    
    @keyframes fadeInUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes popIn { 0% { opacity: 0; transform: scale(0.9); } 100% { opacity: 1; transform: scale(1); } }
    @keyframes blob { 0%, 100% { transform: translate(0, 0) scale(1); } 33% { transform: translate(30px, -50px) scale(1.1); } 66% { transform: translate(-20px, 20px) scale(0.9); } }
    
    .screen { animation: fadeInUp 0.4s ease-out; }
    .stagger-item { opacity: 0; animation: fadeInUp 0.4s ease-out forwards; }

    .bg-blob { position: fixed; border-radius: 50%; filter: blur(80px); z-index: 0; opacity: 0.4; pointer-events: none; }
    .blob-1 { width: 300px; height: 300px; background: var(--brand); top: -50px; left: -50px; animation: blob 12s infinite ease-in-out; }
    .blob-2 { width: 250px; height: 250px; background: var(--brand2); bottom: -50px; right: -50px; animation: blob 15s infinite ease-in-out reverse; }

    .navbar{position:sticky;top:0;z-index:50;background:var(--card);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--line);height:56px;display:flex;align-items:center;box-shadow:var(--shadow)}
    .nav-wrap{display:flex;align-items:center;justify-content:space-between;width:100%}
    .brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:1.2rem;color:var(--text)}
    .brand-dot{width:28px;height:28px;border-radius:9px;background:linear-gradient(135deg,var(--brand),#8b5cf6);position:relative}
    .brand-dot::after{content:"M";position:absolute;inset:0;display:grid;place-items:center;color:#fff;font-weight:800;font-size:14px}
    .nav-right{display:flex;align-items:center;gap:10px}
    .user-chip{display:flex;align-items:center;gap:6px;padding:5px 12px;border-radius:50px;background:var(--sunk);font-size:.85rem;cursor:pointer}
    .user-chip:hover { background: var(--line); }
    .dot-live{width:8px;height:8px;border-radius:50%;background:var(--ok);animation:pulse 2s infinite}
    @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
    .icon-btn{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;background:var(--sunk);border:1px solid var(--line)}
    .icon-btn:hover{background:var(--brand);color:#fff;border-color:var(--brand)}
    .icon-btn svg{width:20px;height:20px}
    [data-theme="light"] .i-moon,[data-theme="dark"] .i-sun{display:none}
    
    .bottom-nav{display:flex;position:fixed;bottom:0;left:0;right:0;background:var(--card);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-top:1px solid var(--line);z-index:45;padding:6px 0;justify-content:space-around;align-items:center;box-shadow:0 -4px 12px rgba(0,0,0,0.05)}
    .bottom-nav button{display:flex;flex-direction:column;align-items:center;gap:2px;color:var(--muted);font-size:.65rem;padding:4px 0;font-weight:600}
    .bottom-nav button.active{color:var(--brand)}
    .bottom-nav button svg{width:22px;height:22px}
    
    .screen{display:none;padding:24px 0 80px}
    .screen.active{display:block}
    
    .hero{max-width:600px;margin:0 auto;text-align:center;padding:40px 16px}
    .hero-tag{display:inline-flex;align-items:center;gap:8px;padding:6px 16px;border-radius:100px;background:var(--card);backdrop-filter:blur(8px);font-size:.85rem;color:var(--text2);margin-bottom:20px;border:1px solid var(--line)}
    .hero-title{font-size:clamp(2rem,7vw,3.5rem);font-weight:800;line-height:1.1;margin-bottom:12px}
    .grad-word{background:linear-gradient(135deg,var(--brand),var(--brand2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
    .hero-sub{max-width:500px;margin:0 auto 24px;color:var(--text2);font-size:1rem;font-style:italic}
    .name-card{background:var(--card);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:var(--radius);padding:24px;box-shadow:var(--shadowMd);text-align:left;margin-bottom:20px}
    .name-card label{display:block;font-weight:600;margin-bottom:8px;color:var(--text2);text-transform:uppercase;font-size:.75rem;letter-spacing:.1em}
    .name-row{display:flex;gap:10px;flex-wrap:wrap}
    input,textarea,select{padding:14px 16px;border:1px solid var(--line2);border-radius:12px;background:var(--bg);font-size:1rem;outline:none;transition:border-color .2s, box-shadow .2s}
    input:focus,textarea:focus,select:focus{border-color:var(--brand);box-shadow:0 0 0 3px rgba(79,70,229,.2)}
    
    .btn-primary{display:inline-flex;align-items:center;gap:8px;padding:14px 24px;border-radius:12px;background:linear-gradient(135deg,var(--brand),var(--brand2));color:#fff;font-weight:700;font-size:1rem;border:none;box-shadow:0 4px 14px rgba(79,70,229,0.3);cursor:pointer;transition:all 0.2s ease}
    .btn-primary:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(79,70,229,.4)}
    .btn-primary:active{transform:translateY(0);box-shadow:0 2px 8px rgba(79,70,229,.3)}
    .btn-primary:focus{outline:none;box-shadow:0 0 0 4px rgba(79,70,229,.3)}
    .btn-ghost{display:inline-flex;align-items:center;gap:6px;padding:12px 20px;border-radius:12px;background:var(--card);backdrop-filter:blur(8px);color:var(--text);font-weight:600;font-size:.95rem;border:1px solid var(--line)}
    .btn-ghost:hover{background:var(--sunk);border-color:var(--line2)}
    .btn-danger{padding:12px 16px;border-radius:12px;background:var(--errsoft);color:var(--err);font-weight:700;border:none}
    .btn-danger:hover{background:var(--err);color:#fff}
    .hidden{display:none!important}
    
    .page-head{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:24px}
    .eyebrow{text-transform:uppercase;letter-spacing:.1em;font-size:.7rem;color:var(--muted);font-weight:600}
    .page-title{font-size:2rem;font-weight:800}
    
    .glass-card { background: var(--card); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadowMd); }
    
    .profile-card { padding: 20px; margin-bottom: 20px; display: flex; justify-content:space-between; align-items: center; }
    .pc-left h2 { font-size: 1.2rem; margin-bottom: 4px; }
    .pc-left p { font-size: 0.8rem; color: var(--muted); font-style: italic; }
    .pc-right { text-align: center; }
    .level-badge { width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, var(--brand), var(--brand2)); color: #fff; display: grid; place-items: center; font-weight: 800; font-size: 1.4rem; box-shadow: 0 4px 12px rgba(79,70,229,0.3); }
    .pc-right span { font-size: 0.65rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
    
    .quick-stats{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:20px}
    @media(min-width:600px){.quick-stats{grid-template-columns:repeat(4,1fr)}}
    .stat{padding:14px;background:var(--card);backdrop-filter:blur(8px);border:1px solid var(--line);border-radius:14px;text-align:center}
    .stat b{display:block;font-size:1.5rem;font-weight:700;background:linear-gradient(135deg,var(--brand),var(--brand2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
    .stat span{font-size:.7rem;color:var(--muted);text-transform:uppercase}
    
    .grid-2{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:20px 0}
    @media(min-width:600px){.grid-2{grid-template-columns:repeat(3,1fr)}}
    .action-card{padding:18px;border-radius:20px;background:var(--card);backdrop-filter:blur(8px);border:1px solid var(--line);cursor:pointer;position:relative;overflow:hidden;text-align:left;width:100%}
    .action-card:hover{transform:translateY(-3px);box-shadow:var(--shadowLg);border-color:var(--brand)}
    .ac-icon{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;margin-bottom:10px;color:#fff;font-size:1.1rem}
    .ac-icon.g1{background:linear-gradient(135deg,#6366f1,#8b5cf6)} .ac-icon.g2{background:linear-gradient(135deg,#f59e0b,#f97316)}
    .ac-icon.g3{background:linear-gradient(135deg,#10b981,#06b6d4)} .ac-icon.g4{background:linear-gradient(135deg,#ef4444,#f97316)}
    .ac-icon.g5{background:linear-gradient(135deg,#8b5cf6,#ec4899)} .ac-icon.g6{background:linear-gradient(135deg,#06b6d4,#3b82f6)}
    .action-card h3{font-size:1rem;margin-bottom:4px;font-weight:700}
    .action-card p{color:var(--text2);font-size:.8rem;margin:0;font-style:italic}
    .ac-arrow{position:absolute;right:14px;top:14px;font-size:1.2rem;color:var(--muted);transition:.3s}
    .action-card:hover .ac-arrow{transform:translateX(6px);color:var(--brand)}
    .section-h{font-weight:700;font-size:.85rem;color:var(--text2);letter-spacing:.05em;text-transform:uppercase;margin:24px 0 10px;display:flex;align-items:center;gap:8px}
    
    .subtopic-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
    .subtopic-tile{padding:14px;border-radius:14px;background:var(--card);backdrop-filter:blur(8px);border:1px solid var(--line);cursor:pointer;text-align:left;width:100%}
    .subtopic-tile:hover{transform:translateY(-2px);border-color:var(--brand);box-shadow:var(--shadowMd)}
    .subtopic-tile h4{font-size:.9rem;margin-bottom:4px;font-weight:700}
    .subtopic-tile span{font-size:.7rem;color:var(--muted)}
    .empty{padding:20px;text-align:center;color:var(--muted);border:1.5px dashed var(--line);border-radius:12px;background:transparent}
    
    .test-list { display: grid; gap: 10px; }
    .test-tile { display: flex; justify-content: space-between; align-items: center; padding: 16px; border-radius: 14px; background: var(--card); backdrop-filter: blur(8px); border: 1px solid var(--line); cursor: pointer; transition: all 0.2s; }
    .test-tile:hover { border-color: var(--brand); transform: translateY(-2px); }
    .test-tile h4 { font-size: 1rem; font-weight: 700; }
    .test-tile p { font-size: 0.75rem; color: var(--muted); }
    .play-all-btn { width: 100%; padding: 16px; border-radius: 14px; background: linear-gradient(135deg, var(--brand), var(--brand2)); color: #fff; font-weight: 700; border: none; cursor: pointer; margin-bottom: 12px; box-shadow: 0 4px 14px rgba(79,70,229,0.3); }
    
    .list-toolbar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
    .list-toolbar input,.list-toolbar select{flex:1;min-width:140px}
    .questions-list{display:grid;gap:8px}
    .q-row{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;padding:12px;background:var(--card);backdrop-filter:blur(8px);border:1px solid var(--line);border-radius:14px}
    .q-row .q-cat{display:inline-block;padding:2px 8px;border-radius:20px;font-size:.65rem;font-weight:700;background:rgba(79,70,229,.1);color:var(--brand);margin-bottom:6px}
    .q-row .q-text{font-weight:600;font-size:.9rem} .q-row .q-ans{font-size:.75rem;color:var(--ok);font-weight:700}
    .q-row .del{padding:4px 8px;border-radius:6px;font-weight:700;font-size:.7rem;border:1px solid var(--line);background:transparent;color:var(--err)}
    .q-row .del:hover{background:var(--err);color:#fff}
    
    .tabs{display:flex;gap:4px;padding:4px;background:var(--sunk);border-radius:12px;margin-bottom:16px;overflow-x:auto}
    .tab{padding:10px 16px;border-radius:8px;font-weight:600;font-size:.85rem;color:var(--text2);white-space:nowrap;cursor:pointer}
    .tab.active{background:var(--card);color:var(--brand);box-shadow:var(--shadow)}
    .tab-panel{display:none} .tab-panel.active{display:block;animation: fadeInUp 0.3s ease}
    .form-card{display:grid;gap:12px;background:var(--card);backdrop-filter:blur(8px);border:1px solid var(--line);border-radius:var(--radius);padding:20px}
    .form-card label{font-weight:600;color:var(--text2);font-size:.85rem;display:block;margin-bottom:4px}
    .form-actions{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap} .form-actions.between{justify-content:space-between}
    
    .chip-container { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
    .chip { padding: 8px 14px; border-radius: 50px; background: var(--sunk); border: 1px solid var(--line); font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: all 0.2s; }
    .chip:hover { border-color: var(--brand); }
    .chip.active { background: var(--brand); color: #fff; border-color: var(--brand); }
    .chip.add-new { background: transparent; border: 1px dashed var(--brand); color: var(--brand); }
    
    .test-topbar{background:var(--card);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--line);padding:10px 0;position:sticky;top:0;z-index:30}
    .test-topwrap{display:flex;align-items:center;gap:10px}
    .tp-progress{flex:1;display:flex;align-items:center;gap:8px;font-weight:700;font-size:.9rem}
    .tp-bar{flex:1;max-width:160px;height:5px;background:var(--sunk);border-radius:50px;overflow:hidden}
    .tp-bar span{display:block;height:100%;background:linear-gradient(90deg,var(--brand),var(--brand2));border-radius:50px;transition:width .4s}
    .tp-timer{padding:6px 10px;border-radius:8px;font-family:var(--mono);font-weight:600;background:var(--sunk);font-size:.9rem}
    .tp-timer.warn{color:var(--err);animation:pulse 1s infinite}
    .test-body{padding-top:20px}
    .question-card{background:var(--card);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:var(--radius);padding:20px;box-shadow:var(--shadowMd)}
    .q-cat-top{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.75rem;font-weight:700;background:rgba(79,70,229,.1);color:var(--brand);margin-bottom:10px}
    .q-text-lg{font-size:clamp(1rem,2.5vw,1.3rem);font-weight:700;margin:0 0 16px}
    .opt-list{display:grid;gap:8px}
    .opt{display:flex;align-items:center;gap:12px;padding:12px 14px;border:1.5px solid var(--line2);border-radius:12px;background:var(--bg);font-weight:600;font-size:.95rem;text-align:left;width:100%;cursor:pointer}
    .opt:hover:not(:disabled){border-color:var(--brand);transform:translateX(2px)}
    .opt:disabled{opacity:.95;cursor:default}
    .opt .kbd{width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center;background:var(--sunk);border:1px solid var(--line);font-weight:800;font-size:13px;color:var(--text2);flex-shrink:0}
    .opt.correct{border-color:var(--ok);background:var(--oksoft)} .opt.correct .kbd{background:var(--ok);color:#fff;border-color:var(--ok)}
    .opt.wrong{border-color:var(--err);background:var(--errsoft)} .opt.wrong .kbd{background:var(--err);color:#fff;border-color:var(--err)}
    .explanation{margin-top:14px;padding:12px;background:rgba(79,70,229,.06);border-left:3px solid var(--brand);border-radius:8px;color:var(--text2);font-size:.9rem}
    .test-actions{display:flex;justify-content:space-between;gap:8px;margin-top:16px}
    
    .result-hero{max-width:560px;margin:auto;text-align:center;padding:28px 16px;background:var(--card);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadowLg)}
    .result-emoji{font-size:3.5rem;animation:popIn .8s}
    .result-hero h2{font-size:1.8rem;font-weight:800;margin-bottom:6px}
    .ring-wrap{position:relative;width:160px;height:160px;margin:20px auto}
    .ring{width:100%;height:100%;transform:rotate(-90deg)}
    .ring-bg{fill:none;stroke:var(--sunk);stroke-width:9} .ring-fg{fill:none;stroke:url(#gradRing);stroke-width:9;stroke-linecap:round;stroke-dasharray:267;stroke-dashoffset:267}
    .ring-center{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center}
    .ring-center b{font-size:2rem;font-weight:800} .ring-center span{font-size:.7rem;color:var(--muted);text-transform:uppercase}
    .result-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:20px 0}
    @media(max-width:400px){.result-grid{grid-template-columns:repeat(2,1fr)}}
    .result-grid>div{padding:12px;background:var(--card);border:1px solid var(--line);border-radius:12px}
    .result-grid b{display:block;font-size:1.4rem}
    .result-actions{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:20px}
    .review-list{margin-top:20px;display:grid;gap:10px}
    .review-card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;text-align:left}
    .rc-status{padding:2px 8px;border-radius:20px;font-size:.65rem;font-weight:800}
    .rc-status.ok{background:var(--oksoft);color:var(--ok)} .rc-status.no{background:var(--errsoft);color:var(--err)} .rc-status.sk{background:var(--sunk);color:var(--muted)}
    .review-card .rc-q{font-weight:700;margin:6px 0;font-size:.9rem}
    .rc-opts{display:grid;gap:4px}
    .rc-opt{padding:6px 8px;border-radius:8px;background:var(--sunk);font-size:.8rem;display:flex;align-items:center;gap:6px;border:1px solid var(--line)}
    .rc-opt.correct{background:var(--oksoft);border-color:transparent;color:var(--ok);font-weight:700}
    .rc-opt.wrong{background:var(--errsoft);border-color:transparent;color:var(--err);font-weight:700;text-decoration:line-through}
    
    .lb-item { display: flex; align-items: center; gap: 12px; padding: 12px 14px; background: var(--card); backdrop-filter: blur(8px); border: 1px solid var(--line); border-radius: 14px; margin-bottom: 8px; }
    .lb-rank { width: 32px; height: 32px; border-radius: 50%; background: var(--sunk); display: grid; place-items: center; font-weight: 800; font-size: 0.9rem; color: var(--brand); }
    .lb-rank.gold { background: linear-gradient(135deg, #f59e0b, #f97316); color: #fff; }
    .lb-rank.silver { background: linear-gradient(135deg, #94a3b8, #64748b); color: #fff; }
    .lb-rank.bronze { background: linear-gradient(135deg, #b45309, #92400e); color: #fff; }
    .lb-info h5 { font-size: 0.95rem; margin: 0; }
    .lb-info p { font-size: 0.75rem; color: var(--muted); margin: 0; font-family: var(--mono); }
    .lb-score { margin-left: auto; font-weight: 800; font-size: 1.1rem; color: var(--brand); }
    
    .modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);justify-content:center;align-items:center;z-index:5000;padding:16px;backdrop-filter:blur(4px)}
    .modal.active{display:flex}
    .modal-content{background:var(--card);padding:28px;border-radius:var(--radius);max-width:440px;width:100%;box-shadow:var(--shadowLg);animation:popIn 0.3s ease}
    .modal-header{font-size:1.25rem;font-weight:800;margin-bottom:8px;color:var(--text)} .modal-sub{color:var(--text2);font-size:.85rem;margin-bottom:16px;font-style:italic}
    .modal-footer{display:flex;gap:8px;margin-top:20px;justify-content:flex-end}
    .loading-overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);display:none;justify-content:center;align-items:center;z-index:9999;backdrop-filter:blur(4px)}
    .loading-overlay.active{display:flex}
    .loading-box{background:var(--card);padding:32px;border-radius:16px;text-align:center;animation:popIn 0.3s ease}
    .spinner{border:4px solid var(--sunk);border-top:4px solid var(--brand);border-radius:50%;width:46px;height:46px;animation:spin 1s linear infinite;margin:0 auto 14px}
    @keyframes spin{0%{transform:rotate(0)}100%{transform:rotate(360deg)}}
    
    .export-card{background:var(--card);backdrop-filter:blur(8px);border:1px solid var(--line);border-radius:var(--radius);padding:20px}
    .export-card h3{font-size:1.1rem;margin-bottom:6px} .export-card p{color:var(--text2);font-size:.85rem;margin-bottom:16px;font-style:italic}
    .toast{position:fixed;left:50%;bottom:80px;transform:translate(-50%,150%);padding:12px 18px;border-radius:12px;background:var(--text);color:#fff;font-weight:600;font-size:.85rem;box-shadow:var(--shadowLg);z-index:100;pointer-events:none;opacity:0;transition:.3s;max-width:calc(100% - 32px)}
    .toast.show{transform:translate(-50%,0);opacity:1} .toast.success{background:var(--ok)} .toast.error{background:var(--err)}
    #confetti{position:fixed;inset:0;pointer-events:none;z-index:99}
  </style>
</head>
<body data-theme="light">
<div class="bg-blob blob-1"></div>
<div class="bg-blob blob-2"></div>

<svg width="0" height="0" style="position:absolute">
  <defs>
    <linearGradient id="gradRing" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4f46e5"/><stop offset="60%" stop-color="#8b5cf6"/><stop offset="100%" stop-color="#ec4899"/>
    </linearGradient>
  </defs>
</svg>

<div class="loading-overlay" id="loadingOverlay">
  <div class="loading-box"><div class="spinner"></div><p style="font-weight:600;color:var(--text2)">Loading...</p></div>
</div>

<div class="modal" id="passwordModal">
  <div class="modal-content">
    <div class="modal-header" id="modalHeader">Authentication Required</div>
    <p class="modal-sub" id="modalSub">Please enter the password to proceed.</p>
    <input type="password" id="modalPassword" placeholder="Enter password" autocomplete="off">
    <div class="modal-footer">
      <button class="btn-ghost" onclick="closePasswordModal()">Cancel</button>
      <button class="btn-primary" onclick="submitModalPassword()">Submit</button>
    </div>
  </div>
</div>

<header class="navbar">
  <div class="container nav-wrap">
    <a class="brand" href="#" onclick="nav('welcome');return false;"><span class="brand-dot"></span>MockTest<span style="color:var(--brand2)">.pro</span></a>
    <div class="nav-right">
      <span class="user-chip" id="userChip" hidden onclick="nav('analytics')"><span class="dot-live"></span><span id="userName"></span></span>
      <button id="themeToggle" class="icon-btn" title="Toggle Theme">
        <svg class="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>
        <svg class="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      </button>
    </div>
  </div>
</header>

<section id="welcomeScreen" class="screen active">
  <div class="container hero">
    <div class="hero-tag"><span class="dot-live"></span> Premium Edition • Multi-User</div>
    <h1 class="hero-title">Practice <span class="grad-word">Smart</span>,<br/>Achieve <span class="grad-word">Instantly</span>.</h1>
    <p class="hero-sub">No login required. Enter your name, select a category, and start testing. Earn XP and climb the leaderboard.</p>
    <div class="name-card">
      <label for="nameInput">Your Name</label>
      <div class="name-row">
        <input id="nameInput" type="text" placeholder="e.g. — Rahul Sharma" autocomplete="off" autofocus required>
        <button id="startBtn" class="btn-primary" type="button">Enter <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M13 5l7 7-7 7"/></svg></button>
      </div>
      <p style="font-size:.75rem;color:var(--muted);margin-top:8px;font-style:italic;">Your profile is saved locally. No data is uploaded to any server.</p>
    </div>
  </div>
</section>

<section id="dashboardScreen" class="screen">
  <div class="container">
    <div class="profile-card glass-card stagger-item" style="animation-delay:0s">
      <div class="pc-left">
        <h2>Welcome, <span id="helloName" class="grad-word">Guest</span> 👋</h2>
        <p id="streakText">🔥 Daily Streak: 0 days</p>
      </div>
      <div class="pc-right">
        <div class="level-badge" id="dashLevel">1</div>
        <span>Level</span>
      </div>
    </div>
    
    <div class="quick-stats" id="quickStats"></div>
    
    <div class="page-head" style="margin-top:24px">
      <div><p class="eyebrow">Quick Access</p><h2 class="page-title">What would you like to do?</h2></div>
    </div>
    <div class="grid-2" id="actionGrid"></div>
    
    <div class="section-h">Recent Activity</div>
    <div id="recentList" class="test-list"></div>
  </div>
</section>

<section id="leaderboardScreen" class="screen">
  <div class="container">
    <div class="page-head">
      <div><p class="eyebrow">Rankings</p><h2 class="page-title">Leaderboard 🏆</h2></div>
      <button class="btn-ghost" onclick="nav('dashboard')">← Home</button>
    </div>
    <div id="leaderboardList"></div>
  </div>
</section>

<section id="categoriesScreen" class="screen">
  <div class="container">
    <div class="page-head"><div><p class="eyebrow">Categories</p><h2 class="page-title">Select Subject</h2></div><button class="btn-ghost" onclick="nav('dashboard')">← Home</button></div>
    <div class="grid-2" id="categoryGrid"></div>
  </div>
</section>

<section id="subcategoriesScreen" class="screen">
  <div class="container">
    <div class="page-head">
      <div><p class="eyebrow" id="subCatName"></p><h2 class="page-title">Topics</h2></div>
      <button class="btn-ghost" onclick="nav('categories')">← Back</button>
    </div>
    <div id="subcategoryList" class="subtopic-grid"></div>
  </div>
</section>

<section id="testsScreen" class="screen">
  <div class="container">
    <div class="page-head">
      <div><p class="eyebrow" id="testCatName"></p><h2 class="page-title">Available Tests</h2></div>
      <button class="btn-ghost" onclick="nav('subcategories')">← Back</button>
    </div>
    <button class="play-all-btn" id="playAllBtn">▶ Play ALL Questions</button>
    <div id="testList" class="test-list"></div>
  </div>
</section>

<section id="testScreen" class="screen">
  <div class="test-topbar"><div class="container test-topwrap"><div class="tp-progress"><span id="tpNow">1</span>/<span id="tpTotal">10</span><div class="tp-bar"><span id="tpBar"></span></div></div><div class="tp-timer" id="tpTimer">⏱ 10:00</div><button id="quitTestBtn" class="btn-ghost sm">Quit</button></div></div>
  <div class="container test-body"><div id="questionCard" class="question-card"></div><div class="test-actions"><button id="prevBtn" class="btn-ghost" disabled>← Previous</button><div style="display:flex;gap:8px"><button id="nextBtn" class="btn-primary">Next →</button><button id="finishBtn" class="btn-primary hidden">Finish ✓</button></div></div></div>
</section>

<section id="resultScreen" class="screen">
  <div class="container">
    <div class="result-hero">
      <div class="result-emoji" id="resultEmoji">🎉</div>
      <h2>Test Complete!</h2>
      <p id="resultSubtitle" style="color:var(--text2);font-style:italic;">Great effort!</p>
      <div class="ring-wrap"><svg class="ring" viewBox="0 0 120 120"><circle cx="60" cy="60" r="52" class="ring-bg"></circle><circle cx="60" cy="60" r="52" class="ring-fg" id="ringFg"></circle></svg><div class="ring-center"><b id="resultPct">0%</b><span>Score</span></div></div>
      <div class="result-grid">
        <div><b id="rCorrect">0</b><span>Correct</span></div>
        <div><b id="rWrong">0</b><span>Wrong</span></div>
        <div><b id="rSkip">0</b><span>Skipped</span></div>
        <div><b id="rTime">00:00</b><span>Time</span></div>
      </div>
      <div class="result-actions">
        <button id="reviewBtn" class="btn-ghost">📖 Review</button>
        <button id="retakeBtn" class="btn-primary">🔄 Retake</button>
        <button class="btn-ghost" onclick="nav('dashboard')">🏠 Dashboard</button>
      </div>
    </div>
    <div id="reviewList" class="review-list hidden"></div>
  </div>
</section>

<section id="manageScreen" class="screen">
  <div class="container">
    <div class="page-head"><div><p class="eyebrow">Question Bank</p><h2 class="page-title">Manage</h2></div><button class="btn-ghost" onclick="nav('dashboard')">← Home</button></div>
    <div class="tabs">
      <button class="tab active" data-tab="add">➕ Add Question</button>
      <button class="tab" data-tab="bulk">📋 Bulk Import</button>
      <button class="tab" data-tab="export">📥 Export</button>
      <button class="tab" data-tab="list">📜 All (<span id="qCount">0</span>)</button>
    </div>
    <div class="tab-panel active" id="tab-add">
      <div class="form-card">
        <div><label>Main Category</label>
          <select id="addCategory" onchange="loadSubcatChips()">
            <option value="G.K.">G.K.</option><option value="Maths">Maths</option><option value="English">English</option><option value="Reasoning">Reasoning</option><option value="Science">Science</option>
          </select>
        </div>
        <div>
          <label>Sub-Category (Topic)</label>
          <div class="chip-container" id="subcatChips"></div>
          <input type="text" id="newSubcatInput" placeholder="Type new topic and press Enter" onkeydown="if(event.key==='Enter'){addNewSubcat();}" style="display:none;">
        </div>
        <div><label>Question</label><textarea id="addQuestion" rows="3" placeholder="Enter your question..."></textarea></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
          <div><label>Option A</label><input id="addOpt0"></div>
          <div><label>Option B</label><input id="addOpt1"></div>
          <div><label>Option C</label><input id="addOpt2"></div>
          <div><label>Option D</label><input id="addOpt3"></div>
        </div>
        <div><label>Correct Answer</label><select id="addCorrect"><option value="0">A</option><option value="1">B</option><option value="2">C</option><option value="3">D</option></select></div>
        <div><label>Explanation (optional)</label><textarea id="addExplanation" rows="2" placeholder="Why is this correct?"></textarea></div>
        <div class="form-actions"><button class="btn-primary" onclick="saveQuestion()">Save Question</button></div>
      </div>
    </div>
    <div class="tab-panel" id="tab-bulk">
      <div class="form-card">
        <div><label>Main Category</label>
          <select id="bulkCategory">
            <option value="G.K.">G.K.</option><option value="Maths">Maths</option><option value="English">English</option><option value="Reasoning">Reasoning</option><option value="Science">Science</option>
          </select>
        </div>
        <div><label>Sub-Category (Topic)</label><input id="bulkSubcategory" placeholder="e.g. World Geography"></div>
        <div><label>JSON Text</label>
          <textarea id="bulkText" rows="10" placeholder='[{"question":"...","options":["A","B","C","D"],"correct":0,"explanation":"..."}]'></textarea>
        </div>
        <div class="form-actions between">
          <button class="btn-primary" onclick="initiateBulkImport()">🔒 Import Questions</button>
        </div>
      </div>
    </div>
    <div class="tab-panel" id="tab-export">
      <div class="export-card">
        <h3>📥 Export All Questions</h3>
        <p>Download all questions in JSON format. Useful for backup or transferring to another device.</p>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
          <button class="btn-primary" onclick="initiateExport()">📥 Export All Questions</button>
          <span style="align-self:center;color:var(--muted);font-size:.8rem;font-style:italic;">🔒 Password protected</span>
        </div>
      </div>
    </div>
    <div class="tab-panel" id="tab-list">
      <div class="list-toolbar">
        <input id="searchQ" type="search" placeholder="🔎 Search..." onkeyup="renderManage()">
        <select id="filterCat" onchange="renderManage()"><option value="">All Categories</option><option value="G.K.">G.K.</option><option value="Maths">Maths</option><option value="English">English</option><option value="Reasoning">Reasoning</option><option value="Science">Science</option></select>
        <button id="clearAllBtn" class="btn-danger" onclick="clearAll()">Clear All</button>
      </div>
      <div id="questionsList" class="questions-list"></div>
    </div>
  </div>
</section>

<nav class="bottom-nav" id="bottomNav">
  <button data-nav="dashboard"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg><span>Home</span></button>
  <button data-nav="categories"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg><span>Test</span></button>
  <button data-nav="leaderboard"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 20V10M12 20V4M6 20v-6"/></svg><span>Ranks</span></button>
  <button data-nav="manage"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg><span>Manage</span></button>
</nav>

<div id="toast" class="toast"></div>
<canvas id="confetti"></canvas>

<script>
let state = { 
  user_id: localStorage.getItem('mtp_uuid') || null, 
  username: localStorage.getItem('mtp_user') || '', 
  currentCategory: '', 
  currentSubcategory: '', 
  currentTest: null, 
  timerInt: null, 
  selectedSubcat: null,
  modalCallback: null 
};

function nav(screen) {
  if (screen === 'welcome') { history.pushState({}, '', '#welcome'); renderScreen('welcome'); return; }
  history.pushState({}, '', '#' + screen);
  renderScreen(screen);
}
window.addEventListener('popstate', () => {
  const hash = window.location.hash.replace('#', '') || 'welcome';
  renderScreen(hash);
});

function renderScreen(screenId) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const map = { welcome:'welcomeScreen', dashboard:'dashboardScreen', categories:'categoriesScreen', subcategories:'subcategoriesScreen', tests:'testsScreen', test:'testScreen', result:'resultScreen', manage:'manageScreen', leaderboard:'leaderboardScreen' };
  const el = document.getElementById(map[screenId]);
  if (el) el.classList.add('active');
  if (screenId === 'dashboard') renderDashboard();
  if (screenId === 'categories') renderCategories();
  if (screenId === 'leaderboard') renderLeaderboard();
  if (screenId === 'manage') renderManage();
  document.querySelectorAll('.bottom-nav button').forEach(b => b.classList.remove('active'));
  const activeBtn = document.querySelector(`.bottom-nav button[data-nav="${screenId}"]`);
  if (activeBtn) activeBtn.classList.add('active');
  window.scrollTo(0,0);
}
document.querySelectorAll('.bottom-nav button').forEach(b => b.addEventListener('click', () => nav(b.dataset.nav)));

let toastTimer;
function toast(msg, type=''){ const t = document.getElementById('toast'); t.className = 'toast show '+type; t.textContent = msg; clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove('show'), 2600); }

function applyTheme(t){ document.body.setAttribute('data-theme', t); localStorage.setItem('mtp_theme', t); }
document.getElementById('themeToggle').addEventListener('click', () => applyTheme(document.body.getAttribute('data-theme') === 'light' ? 'dark' : 'light'));
applyTheme(localStorage.getItem('mtp_theme') || 'light');

function showLoading(show) { document.getElementById('loadingOverlay').classList.toggle('active', show); }

function initializeApp() {
  console.log('🔧 Initializing MockTest Pro...');
  const startBtn = document.getElementById('startBtn');
  const nameInput = document.getElementById('nameInput');
  
  if (!startBtn) {
    console.error('❌ Start button (#startBtn) not found!');
    return;
  }
  if (!nameInput) {
    console.error('❌ Name input (#nameInput) not found!');
    return;
  }
  
  console.log('✅ UI elements found. Attaching event listeners...');
  
  const enterApp = async () => {
    const val = nameInput.value.trim();
    console.log('📝 Entered name:', val);
    
    if (!val) { 
      console.warn('⚠️ Empty name entered');
      toast('Please enter your name','error'); 
      return; 
    }
    
    console.log('🔄 Logging in...');
    showLoading(true);
    
    try {
      const loginData = { username: val, user_id: state.user_id };
      console.log('📤 Sending login request:', loginData);
      
      const res = await fetch('/api/login', {
        method:'POST', 
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(loginData)
      });
      
      console.log('📥 Login response status:', res.status);
      
      if (!res.ok) {
        throw new Error('Login failed with status ' + res.status);
      }
      
      const data = await res.json();
      console.log('✅ Login successful! User data:', data);
      
      state.user_id = data.user_id;
      state.username = data.username;
      localStorage.setItem('mtp_uuid', data.user_id);
      localStorage.setItem('mtp_user', data.username);
      
      document.getElementById('userChip').hidden = false;
      document.getElementById('userName').textContent = data.username;
      
      console.log('✅ Stored in localStorage. Navigating to dashboard...');
      showLoading(false);
      setTimeout(() => nav('dashboard'), 300);
    } catch (e) { 
      console.error('❌ Login error:', e);
      toast('Login failed: ' + e.message,'error'); 
      showLoading(false);
    }
  };
  
  startBtn.onclick = (e) => {
    console.log('🖱️ Start button clicked');
    e.preventDefault();
    enterApp();
  };
  
  nameInput.onkeypress = (e) => {
    if (e.key === 'Enter') {
      console.log('⌨️ Enter key pressed');
      e.preventDefault();
      enterApp();
    }
  };
  
  console.log('✅ Initialization complete!');
}

window.addEventListener('load', () => {
  console.log('📱 Window loaded. Initializing in 100ms...');
  setTimeout(initializeApp, 100);
  
  if (state.user_id) { 
    console.log('🔐 User already logged in. Loading dashboard...');
    document.getElementById('userChip').hidden = false; 
    document.getElementById('userName').textContent = state.username; 
    renderScreen(window.location.hash.replace('#','') || 'dashboard'); 
  }
});

async function renderDashboard() {
  document.getElementById('helloName').textContent = state.username || 'Guest';
  try {
    const stats = await (await fetch(`/api/stats?user_id=${state.user_id}`)).json();
    document.getElementById('dashLevel').textContent = stats.xp ? Math.floor(stats.xp / 100) + 1 : 1;
    document.getElementById('streakText').textContent = `🔥 Daily Streak: ${stats.streak} days`;
    document.getElementById('quickStats').innerHTML = `
      <div class="stat glass-card stagger-item" style="animation-delay:0.05s"><b>${stats.total_questions}</b><span>Questions</span></div>
      <div class="stat glass-card stagger-item" style="animation-delay:0.1s"><b>${stats.total_tests}</b><span>Tests</span></div>
      <div class="stat glass-card stagger-item" style="animation-delay:0.15s"><b>${stats.avg_pct}%</b><span>Average</span></div>
      <div class="stat glass-card stagger-item" style="animation-delay:0.2s"><b>${stats.weak_count}</b><span>Weak</span></div>
    `;
  } catch (e) {}
  
  const grid = document.getElementById('actionGrid');
  grid.innerHTML = `
    <button class="action-card stagger-item" style="animation-delay:0.25s" onclick="nav('categories')"><div class="ac-icon g1">🎯</div><h3>Start Test</h3><p>Select category & topic.</p><span class="ac-arrow">→</span></button>
    <button class="action-card stagger-item" style="animation-delay:0.3s" onclick="nav('leaderboard')"><div class="ac-icon g4">🏆</div><h3>Leaderboard</h3><p>See top rankings.</p><span class="ac-arrow">→</span></button>
    <button class="action-card stagger-item" style="animation-delay:0.35s" onclick="nav('manage');setTimeout(()=>switchTab('add'),100)"><div class="ac-icon g2">➕</div><h3>Add Question</h3><p>Contribute to bank.</p><span class="ac-arrow">→</span></button>
    <button class="action-card stagger-item" style="animation-delay:0.4s" onclick="nav('manage');setTimeout(()=>switchTab('bulk'),100)"><div class="ac-icon g5">📋</div><h3>Bulk Import</h3><p>Upload JSON.</p><span class="ac-arrow">→</span></button>
    <button class="action-card stagger-item" style="animation-delay:0.45s" onclick="nav('manage');setTimeout(()=>switchTab('export'),100)"><div class="ac-icon g6">📥</div><h3>Export Data</h3><p>Backup questions.</p><span class="ac-arrow">→</span></button>
    <button class="action-card stagger-item" style="animation-delay:0.5s" onclick="nav('manage');setTimeout(()=>switchTab('list'),100)"><div class="ac-icon g3">📜</div><h3>All Questions</h3><p>View & manage.</p><span class="ac-arrow">→</span></button>
  `;
  
  const rl = document.getElementById('recentList');
  rl.innerHTML = '<div class="empty">Go to Categories to start a test.</div>';
}

async function renderCategories() {
  const grid = document.getElementById('categoryGrid');
  try {
    const res = await fetch('/api/categories');
    const cats = await res.json();
    const icons = ["🌍","🔢","🇬🇧","🧩","🔬"];
    grid.innerHTML = cats.map((cat,i) => `
      <button class="action-card stagger-item" style="animation-delay:${i*0.05}s" onclick="openCategory('${cat}')">
        <div class="ac-icon g${(i%6)+1}">${icons[i] || '📚'}</div>
        <h3>${cat}</h3><p>Tap to view topics</p><span class="ac-arrow">→</span>
      </button>
    `).join('');
  } catch (e) { grid.innerHTML = '<div class="empty">Failed to load.</div>'; }
}

async function openCategory(cat) {
  state.currentCategory = cat;
  nav('subcategories');
  document.getElementById('subCatName').textContent = cat;
  const list = document.getElementById('subcategoryList');
  list.innerHTML = '<div class="empty">Loading...</div>';
  try {
    const res = await fetch(`/api/subcategories?category=${cat}`);
    const subs = await res.json();
    if (subs.length === 0) { list.innerHTML = '<div class="empty">No topics found.</div>'; return; }
    list.innerHTML = subs.map((s, i) => `
      <button class="subtopic-tile stagger-item" style="animation-delay:${i*0.05}s" onclick="openSubcategory('${escapeAttr(s.name)}')">
        <h4>${escapeHtml(s.name)}</h4><span>${s.count} questions</span>
      </button>
    `).join('');
  } catch (e) { list.innerHTML = '<div class="empty">Error.</div>'; }
}

async function openSubcategory(sub) {
  state.currentSubcategory = sub;
  nav('tests');
  document.getElementById('testCatName').textContent = `${state.currentCategory} • ${sub}`;
  const list = document.getElementById('testList');
  list.innerHTML = '<div class="empty">Loading...</div>';
  try {
    const res = await fetch(`/api/tests?category=${state.currentCategory}&subcategory=${sub}`);
    const tests = await res.json();
    if (tests.length === 0) { list.innerHTML = '<div class="empty">No tests available.</div>'; return; }
    list.innerHTML = tests.map((t, i) => `
      <div class="test-tile stagger-item" style="animation-delay:${i*0.05}s" onclick="startTest(${t.test_number})">
        <div><h4>Test ${t.test_number}</h4><p>${t.count} Questions • 10 Mins</p></div>
        <span class="ac-arrow">→</span>
      </div>
    `).join('');
    document.getElementById('playAllBtn').onclick = () => startTest(null, 'all');
  } catch (e) { list.innerHTML = '<div class="empty">Error.</div>'; }
}

async function startTest(testNum, mode='specific') {
  showLoading(true);
  const body = { user_id: state.user_id, category: state.currentCategory, subcategory: state.currentSubcategory, test_number: testNum, mode: mode };
  try {
    const res = await fetch('/api/start-test', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
    const data = await res.json();
    if (!res.ok) { toast(data.error || 'Error','error'); return; }
    state.currentTest = { questions: data.questions, answers: new Array(data.questions.length).fill(null), currentIdx: 0, startTime: Date.now(), duration: data.timer_min * 60, mode: data.mode, category: state.currentCategory, subcategory: state.currentSubcategory };
    nav('test');
    renderTestQuestion();
    if (data.timer_min > 0) startTimer(data.timer_min * 60);
  } catch (e) { toast('Failed to start','error'); } finally { showLoading(false); }
}
function startTimer(totalSec) {
  clearInterval(state.timerInt);
  state.timerInt = setInterval(() => {
    const passed = Math.floor((Date.now() - state.currentTest.startTime)/1000);
    const left = Math.max(0, totalSec - passed);
    const m = String(Math.floor(left/60)).padStart(2,'0'), s = String(left%60).padStart(2,'0');
    document.getElementById('tpTimer').textContent = `⏱ ${m}:${s}`;
    const timerEl = document.getElementById('tpTimer');
    if (left <= 30) timerEl.classList.add('warn'); else timerEl.classList.remove('warn');
    if (left <= 0) { clearInterval(state.timerInt); submitTest(true); }
  }, 500);
}
function renderTestQuestion() {
  const t = state.currentTest;
  if (!t) return;
  const q = t.questions[t.currentIdx];
  document.getElementById('tpNow').textContent = t.currentIdx + 1;
  document.getElementById('tpTotal').textContent = t.questions.length;
  document.getElementById('tpBar').style.width = ((t.currentIdx+1)/t.questions.length*100)+'%';
  const answered = t.answers[t.currentIdx];
  const card = document.getElementById('questionCard');
  card.innerHTML = `
    <span class="q-cat-top">${escapeHtml(q.category)} • ${escapeHtml(q.subcategory)}</span>
    <h3 class="q-text-lg">${escapeHtml(q.question)}</h3>
    <div class="opt-list">
      ${q.options.map((op,i)=>`<button class="opt ${answered!==null ? (i===q.correct?'correct': (i===answered?'wrong':'')) : ''}" data-i="${i}" ${answered!==null?'disabled':''}><span class="kbd">${String.fromCharCode(65+i)}</span><span>${escapeHtml(op)}</span></button>`).join('')}
    </div>
    ${answered!==null && q.explanation ? `<div class="explanation"><b>💡 Explanation:</b> ${escapeHtml(q.explanation)}</div>` : ''}`;
  
  card.querySelectorAll('.opt').forEach(b => b.addEventListener('click', () => {
    if (state.currentTest.answers[state.currentTest.currentIdx] !== null) return;
    state.currentTest.answers[state.currentTest.currentIdx] = parseInt(b.dataset.i);
    renderTestQuestion();
  }));
  document.getElementById('prevBtn').disabled = t.currentIdx === 0;
  const last = t.currentIdx === t.questions.length-1;
  document.getElementById('nextBtn').classList.toggle('hidden', last);
  document.getElementById('finishBtn').classList.toggle('hidden', !last);
}

document.addEventListener('keydown', (e) => {
  if (!state.currentTest || !document.getElementById('testScreen').classList.contains('active')) return;
  if (state.currentTest.answers[state.currentTest.currentIdx] === null) {
    if (['1','2','3','4'].includes(e.key)) {
      e.preventDefault();
      const idx = parseInt(e.key) - 1;
      document.querySelector(`.opt[data-i="${idx}"]`)?.click();
    }
  } else {
    if (e.key.toLowerCase() === 'n' || e.key === 'Enter') {
      e.preventDefault();
      if (!document.getElementById('nextBtn').classList.contains('hidden')) document.getElementById('nextBtn').click();
      else if (!document.getElementById('finishBtn').classList.contains('hidden')) document.getElementById('finishBtn').click();
    } else if (e.key.toLowerCase() === 'p' || e.key === 'Backspace') {
      e.preventDefault();
      if (!document.getElementById('prevBtn').disabled) document.getElementById('prevBtn').click();
    }
  }
});

document.getElementById('prevBtn').addEventListener('click', ()=>{ if (state.currentTest.currentIdx > 0) { state.currentTest.currentIdx--; renderTestQuestion(); } });
document.getElementById('nextBtn').addEventListener('click', ()=>{ if (state.currentTest.currentIdx < state.currentTest.questions.length-1) { state.currentTest.currentIdx++; renderTestQuestion(); } });
document.getElementById('finishBtn').addEventListener('click', ()=> submitTest(false));
document.getElementById('quitTestBtn').addEventListener('click', ()=>{ if (confirm('Quit test? Progress will not be saved.')) { clearInterval(state.timerInt); nav('dashboard'); } });

async function submitTest(timeUp) {
  clearInterval(state.timerInt);
  const t = state.currentTest;
  const answers = t.questions.map((q,i) => ({question_id: q.id, selected: t.answers[i]}));
  const timeSec = Math.floor((Date.now() - t.startTime)/1000);
  showLoading(true);
  try {
    const res = await fetch('/api/submit-test', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ user_id: state.user_id, answers, time_sec: timeSec, category: t.category, subcategory: t.subcategory, mode: t.mode }) });
    const data = await res.json();
    document.getElementById('rCorrect').textContent = data.correct;
    document.getElementById('rWrong').textContent = data.wrong;
    document.getElementById('rSkip').textContent = data.skipped;
    document.getElementById('rTime').textContent = `${String(Math.floor(timeSec/60)).padStart(2,'0')}:${String(timeSec%60).padStart(2,'0')}`;
    
    const pct = data.pct;
    const emoji = pct>=90?'🏆':pct>=70?'🎉':pct>=50?'👍':'📚';
    document.getElementById('resultEmoji').textContent = emoji;
    document.getElementById('resultSubtitle').textContent = (pct>=90?'Outstanding!':pct>=70?'Great job!':pct>=50?'Good effort!':'Keep practicing!') + (timeUp?' (Time up)':'');
    
    nav('result');
    
    const ring = document.getElementById('ringFg');
    const circum = 2 * Math.PI * 52;
    ring.style.strokeDasharray = circum;
    ring.style.strokeDashoffset = circum;
    void ring.offsetWidth;
    ring.style.transition = 'stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)';
    ring.style.strokeDashoffset = circum - (circum * pct / 100);
    
    const target = pct;
    const duration = 1500;
    const startTime = performance.now();
    function animateCount(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const currentVal = Math.round(target * progress);
      document.getElementById('resultPct').textContent = currentVal + '%';
      if (progress < 1) requestAnimationFrame(animateCount);
      else document.getElementById('resultPct').textContent = target + '%';
    }
    requestAnimationFrame(animateCount);
    
    if (pct >= 70) { fireConfetti(); }
    
    const rl = document.getElementById('reviewList');
    rl.classList.add('hidden');
    rl.innerHTML = t.questions.map((q,i)=>{
      const ans = t.answers[i]; const status = ans===null?'sk': ans===q.correct?'ok':'no'; const label = status==='ok'?'Correct': status==='no'?'Wrong':'Skipped';
      return `<div class="review-card"><div style="display:flex;justify-content:space-between;align-items:center"><span class="q-cat-top">${escapeHtml(q.category)} • ${escapeHtml(q.subcategory)} Q${i+1}</span><span class="rc-status ${status}">${label}</span></div><p class="rc-q">${escapeHtml(q.question)}</p><div class="rc-opts">${q.options.map((op,j)=>{ let cls=''; if(j===q.correct) cls='correct'; else if(j===ans && ans!==q.correct) cls='wrong'; return `<div class="rc-opt ${cls}"><span style="font-weight:800;width:22px">${String.fromCharCode(65+j)}.</span> ${escapeHtml(op)}</div>`; }).join('')}</div>${q.explanation?`<div class="explanation"><b>💡 Explanation:</b> ${escapeHtml(q.explanation)}</div>`:''}</div>`;
    }).join('');
  } catch (e) { toast('Submit error','error'); } finally { showLoading(false); }
}
document.getElementById('reviewBtn').addEventListener('click', ()=>{ const rl = document.getElementById('reviewList'); rl.classList.toggle('hidden'); if (!rl.classList.contains('hidden')) rl.scrollIntoView({behavior:'smooth',block:'start'}); });
document.getElementById('retakeBtn').addEventListener('click', ()=> nav('categories'));

function switchTab(tabName) {
  document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(x => x.classList.remove('active'));
  const tab = document.querySelector(`.tab[data-tab="${tabName}"]`);
  if (tab) tab.classList.add('active');
  const panel = document.getElementById('tab-'+tabName);
  if (panel) panel.classList.add('active');
}
document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', ()=> switchTab(t.dataset.tab)));

async function loadSubcatChips() {
  const cat = document.getElementById('addCategory').value;
  const container = document.getElementById('subcatChips');
  state.selectedSubcat = null;
  container.innerHTML = '<div class="empty" style="padding:5px">Loading...</div>';
  try {
    const res = await fetch(`/api/subcategories?category=${cat}`);
    const subs = await res.json();
    container.innerHTML = subs.map(s => `<div class="chip" onclick="selectSubcat('${escapeAttr(s.name)}')">${escapeHtml(s.name)}</div>`).join('');
    container.innerHTML += `<div class="chip add-new" onclick="showNewSubcatInput()">+ Add New</div>`;
  } catch (e) { container.innerHTML = '<div class="empty">Error</div>'; }
}
function selectSubcat(name) {
  state.selectedSubcat = name;
  document.querySelectorAll('#subcatChips .chip').forEach(c => {
    c.classList.toggle('active', c.textContent === name);
  });
}
function showNewSubcatInput() {
  document.getElementById('newSubcatInput').style.display = 'block';
  document.getElementById('newSubcatInput').focus();
}
function addNewSubcat() {
  const val = document.getElementById('newSubcatInput').value.trim();
  if (!val) return;
  state.selectedSubcat = val;
  const container = document.getElementById('subcatChips');
  container.innerHTML = `<div class="chip active">${escapeHtml(val)}</div><div class="chip add-new" onclick="showNewSubcatInput()">+ Add New</div>`;
  document.getElementById('newSubcatInput').style.display = 'none';
  document.getElementById('newSubcatInput').value = '';
}

async function saveQuestion() {
  if (!state.selectedSubcat) { toast('Please select or add a sub-category','error'); return; }
  const data = {
    category: document.getElementById('addCategory').value,
    subcategory: state.selectedSubcat,
    question: document.getElementById('addQuestion').value.trim(),
    options: [document.getElementById('addOpt0').value, document.getElementById('addOpt1').value, document.getElementById('addOpt2').value, document.getElementById('addOpt3').value],
    correct: parseInt(document.getElementById('addCorrect').value),
    explanation: document.getElementById('addExplanation').value.trim()
  };
  if (!data.question || data.options.includes('')) { toast('Fill all fields','error'); return; }
  showLoading(true);
  try {
    await fetch('/api/add-question', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data) });
    toast('Question saved!','success');
    document.getElementById('addQuestion').value = '';
    document.getElementById('addOpt0').value = '';
    document.getElementById('addOpt1').value = '';
    document.getElementById('addOpt2').value = '';
    document.getElementById('addOpt3').value = '';
    document.getElementById('addExplanation').value = '';
    loadSubcatChips();
  } catch (e) { toast('Error saving','error'); } finally { showLoading(false); }
}

function initiateBulkImport() {
  state.modalCallback = async (password) => {
    const category = document.getElementById('bulkCategory').value;
    const subcategory = document.getElementById('bulkSubcategory').value.trim();
    const raw = document.getElementById('bulkText').value.trim();
    if (!raw || !subcategory) { toast('Missing data','error'); return; }
    try {
      const arr = JSON.parse(raw);
      const res = await fetch('/api/import-questions', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ password, category, subcategory, questions: arr }) });
      const data = await res.json();
      if (!res.ok) { toast(data.error || 'Error','error'); return; }
      toast(`${data.added} questions imported!`,'success');
      document.getElementById('bulkText').value = '';
      document.getElementById('bulkSubcategory').value = '';
      renderManage();
    } catch (e) { toast('Invalid JSON','error'); }
  };
  showPasswordModal('🔒 Import Security', 'Enter password to import questions.');
}

function initiateExport() {
  state.modalCallback = async (password) => {
    try {
      const res = await fetch('/api/export-all', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ password }) });
      if (!res.ok) { const data = await res.json().catch(()=>({})); toast(data.error || 'Wrong password!','error'); return; }
      const blob = await res.blob(); const url = window.URL.createObjectURL(blob); const a = document.createElement('a');
      a.href = url; a.download = `questions_export_${new Date().getTime()}.json`; document.body.appendChild(a); a.click();
      window.URL.revokeObjectURL(url); document.body.removeChild(a);
      toast('Export successful! ✓','success');
    } catch (e) { toast('Export error','error'); }
  };
  showPasswordModal('🔐 Export Security', 'Enter password to export questions.');
}

function showPasswordModal(header, sub) {
  document.getElementById('modalHeader').textContent = header;
  document.getElementById('modalSub').textContent = sub;
  document.getElementById('passwordModal').classList.add('active');
  setTimeout(()=>document.getElementById('modalPassword').focus(), 100);
}
function closePasswordModal() { document.getElementById('passwordModal').classList.remove('active'); document.getElementById('modalPassword').value = ''; state.modalCallback = null; }
async function submitModalPassword() {
  const pwd = document.getElementById('modalPassword').value;
  if (!pwd) { toast('Enter password','error'); return; }
  closePasswordModal();
  showLoading(true);
  if (state.modalCallback) await state.modalCallback(pwd);
  showLoading(false);
}

async function clearAll() {
  if (!confirm('Delete entire question bank? This cannot be undone.')) return;
  await fetch('/api/clear-all', { method:'DELETE' });
  renderManage();
  toast('All questions deleted','success');
}

async function renderManage() {
  try {
    const res = await fetch('/api/questions');
    const qs = await res.json();
    document.getElementById('qCount').textContent = qs.length;
    const list = document.getElementById('questionsList');
    const q = (document.getElementById('searchQ').value||'').toLowerCase(), fc = document.getElementById('filterCat').value;
    const filtered = qs.filter(x => (!fc || x.category === fc) && (!q || x.question.toLowerCase().includes(q)));
    list.innerHTML = filtered.length ? filtered.map((x, i) => `<div class="q-row stagger-item" style="animation-delay:${i*0.02}s"><div style="flex:1"><span class="q-cat">${escapeHtml(x.category)} • ${escapeHtml(x.subcategory)}</span><p class="q-text">${escapeHtml(x.question)}</p><div class="q-ans">✓ ${String.fromCharCode(65+x.correct)}. ${escapeHtml(x.options[x.correct])}</div></div><button class="del" onclick="delQ(${x.id})">Delete</button></div>`).join('') : '<div class="empty">No questions found.</div>';
  } catch (e) {}
}
async function delQ(id) { await fetch(`/api/questions/${id}`, { method:'DELETE' }); renderManage(); toast('Deleted','success'); }

async function renderLeaderboard() {
  const list = document.getElementById('leaderboardList');
  list.innerHTML = '<div class="empty">Loading...</div>';
  try {
    const res = await fetch('/api/leaderboard');
    const data = await res.json();
    if (data.length === 0) { list.innerHTML = '<div class="empty">No data yet. Take a test to rank up!</div>'; return; }
    list.innerHTML = data.map((u, i) => `
      <div class="lb-item glass-card stagger-item" style="animation-delay:${i*0.05}s">
        <div class="lb-rank ${i===0?'gold':i===1?'silver':i===2?'bronze':''}">${u.rank}</div>
        <div class="lb-info"><h5>${escapeHtml(u.username)}</h5><p>${u.accuracy}% Accuracy</p></div>
        <div class="lb-score">${u.score_text}</div>
      </div>
    `).join('');
  } catch (e) { list.innerHTML = '<div class="empty">Error loading.</div>'; }
}

const canvas = document.getElementById('confetti'), ctx = canvas.getContext('2d');
function resizeC(){ canvas.width = innerWidth; canvas.height = innerHeight; }
window.addEventListener('resize', resizeC); resizeC();
function fireConfetti(){
  const colors = ['#4f46e5','#8b5cf6','#ec4899','#f59e0b','#10b981','#06b6d4']; const pieces = [];
  for (let i=0;i<140;i++) pieces.push({x:innerWidth/2+(Math.random()-0.5)*200,y:innerHeight/3,vx:(Math.random()-0.5)*10,vy:Math.random()*-14-4,g:0.35,s:Math.random()*8+4,c:colors[Math.floor(Math.random()*colors.length)],r:Math.random()*Math.PI,vr:(Math.random()-0.5)*0.3});
  let frames=0;
  function loop(){ ctx.clearRect(0,0,canvas.width,canvas.height); pieces.forEach(p=>{p.vy+=p.g;p.x+=p.vx;p.y+=p.vy;p.r+=p.vr;ctx.save();ctx.translate(p.x,p.y);ctx.rotate(p.r);ctx.fillStyle=p.c;ctx.fillRect(-p.s/2,-p.s/2,p.s,p.s*0.6);ctx.restore();}); frames++; if(frames<180) requestAnimationFrame(loop); else ctx.clearRect(0,0,canvas.width,canvas.height); }
  loop();
}

function escapeHtml(s){ return String(s??'').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function escapeAttr(s){ return String(s??'').replace(/'/g,"\\\\'"); }
document.getElementById('passwordModal').addEventListener('click', e => { if (e.target.id === 'passwordModal') closePasswordModal(); });
</script>
</body>
</html>'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
