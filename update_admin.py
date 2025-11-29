#!/usr/bin/env python3
"""
E-XAM Admin Panel (Tkinter GUI) - Cleaned & Improved (Tkinter)
- Removed 'active set' feature entirely
- Fixed spacing / table widths
- Fixed window size (1000x640) and disabled resizing
- Improved visual layout (still pure Tkinter)
- Uses Database context manager for MySQL connections

Dependencies:
    pip install mysql-connector-python
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
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
            database=self.database,
            autocommit=False
        )
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
            try:
                self.cursor.close()
            except Exception:
                pass
            try:
                self.conn.close()
            except Exception:
                pass

# ---------------------------
# TABLE CREATION (no is_active)
# ---------------------------
def create_tables():
    try:
        with Database() as db:
            db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sets (
                    set_id INT AUTO_INCREMENT PRIMARY KEY,
                    set_name VARCHAR(255) UNIQUE,
                    date_created DATETIME
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
    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", f"Could not create tables:\n{e}")

# ---------------------------
# MAIN APP
# ---------------------------
class ExamAdminApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("E-XAM Admin Panel")
        self.geometry("1000x640")
        self.resizable(False, False)  # FIXED size
        # Global font
        self.default_font = ("Segoe UI", 10)
        self.header_font = ("Segoe UI", 18, "bold")

        # frames
        self.login_frame = None
        self.main_frame = None
        self.content_frame = None

        # Run DB migrations / create tables
        create_tables()
        self.show_login()

    # ---------------------------
    # LOGIN
    # ---------------------------
    def show_login(self):
        if self.main_frame:
            self.main_frame.destroy()
            self.main_frame = None
        if self.login_frame:
            self.login_frame.destroy()

        self.login_frame = tk.Frame(self, bg="#f5f6fa")
        self.login_frame.pack(fill="both", expand=True)

        container = tk.Frame(self.login_frame, padx=30, pady=30, bg="#f5f6fa")
        container.place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(container, text="E-XAM Admin Login", font=self.header_font, bg="#f5f6fa").pack(pady=(0,12))
        tk.Label(container, text="Enter admin key:", font=self.default_font, bg="#f5f6fa").pack(anchor="w")
        self.key_entry = tk.Entry(container, show="*", font=self.default_font, width=30)
        self.key_entry.pack(fill="x", pady=(6,10))
        self.key_entry.focus()

        login_btn = tk.Button(container, text="Login", width=20, command=self.handle_login, bg="#3742fa", fg="white",
                              font=self.default_font, bd=0, activebackground="#5352ed")
        login_btn.pack(pady=6)

    def handle_login(self):
        key = self.key_entry.get()
        if key != ADMIN_KEY:
            messagebox.showerror("Access Denied", "Invalid admin key.")
            return
        # proceed to main UI
        self.login_frame.destroy()
        self.login_frame = None
        self.show_main()

    # ---------------------------
    # MAIN UI (sidebar + content)
    # ---------------------------
    def show_main(self):
        self.main_frame = tk.Frame(self, bg="#e9eef8")
        self.main_frame.pack(fill="both", expand=True)

        # Left sidebar
        sidebar = tk.Frame(self.main_frame, bg="#2d3440", width=220)
        sidebar.pack(side="left", fill="y")

        # Right content area
        self.content_frame = tk.Frame(self.main_frame, bg="#f7f8fb")
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Sidebar content
        logo_frame = tk.Frame(sidebar, bg="#2d3440", height=80)
        logo_frame.pack(fill="x")
        tk.Label(logo_frame, text="E-XAM", font=("Segoe UI", 20, "bold"), bg="#2d3440", fg="white").pack(pady=20)

        def mkbtn(text, cmd):
            b = tk.Button(sidebar, text=text, bg="#3742fa", fg="white", bd=0, relief="flat",
                          font=self.default_font, activebackground="#5352ed", height=2, command=cmd)
            b.pack(fill="x", padx=14, pady=8)
            return b

        mkbtn("Dashboard", lambda: self.load_page(self.page_dashboard))
        mkbtn("Create Set", lambda: self.load_page(self.page_create_set))
        mkbtn("Manage Sets", lambda: self.load_page(self.page_manage_sets))
        mkbtn("View Results", lambda: self.load_page(self.page_view_results))
        mkbtn("Logout", self.logout)

        # load default page
        self.load_page(self.page_dashboard)

    def logout(self):
        if messagebox.askyesno("Logout", "Log out from admin panel?"):
            if self.main_frame:
                self.main_frame.destroy()
            self.main_frame = None
            self.show_login()

    # Utility to clear content frame and load a page
    def load_page(self, page_func):
        for w in self.content_frame.winfo_children():
            w.destroy()
        page_func(self.content_frame)

    # ---------------------------
    # PAGE: Dashboard
    # ---------------------------
    def page_dashboard(self, frame):
        header = tk.Label(frame, text="📊 Dashboard", font=self.header_font, bg="#f7f8fb")
        header.pack(anchor="nw", padx=20, pady=(18,8))

        stats_frame = tk.Frame(frame, bg="#f7f8fb")
        stats_frame.pack(fill="x", padx=20)

        # Collect stats
        try:
            with Database() as db:
                db.cursor.execute("SELECT COUNT(*) FROM sets")
                total_sets = db.cursor.fetchone()[0] or 0
                db.cursor.execute("SELECT COUNT(DISTINCT user_name) FROM results")
                total_users = db.cursor.fetchone()[0] or 0
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))
            return

        stat_labels = [
            f"Total Sets: {total_sets}",
            f"Total Users Who Took Exams: {total_users}"
        ]
        for s in stat_labels:
            tk.Label(stats_frame, text=s, font=self.default_font, bg="#f7f8fb").pack(anchor="w", pady=2)

        # Average per set table
        table_frame = tk.Frame(frame, bg="#f7f8fb")
        table_frame.pack(fill="both", expand=True, padx=20, pady=12)

        cols = ("Set ID", "Set Name", "Average Score")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        # fixed width columns
        tree.column("Set ID", width=80, anchor="center", stretch=False)
        tree.column("Set Name", width=560, anchor="w", stretch=False)
        tree.column("Average Score", width=200, anchor="center", stretch=False)
        for c in cols:
            tree.heading(c, text=c)
        tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # populate averages
        try:
            with Database() as db:
                db.cursor.execute("SELECT set_id, set_name FROM sets ORDER BY set_id DESC")
                sets = db.cursor.fetchall()
                for s in sets:
                    db.cursor.execute("SELECT AVG(score/total)*100 FROM results WHERE set_id=%s", (s[0],))
                    avg = db.cursor.fetchone()[0]
                    avg_display = f"{avg:.2f}%" if avg is not None else "No results"
                    tree.insert("", "end", values=(s[0], s[1], avg_display))
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))

    # ---------------------------
    # PAGE: Create Set
    # ---------------------------
    def page_create_set(self, frame):
        header = tk.Label(frame, text="📝 Create Question Set", font=self.header_font, bg="#f7f8fb")
        header.pack(anchor="nw", padx=20, pady=(18,8))

        form = tk.Frame(frame, bg="#f7f8fb")
        form.pack(fill="x", padx=20, pady=6)

        tk.Label(form, text="Set Name:", font=self.default_font, bg="#f7f8fb").grid(row=0, column=0, sticky="w")
        set_name_var = tk.StringVar()
        tk.Entry(form, textvariable=set_name_var, font=self.default_font, width=48).grid(row=0, column=1, sticky="w", padx=8, pady=6)

        qframe = tk.Frame(frame, bg="#f7f8fb")
        qframe.pack(fill="both", padx=20, pady=(6,12), expand=True)

        tk.Label(qframe, text="Questions (enter question and answer then click Add):", font=self.default_font, bg="#f7f8fb").pack(anchor="w")

        qinput_frame = tk.Frame(qframe, bg="#f7f8fb")
        qinput_frame.pack(fill="x", pady=6)
        q_text_var = tk.StringVar()
        a_text_var = tk.StringVar()

        q_entry = tk.Entry(qinput_frame, textvariable=q_text_var, font=self.default_font, width=70)
        q_entry.grid(row=0, column=0, padx=(0,8))
        a_entry = tk.Entry(qinput_frame, textvariable=a_text_var, font=self.default_font, width=20)
        a_entry.grid(row=0, column=1)

        questions_list = []

        def add_question_to_list():
            qtext = q_text_var.get().strip()
            atext = a_text_var.get().strip()
            if not qtext or not atext:
                messagebox.showwarning("Input required", "Both question and answer are required.")
                return
            questions_list.append((qtext, atext))
            lstbox.insert("end", f"Q: {qtext}  |  A: {atext}")
            q_text_var.set("")
            a_text_var.set("")
            q_entry.focus()

        add_btn = tk.Button(qinput_frame, text="Add", command=add_question_to_list, bg="#3742fa", fg="white", bd=0)
        add_btn.grid(row=0, column=2, padx=(8,0))

        lstbox = tk.Listbox(qframe, height=8, font=("Segoe UI", 10))
        lstbox.pack(fill="both", expand=False, pady=(8,0), ipadx=2, ipady=2)

        def remove_selected_question():
            sel = lstbox.curselection()
            if not sel:
                messagebox.showinfo("Remove", "Select a question to remove.")
                return
            idx = sel[0]
            lstbox.delete(idx)
            del questions_list[idx]

        tk.Button(qframe, text="Remove Selected Question", command=remove_selected_question, bg="#e74c3c", fg="white", bd=0).pack(anchor="e", pady=6)

        def save_set_gui():
            set_name = set_name_var.get().strip()
            if not set_name:
                messagebox.showwarning("Input required", "Set name cannot be empty.")
                return
            if not questions_list:
                if not messagebox.askyesno("No questions", "No questions added. Create empty set?"):
                    return
            try:
                with Database() as db:
                    db.cursor.execute(
                        "INSERT INTO sets (set_name, date_created) VALUES (%s, %s)",
                        (set_name, datetime.now())
                    )
                    db.cursor.execute("SELECT set_id FROM sets WHERE set_name=%s", (set_name,))
                    row = db.cursor.fetchone()
                    if row:
                        set_id = row[0]
                        for q, a in questions_list:
                            db.cursor.execute(
                                "INSERT INTO questions (set_id, question_text, answer) VALUES (%s, %s, %s)",
                                (set_id, q, a)
                            )
                messagebox.showinfo("Success", f"Set '{set_name}' created successfully!")
                # clear
                set_name_var.set("")
                lstbox.delete(0, "end")
                questions_list.clear()
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        tk.Button(frame, text="Save Set", command=save_set_gui, bg="#2ed573", fg="black", font=self.default_font, bd=0).pack(pady=(4,12))

    # ---------------------------
    # PAGE: Manage Sets / Questions
    # ---------------------------
    def page_manage_sets(self, frame):
        header = tk.Label(frame, text="📂 Manage Sets / Questions", font=self.header_font, bg="#f7f8fb")
        header.pack(anchor="nw", padx=20, pady=(18,8))

        pane = tk.PanedWindow(frame, orient="horizontal", sashwidth=6)
        pane.pack(fill="both", expand=True, padx=20, pady=10)

        # Left: sets list
        left = tk.Frame(pane, bg="#ffffff")
        pane.add(left, width=300)

        tk.Label(left, text="Sets:", font=self.default_font, bg="#ffffff").pack(anchor="nw", padx=8, pady=(8,6))
        sets_tree = ttk.Treeview(left, columns=("id", "name"), show="headings", height=18)
        sets_tree.heading("id", text="ID")
        sets_tree.heading("name", text="Name")
        sets_tree.column("id", width=60, anchor="center", stretch=False)
        sets_tree.column("name", width=200, anchor="w", stretch=False)
        sets_tree.pack(fill="both", expand=True, padx=8, pady=(0,8))

        def load_sets():
            for r in sets_tree.get_children():
                sets_tree.delete(r)
            try:
                with Database() as db:
                    db.cursor.execute("SELECT set_id, set_name FROM sets ORDER BY set_id DESC")
                    for s in db.cursor.fetchall():
                        sets_tree.insert("", "end", values=(s[0], s[1]))
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        # Right: questions for selected set
        right = tk.Frame(pane, bg="#f7f7f7")
        pane.add(right)

        tk.Label(right, text="Questions in selected set:", font=self.default_font, bg="#f7f7f7").pack(anchor="nw", padx=8, pady=(8,6))
        q_tree = ttk.Treeview(right, columns=("qid", "qtext", "ans"), show="headings", height=14)
        q_tree.heading("qid", text="Q ID")
        q_tree.heading("qtext", text="Question")
        q_tree.heading("ans", text="Answer")
        q_tree.column("qid", width=80, anchor="center", stretch=False)
        q_tree.column("qtext", width=520, anchor="w", stretch=False)
        q_tree.column("ans", width=180, anchor="w", stretch=False)
        q_tree.pack(fill="both", expand=True, padx=8, pady=(0,8))

        btn_frame = tk.Frame(right, bg="#f7f7f7")
        btn_frame.pack(fill="x", padx=8, pady=(4,8))

        def on_set_select(event):
            sel = sets_tree.selection()
            if not sel:
                return
            set_id = sets_tree.item(sel[0])["values"][0]
            # load questions
            for r in q_tree.get_children():
                q_tree.delete(r)
            try:
                with Database() as db:
                    db.cursor.execute("SELECT question_id, question_text, answer FROM questions WHERE set_id=%s", (set_id,))
                    for q in db.cursor.fetchall():
                        # trim long question display for safety in the view (full is shown when editing)
                        q_tree.insert("", "end", values=(q[0], q[1], q[2]))
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        sets_tree.bind("<<TreeviewSelect>>", on_set_select)

        def add_question_to_set():
            sel = sets_tree.selection()
            if not sel:
                messagebox.showinfo("Select Set", "Select a set to add a question.")
                return
            set_id = sets_tree.item(sel[0])["values"][0]
            qtext = simpledialog.askstring("Add Question", "Enter question text:")
            if qtext is None or qtext.strip() == "":
                return
            ans = simpledialog.askstring("Answer", "Enter answer text:")
            if ans is None:
                return
            try:
                with Database() as db:
                    db.cursor.execute("INSERT INTO questions (set_id, question_text, answer) VALUES (%s, %s, %s)", (set_id, qtext.strip(), ans.strip()))
                on_set_select(None)
                messagebox.showinfo("Success", "Question added.")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        def edit_question():
            sel = q_tree.selection()
            if not sel:
                messagebox.showinfo("Select Question", "Select a question to edit.")
                return
            q_id, qtext, ans = q_tree.item(sel[0])["values"]
            new_q = simpledialog.askstring("Edit Question", "New question text:", initialvalue=qtext)
            if new_q is None or new_q.strip() == "":
                return
            new_a = simpledialog.askstring("Edit Answer", "New answer:", initialvalue=ans)
            if new_a is None:
                return
            try:
                with Database() as db:
                    db.cursor.execute("UPDATE questions SET question_text=%s, answer=%s WHERE question_id=%s", (new_q.strip(), new_a.strip(), q_id))
                on_set_select(None)
                messagebox.showinfo("Success", "Question updated.")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        def delete_question():
            sel = q_tree.selection()
            if not sel:
                messagebox.showinfo("Select Question", "Select a question to delete.")
                return
            q_id = q_tree.item(sel[0])["values"][0]
            if not messagebox.askyesno("Confirm", "Are you sure you want to delete this question?"):
                return
            try:
                with Database() as db:
                    db.cursor.execute("DELETE FROM questions WHERE question_id=%s", (q_id,))
                on_set_select(None)
                messagebox.showinfo("Deleted", "Question deleted.")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        def delete_set():
            sel = sets_tree.selection()
            if not sel:
                messagebox.showinfo("Select Set", "Select a set to delete.")
                return
            set_id = sets_tree.item(sel[0])["values"][0]
            if not messagebox.askyesno("Confirm", "Delete set and all its questions?"):
                return
            try:
                with Database() as db:
                    db.cursor.execute("DELETE FROM sets WHERE set_id=%s", (set_id,))
                load_sets()
                for r in q_tree.get_children():
                    q_tree.delete(r)
                messagebox.showinfo("Deleted", "Set deleted.")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        # Buttons
        bpad = {"side": "left", "padx": 6}
        tk.Button(btn_frame, text="Add Question", command=add_question_to_set, bg="#3742fa", fg="white", bd=0).pack(**bpad)
        tk.Button(btn_frame, text="Edit Question", command=edit_question, bg="#f1c40f", fg="black", bd=0).pack(**bpad)
        tk.Button(btn_frame, text="Delete Question", command=delete_question, bg="#e74c3c", fg="white", bd=0).pack(**bpad)
        tk.Button(btn_frame, text="Delete Set", command=delete_set, bg="#e74c3c", fg="white", bd=0).pack(**bpad)

        # initial load
        load_sets()

    # ---------------------------
    # PAGE: View Results
    # ---------------------------
    def page_view_results(self, frame):
        header = tk.Label(frame, text="📘 View All Results", font=self.header_font, bg="#f7f8fb")
        header.pack(anchor="nw", padx=20, pady=(18,8))

        table_frame = tk.Frame(frame, bg="#f7f8fb")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("Result ID", "User", "Set", "Score", "Total", "Date")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=20)
        # fixed widths
        tree.column("Result ID", width=80, anchor="center", stretch=False)
        tree.column("User", width=160, anchor="w", stretch=False)
        tree.column("Set", width=240, anchor="w", stretch=False)
        tree.column("Score", width=80, anchor="center", stretch=False)
        tree.column("Total", width=80, anchor="center", stretch=False)
        tree.column("Date", width=260, anchor="center", stretch=False)
        for c in cols:
            tree.heading(c, text=c)
        tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Populate
        try:
            with Database() as db:
                db.cursor.execute("""
                    SELECT r.result_id, r.user_name, s.set_name, r.score, r.total, r.date_taken
                    FROM results r
                    JOIN sets s ON r.set_id = s.set_id
                    ORDER BY r.date_taken DESC
                """)
                for r in db.cursor.fetchall():
                    # format date nicely
                    date_str = r[5].strftime("%Y-%m-%d %H:%M:%S") if isinstance(r[5], datetime) else str(r[5])
                    tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4], date_str))
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))

# ---------------------------
# RUN SYSTEM
# ---------------------------
if __name__ == "__main__":
    app = ExamAdminApp()
    app.mainloop()
