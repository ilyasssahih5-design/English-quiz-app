import csv
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, abort

app = Flask(__name__)

# -----------------------
# ADMIN PASSWORD (your choice)
# -----------------------
ADMIN_PASSWORD = "0690510180Ilyas"

# -----------------------
# QUESTIONS (from what you gave)
# Each item includes a "points" value (you can change)
# -----------------------
questions = {
    "grammar": [   # PART 1 — Fill in blanks (Present Simple)
        {"question": "My sister __________ (study) English every day.", "answer": "studies", "points": 1},
        {"question": "We __________ (not/watch) TV in the morning.", "answer": "do not watch", "points": 1},
        {"question": "__________ you __________ (like) pizza?", "answer": "do you like", "points": 1},
        {"question": "He always __________ (go) to school by bus.", "answer": "goes", "points": 1},
        {"question": "The sun __________ (rise) in the east.", "answer": "rises", "points": 1},
        {"question": "They __________ (work) in a restaurant downtown.", "answer": "work", "points": 1},
        {"question": "My parents __________ (not/speak) French.", "answer": "do not speak", "points": 1},
        {"question": "What time __________ the train __________ (leave)?", "answer": "does the train leave", "points": 1},
    ],
    "multiple_choice": [  # PART 2
        {"question": "She __________ to music every evening.", "options": ["listen", "listens", "listening"], "answer": "listens", "points": 1},
        {"question": "My friends __________ football on weekends.", "options": ["plays", "play", "playing"], "answer": "play", "points": 1},
        {"question": "The shop __________ at 9:00 a.m.", "options": ["open", "opens", "opened"], "answer": "opens", "points": 1},
        {"question": "I __________ coffee in the morning.", "options": ["don’t drink", "doesn’t drink", "not drink"], "answer": "don’t drink", "points": 1},
        {"question": "__________ your brother live near here?", "options": ["Is", "Do", "Does"], "answer": "Does", "points": 1},
    ],
    "correct_mistakes": [  # PART 3 — correct the mistake
        {"question": "She go to work every day.", "answer": "She goes to work every day.", "points": 2},
        {"question": "My dog don’t like water.", "answer": "My dog doesn’t like water.", "points": 2},
        {"question": "Do he play basketball?", "answer": "Does he play basketball?", "points": 2},
        {"question": "They studies English on Monday.", "answer": "They study English on Monday.", "points": 2},
        {"question": "I not eat breakfast in the morning.", "answer": "I do not eat breakfast in the morning.", "points": 2},
    ],
    "reading": [  # PART 4 — reading comprehension (Tom)
        {"question": "Where does Tom live?", "answer": "london", "points": 2},
        {"question": "What time does Tom wake up?", "answer": "7:00 a.m.", "equivalents": ["7:00", "7:00 am", "7 am"], "points": 2},
        {"question": "What does Tom do after school?", "answer": "plays football", "equivalents": ["plays football with his friends", "play football"], "points": 2},
        {"question": "Does Tom go to bed early or late?", "answer": "early", "points": 2},
        {"question": "What time do his classes finish?", "answer": "2:30", "equivalents": ["2:30 pm", "14:30"], "points": 2},
    ],
    "listening": [  # PART 5 — listening (Sarah script)
        {"question": "What is Sarah's job?", "answer": "nurse", "points": 2},
        {"question": "What time does she start work?", "answer": "8 o'clock", "equivalents": ["8:00", "8 am", "8:00 am"], "points": 2},
        {"question": "What does she do at work?", "answer": "helps patients and talks to doctors", "equivalents": ["help patients and talk to doctors", "helps patients", "talks to doctors"], "points": 2},
        {"question": "Does she like her job?", "answer": "yes", "equivalents": ["she likes her job", "yes she does", "yes, she does"], "points": 2},
        {"question": "What does she do in the evening?", "answer": "cooks dinner and reads a book", "equivalents": ["cook dinner and read a book", "cooks dinner", "reads a book"], "points": 2},
    ],
    "writing": [  # PART 6 — writing (student writes 5 sentences)
        {"question": "Write 5 sentences describing your daily routine using the Present Simple.", "points": 4}
    ],
    "speaking": [  # Speaking as text response (you will read later)
        {"question": "Describe aloud (or write) one short paragraph about your daily routine (use Present Simple). If recording is not available, write what you would say.", "points": 3}
    ],
}

# CSV file to store results
CSV_FILE = "results.csv"

# helper: normalize answers for comparison
def normalize(s):
    if s is None:
        return ""
    return " ".join(str(s).strip().lower().replace("’", "'").split())

# calculate score per section and total; return details
def grade_submission(form):
    per_section = {}
    total_score = 0
    total_max = 0
    details = {}

    for section, qlist in questions.items():
        section_score = 0
        section_max = sum(q.get("points", 1) for q in qlist)
        qdetails = []
        for i, q in enumerate(qlist):
            key = f"{section}_{i}"
            user = normalize(form.get(key, ""))
            correct = normalize(q.get("answer", ""))
            equivalents = [normalize(x) for x in q.get("equivalents", [])] if q.get("equivalents") else []
            is_correct = False
            # writing and speaking: store as-is (no automatic correctness)
            if section in ("writing", "speaking"):
                is_correct = None
            else:
                if user == correct or (equivalents and user in equivalents):
                    is_correct = True
                    section_score += q.get("points", 1)
                else:
                    is_correct = False
            qdetails.append({
                "question": q.get("question"),
                "your": form.get(key, ""),
                "expected": q.get("answer"),
                "equivalents": q.get("equivalents", []),
                "points": q.get("points", 1),
                "correct": is_correct
            })
        per_section[section] = {"score": section_score, "max": section_max}
        total_score += section_score
        total_max += section_max
        details[section] = qdetails

    return per_section, total_score, total_max, details

# save to CSV
def save_result_row(name, per_section, total_score, total_max, details):
    # we will save: timestamp, name, per-section scores (as JSON-like), total_score, total_max, writing text, speaking text
    ts = datetime.utcnow().isoformat()
    # extract writing and speaking text (first item each)
    writing_text = ""
    speaking_text = ""
    if details.get("writing"):
        writing_text = details["writing"][0]["your"] if details["writing"][0].get("your") else ""
    if details.get("speaking"):
        speaking_text = details["speaking"][0]["your"] if details["speaking"][0].get("your") else ""
    # per-section summary string
    section_summary = ";".join([f"{sec}:{per_section[sec]['score']}/{per_section[sec]['max']}" for sec in per_section])
    # append row
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([ts, name, section_summary, total_score, total_max, writing_text, speaking_text])

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", questions=questions)

@app.route("/submit", methods=["POST"])
def submit():
    form = request.form
    student_name = form.get("student_name", "Anonymous").strip()
    # grade
    per_section, total_score, total_max, details = grade_submission(form)
    # attach user's raw inputs to details for writing/speaking
    # (fill details entries' "your" already done in grade_submission from form)
    # Save to CSV
    save_result_row(student_name, per_section, total_score, total_max, details)
    # Show result to student (they see their own score)
    return render_template("result.html",
                           student_name=student_name,
                           per_section=per_section,
                           total_score=total_score,
                           total_max=total_max,
                           details=details,
                           questions=questions)

# ADMIN VIEW: protected by password query parameter e.g. /admin?password=YOURPASSWORD
@app.route("/admin", methods=["GET"])
def admin():
    password = request.args.get("password", "")
    if password != ADMIN_PASSWORD:
        # show a simple login-like page with instructions (do not reveal real data)
        return render_template("admin.html", authorized=False, message="Enter password in the URL: /admin?password=YOURPASSWORD")
    # read CSV file and show rows
    rows = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for r in reader:
                if r:
                    # r = [ts, name, section_summary, total_score, total_max, writing_text, speaking_text]
                    rows.append({
                        "timestamp": r[0],
                        "name": r[1],
                        "section_summary": r[2],
                        "total_score": r[3],
                        "total_max": r[4],
                        "writing": r[5],
                        "speaking": r[6] if len(r) > 6 else ""
                    })
    return render_template("admin.html", authorized=True, rows=rows)

if __name__ == "__main__":
    # ensure CSV exists
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "name", "section_summary", "total_score", "total_max", "writing", "speaking"])
    app.run(debug=True)
