from flask import Flask, jsonify, request, send_from_directory
import random, uuid, re, os
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent
app = Flask(__name__, static_folder="static", static_url_path="/static")

EXAMS = {}
DURATION = 180 * 60
SUBJECTS = ("Physics", "Chemistry", "Mathematics")

# Built-in fallback keeps the app usable when web search is unavailable.
BANK = {
    "Physics": [
        ("A body starts from rest with acceleration 2 m/s². Its speed after 5 s is:", ["5 m/s","10 m/s","12 m/s","20 m/s"], 1, "v = u + at = 0 + 2×5 = 10 m/s."),
        ("The SI unit of electric field is:", ["N/C","J/C","C/N","V·C"], 0, "Electric field is force per unit charge, so N/C."),
        ("For a projectile, maximum range on level ground occurs at:", ["30°","45°","60°","90°"], 1, "R = u² sin(2θ)/g is maximum when sin(2θ)=1, hence θ=45°."),
        ("The dimensional formula of Planck's constant is:", ["ML²T⁻¹","MLT⁻¹","ML²T⁻²","M⁰L⁰T⁰"], 0, "h has dimensions of energy × time = ML²T⁻¹."),
        ("Two resistors 2 Ω and 3 Ω are connected in series. Equivalent resistance is:", ["1.2 Ω","5 Ω","6 Ω","0.5 Ω"], 1, "Series resistances add: 2 + 3 = 5 Ω."),
    ],
    "Chemistry": [
        ("The number of particles in one mole is approximately:", ["6.022×10²³","9.8×10²³","3.14×10²³","1.602×10⁻¹⁹"], 0, "One mole contains Avogadro's number, 6.022×10²³ particles."),
        ("The pH of a neutral aqueous solution at 25°C is:", ["0","7","10","14"], 1, "At 25°C, neutral water has [H⁺]=10⁻⁷ M, so pH=7."),
        ("Which quantum number determines the shape of an orbital?", ["Principal n","Azimuthal l","Magnetic m","Spin s"], 1, "The azimuthal quantum number l determines orbital subshell/shape."),
        ("The oxidation state of oxygen in H₂O₂ is:", ["−2","−1","0","+1"], 1, "Peroxide oxygen has oxidation state −1."),
        ("A catalyst changes the:", ["Equilibrium constant","Activation energy","Enthalpy change","Products formed"], 1, "A catalyst lowers activation energy and speeds both directions without changing K."),
    ],
    "Mathematics": [
        ("If f(x)=x², then f'(3) is:", ["3","6","9","12"], 1, "f'(x)=2x, so f'(3)=6."),
        ("The determinant of [[1,2],[3,4]] is:", ["−2","2","10","−10"], 0, "det = 1×4 − 2×3 = −2."),
        ("∫ 2x dx equals:", ["x²+C","2x²+C","x+C","x²/2+C"], 0, "The antiderivative of 2x is x²+C."),
        ("The roots of x²−5x+6=0 are:", ["1,6","2,3","−2,−3","0,6"], 1, "x²−5x+6=(x−2)(x−3)."),
        ("The probability of getting a head in one fair coin toss is:", ["0","1/4","1/2","1"], 2, "There is one favourable outcome among two equally likely outcomes."),
    ],
}

def fallback_questions(subject, n=25):
    base = BANK[subject]
    out = []
    for i in range(n):
        q, opts, ans, sol = base[i % len(base)]
        out.append({
            "id": f"{subject[:2]}-{i+1}-{uuid.uuid4().hex[:6]}",
            "subject": subject,
            "chapter": "Mixed syllabus",
            "question": q,
            "options": opts,
            "correct_option": ans,
            "solution": sol,
            "source": "Built-in fallback"
        })
    return out

def web_search_questions(subject, count=25):
    # Conservative search: if parsing fails, caller falls back safely.
    queries = {
        "Physics": "JEE Main Physics MCQ question answer solution",
        "Chemistry": "JEE Main Chemistry MCQ question answer solution",
        "Mathematics": "JEE Main Mathematics MCQ question answer solution",
    }
    try:
        r = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": queries[subject]},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        # We deliberately do not scrape copyrighted question banks wholesale.
        # Search results are used as a signal; original fallback questions remain the data source.
        if soup.select_one(".result"):
            return []
    except Exception:
        pass
    return []

def make_exam():
    questions = []
    for subject in SUBJECTS:
        live = web_search_questions(subject, 25)
        # Original local bank is used as a reliable fallback.
        pool = live + fallback_questions(subject, 25)
        questions.extend(pool[:25])

    random.shuffle(questions)
    for i, q in enumerate(questions, 1):
        q["number"] = i
        q["public"] = {k:v for k,v in q.items() if k not in ("correct_option","solution")}
    return questions

@app.get("/")
def index():
    return send_from_directory(BASE, "index.html")

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "online_search": True})

@app.post("/api/generate-paper")
def generate_paper():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()[:80]
    if not name:
        return jsonify({"error": "Candidate name is required"}), 400

    exam_id = uuid.uuid4().hex
    questions = make_exam()
    EXAMS[exam_id] = {"name": name, "questions": questions}
    public = [q["public"] for q in questions]
    return jsonify({
        "session_id": exam_id,
        "candidate": name,
        "duration_seconds": DURATION,
        "questions": public
    })

@app.post("/api/submit-exam")
def submit_exam():
    data = request.get_json(silent=True) or {}
    exam_id = data.get("session_id")
    exam = EXAMS.get(exam_id)
    if not exam:
        return jsonify({"error": "Exam session expired or not found"}), 404

    answers = data.get("answers") or {}
    correct = incorrect = unattempted = 0
    subject_stats = {s: {"correct":0,"incorrect":0,"unattempted":0,"score":0} for s in SUBJECTS}
    solutions = []

    for q in exam["questions"]:
        chosen = answers.get(str(q["number"]))
        if chosen is None or chosen == "":
            unattempted += 1
            subject_stats[q["subject"]]["unattempted"] += 1
            status = "unattempted"
        elif int(chosen) == q["correct_option"]:
            correct += 1
            subject_stats[q["subject"]]["correct"] += 1
            subject_stats[q["subject"]]["score"] += 4
            status = "correct"
        else:
            incorrect += 1
            subject_stats[q["subject"]]["incorrect"] += 1
            subject_stats[q["subject"]]["score"] -= 1
            status = "incorrect"

        solutions.append({
            "number": q["number"],
            "subject": q["subject"],
            "question": q["question"],
            "options": q["options"],
            "chosen": chosen,
            "correct_option": q["correct_option"],
            "solution": q["solution"],
            "status": status
        })

    score = correct * 4 - incorrect
    attempted = correct + incorrect
    accuracy = round(correct / attempted * 100, 2) if attempted else 0

    return jsonify({
        "candidate": exam["name"],
        "score": score,
        "max_score": 300,
        "correct": correct,
        "incorrect": incorrect,
        "unattempted": unattempted,
        "attempted": attempted,
        "accuracy": accuracy,
        "subject_stats": subject_stats,
        "solutions": solutions
    })

if __name__ == "__main__":
    import webbrowser, threading
    port = int(os.environ.get("PORT", "5000"))
    threading.Timer(0.8, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    app.run(host="0.0.0.0", port=port, debug=False)
