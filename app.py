from flask import Flask, render_template, request
import csv
from datetime import datetime

app = Flask(__name__)

# Correct answers
answers = {
    'grammar': ["study", "don't watch", "Do you like", "go", "rises", "work", "don't speak", "does leave"],
    'multiple_choice': ["B", "B", "B", "A", "C"],
    'correction': [
        "She goes to work every day.",
        "My dog doesn't like water.",
        "Does he play basketball?",
        "They study English on Monday.",
        "I do not eat breakfast in the morning."
    ],
    'reading': ["London", "7:00 a.m.", "plays football with his friends", "early", "2:30"],
    'listening': ["nurse", "8 o'clock", "help patients and talk to doctors", "yes", "cook dinner and read a book"],
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('student_name', 'Anonymous')
        score = 0
        total = 0

        # Grammar
        for i, key in enumerate(answers['grammar']):
            total += 1
            if request.form.get(f'grammar_{i}', '').strip() == key:
                score += 1

        # Multiple Choice
        for i, key in enumerate(answers['multiple_choice']):
            total += 1
            if request.form.get(f'mc_{i}') == key:
                score += 1

        # Correction
        for i, key in enumerate(answers['correction']):
            total += 1
            if request.form.get(f'correction_{i}', '').strip() == key:
                score += 1

        # Reading
        for i, key in enumerate(answers['reading']):
            total += 1
            if request.form.get(f'reading_{i}', '').strip() == key:
                score += 1

        # Listening
        for i, key in enumerate(answers['listening']):
            total += 1
            if request.form.get(f'listening_{i}', '').strip() == key:
                score += 1

        # Save to CSV
        with open('scores.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, score, total])

        return render_template('result.html', name=name, score=score, total=total)

    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "0690510180Ilyas":
            results = []
            with open('scores.csv', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    results.append(row)
            return render_template('admin.html', results=results)
        else:
            return "Wrong password!"
    return render_template('admin_login.html')

if __name__ == "__main__":
    app.run(debug=True)
