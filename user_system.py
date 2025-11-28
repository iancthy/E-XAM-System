import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
from datetime import datetime

# ============================================================
# DATABASE CLASS (Same logic, just cleaner)
# ============================================================
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

# ============================================================
# USER GUI APPLICATION
# ============================================================
class QuizUserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz System - User Panel")
        self.root.geometry("500x420")

        self.user_name = ""

        self.build_login_screen()

    # --------------------------------------------------------
    # LOGIN SCREEN
    # --------------------------------------------------------
    def build_login_screen(self):
        self.clear_screen()

        tk.Label(self.root, text="Welcome to the Quiz System",
                 font=("Arial", 16)).pack(pady=20)

        tk.Label(self.root, text="Enter your name:").pack()
        self.user_entry = tk.Entry(self.root, width=30)
        self.user_entry.pack(pady=10)

        tk.Button(self.root, text="Continue",
                  command=self.start_user_panel).pack(pady=15)

    # --------------------------------------------------------
    # MAIN USER MENU
    # --------------------------------------------------------
    def start_user_panel(self):
        name = self.user_entry.get().strip()
        if not name:
            messagebox.showwarning("Error", "Please enter your name!")
            return

        self.user_name = name
        self.build_user_menu()

    def build_user_menu(self):
        self.clear_screen()
    
        tk.Label(self.root, text=f"Hello, {self.user_name}!",
                 font=("Arial", 16)).pack(pady=20)
    
        tk.Button(self.root, text="View Available Quizzes",
                  width=30, command=self.view_active_sets).pack(pady=10)
    
        tk.Button(self.root, text="Take a Quiz",
                  width=30, command=self.take_quiz_select).pack(pady=10)
    
        tk.Button(self.root, text="View My Results",
                  width=30, command=self.view_user_results).pack(pady=10)
    
        # UPDATED — Logout instead of Exit
        tk.Button(self.root, text="Logout",
                  width=30, command=self.build_login_screen).pack(pady=10)

    # --------------------------------------------------------
    # VIEW ACTIVE QUIZZES (GUI)
    # --------------------------------------------------------
    def view_active_sets(self):
        with Database() as db:
            db.cursor.execute("SELECT set_id, set_name FROM sets WHERE is_active = TRUE")
            sets = db.cursor.fetchall()

        win = tk.Toplevel(self.root)
        win.title("Active Quizzes")
        win.geometry("400x300")

        tk.Label(win, text="Available Quizzes", font=("Arial", 14)).pack(pady=10)

        if not sets:
            tk.Label(win, text="No active quizzes found.").pack()
            return

        tree = ttk.Treeview(win, columns=("ID", "Name"), show="headings")
        tree.heading("ID", text="Quiz ID")
        tree.heading("Name", text="Quiz Name")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for s in sets:
            tree.insert("", tk.END, values=(s[0], s[1]))

    # --------------------------------------------------------
    # TAKE QUIZ (Screen to choose quiz)
    # --------------------------------------------------------
    def take_quiz_select(self):
        with Database() as db:
            db.cursor.execute("SELECT set_id, set_name FROM sets WHERE is_active = TRUE")
            self.active_sets = db.cursor.fetchall()

        if not self.active_sets:
            messagebox.showinfo("No Quiz", "No active quizzes available.")
            return

        win = tk.Toplevel(self.root)
        win.title("Select Quiz")
        win.geometry("400x300")

        tk.Label(win, text="Choose a quiz:", font=("Arial", 14)).pack(pady=15)

        self.quiz_var = tk.StringVar()
        quiz_list = ttk.Combobox(win, textvariable=self.quiz_var,
                                 values=[f"{s[0]} - {s[1]}" for s in self.active_sets],
                                 state="readonly", width=35)
        quiz_list.pack(pady=10)

        tk.Button(win, text="Start Quiz",
                  command=lambda: self.start_quiz(win)).pack(pady=20)

    # --------------------------------------------------------
    # TAKE QUIZ (Actual quiz window)
    # --------------------------------------------------------
    def start_quiz(self, parent_win):
        selected = self.quiz_var.get()
        if not selected:
            messagebox.showwarning("Error", "Please select a quiz.")
            return

        parent_win.destroy()

        set_id = selected.split(" - ")[0]

        with Database() as db:
            db.cursor.execute("""
                SELECT question_id, question_text, answer 
                FROM questions WHERE set_id=%s
            """, (set_id,))
            self.questions = db.cursor.fetchall()

        if not self.questions:
            messagebox.showerror("Error", "This quiz has no questions.")
            return

        self.current_index = 0
        self.score = 0
        self.current_set_id = set_id

        self.quiz_window()

    def quiz_window(self):
        self.clear_screen()

        if self.current_index >= len(self.questions):
            self.finish_quiz()
            return

        q_id, question_text, correct_answer = self.questions[self.current_index]

        tk.Label(self.root, text=f"Question {self.current_index + 1}",
                 font=("Arial", 16)).pack(pady=20)

        tk.Label(self.root, text=question_text,
                 font=("Arial", 13), wraplength=450).pack(pady=10)

        self.answer_entry = tk.Entry(self.root, width=40)
        self.answer_entry.pack(pady=10)

        tk.Button(self.root, text="Submit",
                  command=self.submit_answer).pack(pady=20)

    def submit_answer(self):
        user_answer = self.answer_entry.get().strip()
        correct_answer = self.questions[self.current_index][2].strip()

        if user_answer.lower() == correct_answer.lower():
            self.score += 1

        self.current_index += 1
        self.quiz_window()

    # --------------------------------------------------------
    # QUIZ FINISHED
    # --------------------------------------------------------
    def finish_quiz(self):
        total = len(self.questions)

        with Database() as db:
            db.cursor.execute("""
                INSERT INTO results (user_name, set_id, score, total, date_taken)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.user_name, self.current_set_id, self.score, total, datetime.now()))

        messagebox.showinfo("Quiz Finished",
                            f"Your score: {self.score}/{total}\nResult saved!")

        self.build_user_menu()

    # --------------------------------------------------------
    # VIEW USER RESULTS
    # --------------------------------------------------------
    def view_user_results(self):
        with Database() as db:
            db.cursor.execute("""
                SELECT s.set_name, r.score, r.total, r.date_taken
                FROM results r
                JOIN sets s ON r.set_id = s.set_id
                WHERE r.user_name = %s
            """, (self.user_name,))
            results = db.cursor.fetchall()

        win = tk.Toplevel(self.root)
        win.title("My Results")
        win.geometry("500x350")

        tk.Label(win, text="Your Quiz Results", font=("Arial", 14)).pack(pady=10)

        if not results:
            tk.Label(win, text="No results found.").pack()
            return

        tree = ttk.Treeview(win, columns=("Quiz", "Score", "Total", "Date"), show="headings")
        tree.heading("Quiz", text="Quiz")
        tree.heading("Score", text="Score")
        tree.heading("Total", text="Total")
        tree.heading("Date", text="Date Taken")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for r in results:
            tree.insert("", tk.END, values=r)

    # --------------------------------------------------------
    # UTILITY
    # --------------------------------------------------------
    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()


# ============================================================
# RUN SYSTEM
# ============================================================
root = tk.Tk()
app = QuizUserApp(root)
root.mainloop()
