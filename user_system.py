import mysql.connector
from datetime import datetime

# ---------------------------
# DATABASE CONNECTION (light OOP)
# ---------------------------
class Database:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = ""
        self.database = "exam_system"
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.cursor.close()
            self.conn.close()

# ---------------------------
# USER FUNCTIONS
# ---------------------------
def view_active_sets():
    with Database() as db:
        db.cursor.execute("SELECT set_id, set_name FROM sets WHERE is_active = TRUE")
        sets = db.cursor.fetchall()
        if not sets:
            print("No active quizzes available at the moment.\n")
            return []
        print("\nAvailable Quizzes:")
        for s in sets:
            print(f"- ID: {s[0]}, Name: {s[1]}")
        return sets

def take_quiz(user_name):
    active_sets = view_active_sets()
    if not active_sets:
        return

    set_id = input("Enter the Quiz ID you want to take: ")
    with Database() as db:
        db.cursor.execute("SELECT question_id, question_text, answer FROM questions WHERE set_id=%s", (set_id,))
        questions = db.cursor.fetchall()
        if not questions:
            print("No questions in this quiz.\n")
            return

        score = 0
        total = len(questions)

        print(f"\nStarting Quiz '{[s[1] for s in active_sets if str(s[0]) == set_id][0]}'...\n")
        for q in questions:
            print(q[1])
            user_answer = input("Your answer: ")
            if user_answer.strip().lower() == q[2].strip().lower():
                score += 1

        print(f"\nQuiz Finished! Your Score: {score}/{total}")

        # Save result
        db.cursor.execute(
            "INSERT INTO results (user_name, set_id, score, total, date_taken) VALUES (%s, %s, %s, %s, %s)",
            (user_name, set_id, score, total, datetime.now())
        )
        print("Your result has been saved.\n")

def view_user_results(user_name):
    with Database() as db:
        db.cursor.execute("""
            SELECT s.set_name, r.score, r.total, r.date_taken
            FROM results r
            JOIN sets s ON r.set_id = s.set_id
            WHERE r.user_name = %s
        """, (user_name,))
        results = db.cursor.fetchall()
        if not results:
            print("You have not taken any quizzes yet.\n")
        else:
            print("\n=== Your Quiz Results ===")
            for r in results:
                print(f"- Quiz: {r[0]}, Score: {r[1]}/{r[2]}, Date: {r[3]}")

# ---------------------------
# USER PANEL
# ---------------------------
def user_panel():
    print("=== Welcome to the Quiz System ===")
    user_name = input("Enter your name: ")

    while True:
        print("\nOptions:")
        print("1. View Available Quizzes")
        print("2. Take a Quiz")
        print("3. View My Results")
        print("4. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            view_active_sets()
        elif choice == "2":
            take_quiz(user_name)
        elif choice == "3":
            view_user_results(user_name)
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")

# ---------------------------
# RUN SYSTEM
# ---------------------------
if __name__ == "__main__":
    user_panel()
