import os
import json
import random
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')

# Dynamic Chapter Lists based on JEE Mains Syllabus
CHAPTERS = {
    "11th": {
        "physics": ["Kinematics", "Laws of Motion", "Work, Energy & Power", "Rotational Motion", "Thermodynamics"],
        "chemistry": ["Some Basic Concepts of Chemistry", "Structure of Atom", "Chemical Bonding", "Thermodynamics", "Equilibrium"],
        "maths": ["Sets & Functions", "Quadratic Equations", "Sequences & Series", "Straight Lines", "Permutations & Combinations"]
    },
    "12th": {
        "physics": ["Electrostatics", "Current Electricity", "Magnetism", "Ray Optics", "Modern Physics"],
        "chemistry": ["Solutions", "Electrochemistry", "Chemical Kinetics", "Coordination Compounds", "Aldehydes & Ketones"],
        "maths": ["Matrices & Determinants", "Calculus (Limits/Derivatives)", "Integrals", "Vector Algebra", "3D Geometry"]
    },
    "dropper": {
        "physics": ["Kinematics", "Laws of Motion", "Electrostatics", "Current Electricity", "Modern Physics"],
        "chemistry": ["Structure of Atom", "Chemical Bonding", "Solutions", "Electrochemistry", "Coordination Compounds"],
        "maths": ["Quadratic Equations", "Matrices & Determinants", "Calculus", "Vector Algebra", "3D Geometry"]
    }
}

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/api/get-chapters', methods=['POST'])
def get_chapters():
    data = request.json or {}
    cls = data.get('class', '11th')
    return jsonify(CHAPTERS.get(cls, CHAPTERS['11th']))

@app.route('/api/generate-paper', methods=['POST'])
def generate_paper():
    data = request.json or {}
    selected_chapters = data.get('chapters', {})

    subjects = ['physics', 'chemistry', 'maths']
    paper = {}

    for sub in subjects:
        # Generate 20 MCQs for Section A
        sec_a = []
        for i in range(1, 21):
            sec_a.append({
                "id": f"{sub}_a_{i}",
                "type": "mcq",
                "question": f"[{sub.capitalize()} - Section A MCQ {i}] Solve for the given conditions in {random.choice(selected_chapters.get(sub, ['General']))}:",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct": "Option A",
                "explanation": f"Detailed step-by-step solution for {sub.capitalize()} MCQ question {i}."
            })

        # Generate 5 Integer/Numerical Value Questions for Section B
        sec_b = []
        for i in range(1, 6):
            sec_b.append({
                "id": f"{sub}_b_{i}",
                "type": "integer",
                "question": f"[{sub.capitalize()} - Section B Integer {i}] Find the exact numerical value for the problem in {random.choice(selected_chapters.get(sub, ['General']))}:",
                "correct": "25",
                "explanation": f"Detailed mathematical calculation leading to final integer value 25 for {sub.capitalize()} question {i}."
            })

        paper[sub] = {
            "section_a": sec_a,
            "section_b": sec_b
        }

    return jsonify({"status": "success", "paper": paper})

@app.route('/api/submit-exam', methods=['POST'])
def submit_exam():
    data = request.json or {}
    user_answers = data.get('answers', {})
    paper = data.get('paper', {})

    total_correct = 0
    total_wrong = 0
    total_unattempted = 0
    subject_scores = {"physics": 0, "chemistry": 0, "maths": 0}

    for sub in ['physics', 'chemistry', 'maths']:
        sub_data = paper.get(sub, {})
        all_questions = sub_data.get('section_a', []) + sub_data.get('section_b', [])

        for q in all_questions:
            q_id = q['id']
            user_ans = user_answers.get(q_id, "").strip()

            if not user_ans:
                total_unattempted += 1
            elif user_ans.lower() == str(q['correct']).lower():
                total_correct += 1
                subject_scores[sub] += 4
            else:
                total_wrong += 1
                subject_scores[sub] -= 1

    total_score = sum(subject_scores.values())
    total_attempted = total_correct + total_wrong
    accuracy = round((total_correct / total_attempted * 100), 2) if total_attempted > 0 else 0.0

    return jsonify({
        "status": "success",
        "total_score": total_score,
        "max_score": 300,
        "accuracy": accuracy,
        "total_correct": total_correct,
        "total_wrong": total_wrong,
        "total_unattempted": total_unattempted,
        "subject_scores": subject_scores
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
