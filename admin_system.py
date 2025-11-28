"""
E-XAM Admin Panel (Tkinter GUI)
Features:
- Admin login (GUI)
- Sidebar navigation
- Create sets (with adding multiple questions)
- Manage sets: add/edit/delete questions, delete set, set active
- View dashboard (stats)
- View all results (table)
- Uses the provided Database context manager class and same DB schema
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
    try:
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
        self.minsize(900, 600)

        # Top-level frames: login_frame shown first
        self.login_frame = None
        self.main_frame = None

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

        self.login_frame = tk.Frame(self)
        self.login_frame.pack(fill="both", expand=True)

        container = tk.Frame(self.login_frame, padx=30, pady=30)
        container.place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(container, text="E-XAM Admin Login", font=("Segoe UI", 20)).pack(pady=(0,10))
        tk.Label(container, text="Enter admin key:", font=("Segoe UI", 11)).pack(anchor="w")
        self.key_entry = tk.Entry(container, show="*", font=("Segoe UI", 12))
        self.key_entry.pack(fill="x", pady=(0,10))
        self.key_entry.focus()

        login_btn = tk.Button(container, text="Login", width=20, command=self.handle_login)
        login_btn.pack(pady=10)

    def handle_login(self):
        key = self.key_entry.get()
        if key != ADMIN_KEY:
            messagebox.showerror("Access Denied", "Invalid key! Access denied.")
            return
        # proceed to main UI
        self.login_frame.destroy()
        self.login_frame = None
        self.show_main()

    # ---------------------------
    # MAIN UI (sidebar + content)
    # ---------------------------
    def show_main(self):
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)

        # Left sidebar
        sidebar = tk.Frame(self.main_frame, bg="#2f3542", width=220)
        sidebar.pack(side="left", fill="y")

        # Right content area
        self.content_frame = tk.Frame(self.main_frame, bg="#f1f2f6")
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Sidebar buttons
        btn_config = {"fill": "x", "padx": 12, "pady": 8}
        ttk_style = ttk.Style()
        ttk_style.configure("Side.TButton", font=("Segoe UI", 11), foreground="#ffffff")
        # We'll use regular tk.Button for custom colors
        def mkbtn(text, cmd):
            b = tk.Button(sidebar, text=text, bg="#3742fa", fg="white", bd=0, relief="flat",
                          font=("Segoe UI", 11), activebackground="#5352ed", height=2,
                          command=cmd)
            b.pack(fill="x", padx=12, pady=6)
            return b

        mkbtn("Dashboard", lambda: self.load_page(self.page_dashboard))
        mkbtn("Create Set", lambda: self.load_page(self.page_create_set))
        mkbtn("Manage Sets", lambda: self.load_page(self.page_manage_sets))
        mkbtn("View Results", lambda: self.load_page(self.page_view_results))
        mkbtn("Logout", self.logout)

        # load default
        self.load_page(self.page_dashboard)

    def logout(self):
        if messagebox.askyesno("Logout", "Log out from admin panel?"):
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
        header = tk.Label(frame, text="📊 Dashboard", font=("Segoe UI", 20), bg="#f1f2f6")
        header.pack(anchor="nw", padx=20, pady=(20,8))

        # Quick stats frame
        stats_frame = tk.Frame(frame, bg="#f1f2f6")
        stats_frame.pack(fill="x", padx=20)

        # Total sets and active set
        try:
            with Database() as db:
                db.cursor.execute("SELECT COUNT(*) FROM sets")
                total_sets = db.cursor.fetchone()[0]
                db.cursor.execute("SELECT set_id, set_name FROM sets WHERE is_active=TRUE")
                active = db.cursor.fetchone()
                active_name = active[1] if active else "None"
                db.cursor.execute("SELECT COUNT(DISTINCT user_name) FROM results")
                total_users = db.cursor.fetchone()[0] or 0
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))
            return

        tk.Label(stats_frame, text=f"Total Sets: {total_sets}", font=("Segoe UI", 13), bg="#f1f2f6").pack(anchor="w")
        tk.Label(stats_frame, text=f"Active Set: {active_name}", font=("Segoe UI", 13), bg="#f1f2f6").pack(anchor="w")
        tk.Label(stats_frame, text=f"Total Users Who Took Exams: {total_users}", font=("Segoe UI", 13), bg="#f1f2f6").pack(anchor="w")

        # Average per set table
        table_frame = tk.Frame(frame, bg="#f1f2f6")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("Set ID", "Set Name", "Average Score")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center")
        tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # populate averages
        try:
            with Database() as db:
                db.cursor.execute("SELECT set_id, set_name FROM sets")
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
        header = tk.Label(frame, text="📝 Create Question Set", font=("Segoe UI", 20), bg="#f1f2f6")
        header.pack(anchor="nw", padx=20, pady=(20,8))

        form = tk.Frame(frame, bg="#f1f2f6")
        form.pack(fill="x", padx=20, pady=10)

        tk.Label(form, text="Set Name:", font=("Segoe UI", 12), bg="#f1f2f6").grid(row=0, column=0, sticky="w")
        set_name_var = tk.StringVar()
        tk.Entry(form, textvariable=set_name_var, font=("Segoe UI", 12), width=40).grid(row=0, column=1, sticky="w", padx=8, pady=4)

        # Questions listbox + controls
        qframe = tk.Frame(frame, bg="#f1f2f6")
        qframe.pack(fill="both", padx=20, pady=(8,20), expand=True)

        tk.Label(qframe, text="Questions (enter question and answer then click Add):", font=("Segoe UI", 11), bg="#f1f2f6").pack(anchor="w")

        qinput_frame = tk.Frame(qframe, bg="#f1f2f6")
        qinput_frame.pack(fill="x", pady=6)
        q_text_var = tk.StringVar()
        a_text_var = tk.StringVar()

        tk.Entry(qinput_frame, textvariable=q_text_var, font=("Segoe UI", 11), width=60).grid(row=0, column=0, padx=(0,8))
        tk.Entry(qinput_frame, textvariable=a_text_var, font=("Segoe UI", 11), width=20).grid(row=0, column=1)

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

        add_btn = tk.Button(qinput_frame, text="Add", command=add_question_to_list)
        add_btn.grid(row=0, column=2, padx=(8,0))

        lstbox = tk.Listbox(qframe, height=8, font=("Segoe UI", 10))
        lstbox.pack(fill="both", expand=False, pady=(6,0))

        def remove_selected_question():
            sel = lstbox.curselection()
            if not sel:
                messagebox.showinfo("Remove", "Select a question to remove.")
                return
            idx = sel[0]
            lstbox.delete(idx)
            del questions_list[idx]

        tk.Button(qframe, text="Remove Selected Question", command=remove_selected_question).pack(anchor="e", pady=6)

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
                    db.cursor.execute("UPDATE sets SET is_active = FALSE")
                    db.cursor.execute(
                        "INSERT INTO sets (set_name, date_created, is_active) VALUES (%s, %s, TRUE)",
                        (set_name, datetime.now())
                    )
                    db.cursor.execute("SELECT set_id FROM sets WHERE set_name=%s", (set_name,))
                    set_id = db.cursor.fetchone()[0]
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

        tk.Button(frame, text="Save Set", command=save_set_gui, bg="#2ed573", fg="black", font=("Segoe UI", 11)).pack(pady=8)

    # ---------------------------
    # PAGE: Manage Sets / Questions
    # ---------------------------
    def page_manage_sets(self, frame):
        header = tk.Label(frame, text="📂 Manage Sets / Questions", font=("Segoe UI", 20), bg="#f1f2f6")
        header.pack(anchor="nw", padx=20, pady=(20,8))

        pane = tk.PanedWindow(frame, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=20, pady=10)

        # Left: sets list
        left = tk.Frame(pane, bg="#ffffff")
        pane.add(left, width=260)

        tk.Label(left, text="Sets:", font=("Segoe UI", 12), bg="#ffffff").pack(anchor="nw", padx=8, pady=(6,4))
        sets_tree = ttk.Treeview(left, columns=("id","name","active"), show="headings", height=18)
        sets_tree.heading("id", text="ID")
        sets_tree.heading("name", text="Name")
        sets_tree.heading("active", text="Active")
        sets_tree.column("id", width=40, anchor="center")
        sets_tree.column("name", width=160, anchor="w")
        sets_tree.column("active", width=60, anchor="center")
        sets_tree.pack(fill="both", expand=True, padx=8, pady=(0,8))

        def load_sets():
            for r in sets_tree.get_children():
                sets_tree.delete(r)
            try:
                with Database() as db:
                    db.cursor.execute("SELECT set_id, set_name, is_active FROM sets ORDER BY set_id DESC")
                    for s in db.cursor.fetchall():
                        sets_tree.insert("", "end", values=(s[0], s[1], "Yes" if s[2] else "No"))
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        # Right: questions for selected set
        right = tk.Frame(pane, bg="#f7f7f7")
        pane.add(right)

        tk.Label(right, text="Questions in selected set:", font=("Segoe UI", 12), bg="#f7f7f7").pack(anchor="nw", padx=8, pady=(6,4))
        q_tree = ttk.Treeview(right, columns=("qid","qtext","ans"), show="headings", height=14)
        q_tree.heading("qid", text="Q ID")
        q_tree.heading("qtext", text="Question")
        q_tree.heading("ans", text="Answer")
        q_tree.column("qid", width=60, anchor="center")
        q_tree.column("qtext", width=520, anchor="w")
        q_tree.column("ans", width=120, anchor="w")
        q_tree.pack(fill="both", expand=True, padx=8, pady=(0,8))

        # Controls for question actions
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

        def set_active_set():
            sel = sets_tree.selection()
            if not sel:
                messagebox.showinfo("Select Set", "Select a set to set active.")
                return
            set_id = sets_tree.item(sel[0])["values"][0]
            try:
                with Database() as db:
                    db.cursor.execute("UPDATE sets SET is_active = FALSE")
                    db.cursor.execute("UPDATE sets SET is_active = TRUE WHERE set_id=%s", (set_id,))
                load_sets()
                messagebox.showinfo("Active Set", "Active set updated successfully.")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        tk.Button(btn_frame, text="Add Question", command=add_question_to_set).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Edit Question", command=edit_question).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Delete Question", command=delete_question).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Delete Set", command=delete_set).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Set Active", command=set_active_set).pack(side="left", padx=6)

        # initial load
        load_sets()

    # ---------------------------
    # PAGE: View Results
    # ---------------------------
    def page_view_results(self, frame):
        header = tk.Label(frame, text="📘 View All Results", font=("Segoe UI", 20), bg="#f1f2f6")
        header.pack(anchor="nw", padx=20, pady=(20,8))

        table_frame = tk.Frame(frame, bg="#f1f2f6")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("Result ID", "User", "Set", "Score", "Total", "Date")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center")
        tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        try:
            with Database() as db:
                db.cursor.execute("""
                    SELECT r.result_id, r.user_name, s.set_name, r.score, r.total, r.date_taken
                    FROM results r
                    JOIN sets s ON r.set_id = s.set_id
                    ORDER BY r.date_taken DESC
                """)
                for r in db.cursor.fetchall():
                    tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4], r[5]))
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))


# ---------------------------
# RUN SYSTEM
# ---------------------------
if __name__ == "__main__":
    app = ExamAdminApp()
    app.mainloop()
