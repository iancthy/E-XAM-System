import mysql.connector
from datetime import datetime

# ---------------------------
# CONFIG
# ---------------------------
ADMIN_KEY = "1234"  # change to your secure admin key

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
# TABLE CREATION
# ---------------------------
def create_tables():
    with Database() as db:
        db.cursor.execute("""
        CREATE TABLE IF NOT EXISTS sets (
            set_id INT AUTO_INCREMENT PRIMARY KEY,
            set_name VARCHAR(255) UNIQUE,
            date_created DATETIME,
            is_active BOOLEAN DEFAULT FALSE
        )
        """)
        db.cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            question_id INT AUTO_INCREMENT PRIMARY KEY,
            set_id INT,
            question_text TEXT,
            answer TEXT,
            FOREIGN KEY (set_id) REFERENCES sets(set_id) ON DELETE CASCADE
        )
        """)
        db.cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            result_id INT AUTO_INCREMENT PRIMARY KEY,
            user_name VARCHAR(255),
            set_id INT,
            score INT,
            total INT,
            date_taken DATETIME,
            FOREIGN KEY (set_id) REFERENCES sets(set_id) ON DELETE CASCADE
        )
        """)

# ---------------------------
# ADMIN LOGIN
# ---------------------------
def admin_login():
    key = input("Enter admin key: ")
    if key != ADMIN_KEY:
        print("Invalid key! Access denied.")
        return False
    return True

# ---------------------------
# CREATE QUESTION SET
# ---------------------------
def create_question_set():
    set_name = input("Enter new set name: ")
    with Database() as db:
        db.cursor.execute("UPDATE sets SET is_active = FALSE")

# Insert new set as active
        db.cursor.execute(
            "INSERT INTO sets (set_name, date_created, is_active) VALUES (%s, %s, TRUE)",
    (set_name, datetime.now())
        )
        db.cursor.execute("SELECT set_id FROM sets WHERE set_name=%s", (set_name,))
        set_id = db.cursor.fetchone()[0]

        while True:
            q = input("Enter question: ")
            a = input("Enter answer: ")
            db.cursor.execute(
                "INSERT INTO questions (set_id, question_text, answer) VALUES (%s, %s, %s)",
                (set_id, q, a)
            )
            more = input("Add another question? (y/n): ")
            if more.lower() != 'y':
                break

    print(f"Set '{set_name}' created successfully!\n")

# ---------------------------
# VIEW SETS
# ---------------------------
def view_sets():
    with Database() as db:
        db.cursor.execute("SELECT set_id, set_name, date_created, is_active FROM sets")
        sets = db.cursor.fetchall()
        if not sets:
            print("No sets available.\n")
        else:
            print("\nAll Question Sets:")
            for s in sets:
                active_mark = " (ACTIVE)" if s[3] else ""
                print(f"- ID: {s[0]}, Name: {s[1]}, Created: {s[2]}{active_mark}")

# ---------------------------
# MANAGE SETS AND QUESTIONS
# ---------------------------
def manage_sets():
    with Database() as db:
        while True:
            view_sets()
            print("\nOptions:")
            print("1. Add Question to Set")
            print("2. Edit Question")
            print("3. Delete Question")
            print("4. Delete Set")
            print("5. Set Active Question Set")
            print("6. Back to Admin Panel")
            choice = input("Enter choice: ")

            if choice == "1":
                while True:
                    # Display available sets
                    db.cursor.execute("SELECT set_id, set_name FROM sets")
                    sets = db.cursor.fetchall()
                    if not sets:
                        print("No sets available. Please create a set first.")
                        break

                    print("\nAvailable Sets:")
                    for s in sets:
                        print(f"- ID: {s[0]}, Name: {s[1]}")

                    set_id = input("Enter Set ID to add question: ")

                    while True:
                        q = input("Enter question: ")
                        a = input("Enter answer: ")
                        db.cursor.execute(
                            "INSERT INTO questions (set_id, question_text, answer) VALUES (%s, %s, %s)",
                            (set_id, q, a)
                        )
                        more = input("Add another question to this set? (y/n): ")
                        if more.lower() != 'y':
                            break

                    add_more_set = input("Do you want to add questions to another set? (y/n): ")
                    if add_more_set.lower() != 'y':
                        break

            elif choice == "2":
                set_id = input("Enter Set ID to edit questions: ")
                db.cursor.execute("SELECT question_id, question_text, answer FROM questions WHERE set_id=%s", (set_id,))
                questions = db.cursor.fetchall()
                if not questions:
                    print("No questions in this set.")
                    continue
                for q in questions:
                    print(f"{q[0]}. {q[1]} -> Answer: {q[2]}")
                q_id = input("Enter Question ID to edit: ")
                new_q = input("New question text: ")
                new_a = input("New answer: ")
                db.cursor.execute(
                    "UPDATE questions SET question_text=%s, answer=%s WHERE question_id=%s",
                    (new_q, new_a, q_id)
                )
                print("Question updated successfully.")

            elif choice == "3":
                set_id = input("Enter Set ID to delete question from: ")
                db.cursor.execute("SELECT question_id, question_text FROM questions WHERE set_id=%s", (set_id,))
                questions = db.cursor.fetchall()
                if not questions:
                    print("No questions in this set.")
                    continue
                for q in questions:
                    print(f"{q[0]}. {q[1]}")
                q_id = input("Enter Question ID to delete: ")
                confirm = input("Are you sure? (y/n): ")
                if confirm.lower() == "y":
                    db.cursor.execute("DELETE FROM questions WHERE question_id=%s", (q_id,))
                    print("Question deleted successfully.")

            elif choice == "4":
                set_id = input("Enter Set ID to delete entire set: ")
                confirm = input("Are you sure? This will delete all questions in the set. (y/n): ")
                if confirm.lower() == "y":
                    db.cursor.execute("DELETE FROM sets WHERE set_id=%s", (set_id,))
                    print("Set deleted successfully.")

            elif choice == "5":
                set_id = input("Enter Set ID to set as ACTIVE: ")
                db.cursor.execute("UPDATE sets SET is_active = FALSE")
                db.cursor.execute("UPDATE sets SET is_active = TRUE WHERE set_id=%s", (set_id,))
                print("Active set updated successfully.")

            elif choice == "6":
                break
            else:
                print("Invalid choice!")

# ---------------------------
# DASHBOARD AND RESULTS
# ---------------------------
def view_results():
    with Database() as db:
        db.cursor.execute("""
            SELECT r.result_id, r.user_name, s.set_name, r.score, r.total, r.date_taken
            FROM results r
            JOIN sets s ON r.set_id = s.set_id
        """)
        results = db.cursor.fetchall()
        if not results:
            print("No results yet.\n")
        else:
            print("\n=== User Results ===")
            for r in results:
                print(f"- User: {r[1]}, Set: {r[2]}, Score: {r[3]}/{r[4]}, Date: {r[5]}")

def view_dashboard():
    with Database() as db:
        print("\n=== Dashboard ===")
        db.cursor.execute("SELECT set_id, set_name, is_active FROM sets")
        sets = db.cursor.fetchall()
        print("Available Sets:")
        for s in sets:
            active_mark = " (ACTIVE)" if s[2] else ""
            print(f"- {s[0]}: {s[1]}{active_mark}")

        db.cursor.execute("SELECT COUNT(DISTINCT user_name) FROM results")
        total_users = db.cursor.fetchone()[0]
        print(f"Total users who took exams: {total_users}")

        for s in sets:
            db.cursor.execute("SELECT AVG(score/total)*100 FROM results WHERE set_id=%s", (s[0],))
            avg = db.cursor.fetchone()[0]
            avg_display = f"{avg:.2f}%" if avg else "No results"
            print(f"Set '{s[1]}' average score: {avg_display}")

# ---------------------------
# ADMIN PANEL LOOP
# ---------------------------
def admin_panel():
    create_tables()
    if not admin_login():
        return

    while True:
        print("\n=== ADMIN PANEL ===")
        print("1. Create Question Set")
        print("2. Manage Sets / Questions")
        print("3. View Dashboard")
        print("4. View All Results")
        print("5. Logout")
        choice = input("Enter choice: ")
        if choice == "1":
            create_question_set()
        elif choice == "2":
            manage_sets()
        elif choice == "3":
            view_dashboard()
        elif choice == "4":
            view_results()
        elif choice == "5":
            print("Logging out...")
            break
        else:
            print("Invalid choice!")

# ---------------------------
# RUN SYSTEM
# ---------------------------
if __name__ == "__main__":
    admin_panel()
