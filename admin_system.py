#!/usr/bin/env python3
"""
E-XAM Admin Panel (Tkinter GUI) - Minimal grayscale theme + emoji icons
- Pure Tkinter
- Fixed size: 1000 x 640 (not resizable)
- Removed "active set" usage in GUI
- Refresh buttons added for Manage Sets and Results
- Minimal grayscale palette, emoji icons kept
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
WIN_W = 1000
WIN_H = 640

# Minimal grayscale palette
BG = "#F2F2F2"          # main background
SIDEBAR_BG = "#E6E6E6"  # sidebar
PANEL_BG = "#FFFFFF"    # content panels
BTN_BG = "#D9D9D9"      # button background
BTN_ACTIVE = "#C8C8C8"  # button active background
HDR_BG = "#EDEDED"      # header background
BORDER = "#BFBFBF"      # borders / separators
TEXT = "#000000"        # text color

# ---------------------------
# DATABASE CONNECTION (light OOP)
# ---------------------------
class Database:
    def __init__(self):
        # Update to your DB credentials
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
# TABLE CREATION (no is_active used)
# ---------------------------
def create_tables():
    try:
        with Database() as db:
            # Users table
            db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_name VARCHAR(255) UNIQUE NOT NULL,
                    pin VARCHAR(10) NOT NULL
                )
            """)
            
            # Sets table
            db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sets (
                    set_id INT AUTO_INCREMENT PRIMARY KEY,
                    set_name VARCHAR(255) UNIQUE NOT NULL,
                    date_created DATETIME
                )
            """)
            
            # Questions table
            db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    question_id INT AUTO_INCREMENT PRIMARY KEY,
                    set_id INT,
                    question_text TEXT,
                    answer TEXT,
                    FOREIGN KEY (set_id) REFERENCES sets(set_id) ON DELETE CASCADE
                )
            """)
            
            # Results table
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
            
            print("Tables created successfully!")
    except mysql.connector.Error as e:
        print("Table creation error:", e)
        messagebox.showerror("Database Error", f"Could not create tables:\n{e}")


# ---------------------------
# Helper: simple button creation to preserve minimal look
# ---------------------------
def simple_button(parent, text, command=None, width=None):
    kw = {"bg": BTN_BG, "activebackground": BTN_ACTIVE, "relief": "flat", "bd": 1}
    btn = tk.Button(parent, text=text, command=command, **kw)
    if width:
        btn.config(width=width)
    return btn

# ---------------------------
# Main App
# ---------------------------
class ExamAdminApp(tk.Tk):
    def large_text_dialog(self, title, label, initial_text=""):
        popup = tk.Toplevel()
        popup.title(title)
        popup.geometry("500x500")
        popup.resizable(True, True)

        tk.Label(popup, text=label, font=("Segoe UI", 10)).pack(anchor="w", padx=10, pady=6)

        text_widget = tk.Text(popup, font=("Segoe UI", 10), wrap="word")
        text_widget.pack(fill="both", expand=True, padx=10)
        text_widget.insert("1.0", initial_text)

        result = {"value": None}

        def save_and_close():
            result["value"] = text_widget.get("1.0", "end-1c")
            popup.destroy()

        btn = tk.Button(popup, text="Save", width=12, command=save_and_close)
        btn.pack(pady=8)

        popup.wait_window()
        return result["value"]

    
    def __init__(self):
        super().__init__()
        # --- Disable Treeview column resizing globally ---
        self.style = ttk.Style()
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10))
        self.title("E-XAM Admin Panel")
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.resizable(False, False)  # fixed size
        self.configure(bg=BG)

        # Fonts & style
        self.default_font = ("Segoe UI", 10)
        self.header_font = ("Segoe UI", 16, "bold")

        # frames
        self.login_frame = None
        self.main_frame = None
        self.content_frame = None

        create_tables()
        self.show_login()
        
    def make_treeview_sortable(self, tree):
        """Enable click-to-sort on Treeview columns."""
        # store sort state per column
        sort_state = {}

        def sort_column(col):
            # Get current data
            data = [(tree.set(k, col), k) for k in tree.get_children("")]

            # detect numeric columns
            def try_num(v):
                try:
                    return float(v.replace("%", ""))  # handles percentages
                except:
                    return v.lower() if isinstance(v, str) else v

            # toggle ASC/DESC
            reverse = sort_state.get(col, False)
            data.sort(key=lambda t: try_num(t[0]), reverse=reverse)

            # Apply sorting
            for idx, (_, item_id) in enumerate(data):
                tree.move(item_id, "", idx)

            # Toggle for next click
            sort_state[col] = not reverse

            # update arrows
            for c in tree["columns"]:
                label = c
                if c == col:
                    label += " ▲" if not reverse else " ▼"
                tree.heading(c, text=label, command=lambda _c=c: sort_column(_c))

        # initial bind
        for col in tree["columns"]:
            tree.heading(col, text=col, command=lambda _c=col: sort_column(_c))

        
    def limit_treeview_column_widths(self, tree, max_total_width=None):
        """Prevents Treeview columns from being resized beyond a certain total width."""
        if max_total_width is None:
            max_total_width = WIN_W - getattr(self, "left_width", 220) - 40  # leave margin for sidebar + padding

        def on_resize(event):
            total_width = sum([tree.column(c)["width"] for c in tree["columns"]])
            if total_width > max_total_width:
                # Reduce last column to fit
                overflow = total_width - max_total_width
                last_col = tree["columns"][-1]
                new_width = max(tree.column(last_col)["width"] - overflow, 50)  # minimum width 50px
                tree.column(last_col, width=new_width)

        tree.bind("<ButtonRelease-1>", on_resize)  # after resizing finishes
        


    # ---------------------------
    # Login
    # ---------------------------
    def show_login(self):
        if self.main_frame:
            self.main_frame.destroy()
            self.main_frame = None
        if self.login_frame:
            self.login_frame.destroy()

        self.login_frame = tk.Frame(self, bg=BG)
        self.login_frame.pack(fill="both", expand=True)

        container = tk.Frame(self.login_frame, bg=BG, padx=24, pady=24)
        container.place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(container, text="E-XAM Admin Login", font=self.header_font, bg=BG).pack(pady=(0,12))
        tk.Label(container, text="Enter admin key:", font=self.default_font, bg=BG).pack(anchor="w")
        self.key_entry = tk.Entry(container, show="*", font=self.default_font, width=28)
        self.key_entry.pack(fill="x", pady=(6,10))
        self.key_entry.focus()

        login_btn = simple_button(container, "Login", command=self.handle_login, width=20)
        login_btn.pack(pady=6)

    def handle_login(self):
        key = self.key_entry.get()
        if key != ADMIN_KEY:
            messagebox.showerror("Access Denied", "Invalid admin key.")
            return
        self.login_frame.destroy()
        self.login_frame = None
        self.show_main()

    # ---------------------------
    # Main UI (sidebar + content)
    # ---------------------------
    def show_main(self):
        # clear any existing main_frame
        if self.main_frame:
            self.main_frame.destroy()

        self.main_frame = tk.Frame(self, bg=BG)
        self.main_frame.pack(fill="both", expand=True)

        # Sidebar
        self.left_width = 220
        sidebar = tk.Frame(self.main_frame, width=self.left_width, bg=SIDEBAR_BG, relief="flat", bd=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Content area
        self.content_frame = tk.Frame(self.main_frame, bg=BG)
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Logo area (minimal)
        logo_frame = tk.Frame(sidebar, bg=SIDEBAR_BG, height=80)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)
        tk.Label(logo_frame, text="E-XAM", font=("Segoe UI", 18, "bold"), bg=SIDEBAR_BG).pack(pady=(20,0))

        # Nav buttons (emoji icons kept)
        nav_cfg = {"padx": 12, "pady": 6, "fill": "x"}
        self.nav_buttons = {}
        self.nav_buttons['dashboard'] = simple_button(sidebar, "📊  Dashboard", command=lambda: self.load_page(self.page_dashboard))
        self.nav_buttons['dashboard'].pack(**nav_cfg)
        self.nav_buttons['create_set'] = simple_button(sidebar, "📝  Create Set", command=lambda: self.load_page(self.page_create_set))
        self.nav_buttons['create_set'].pack(**nav_cfg)
        self.nav_buttons['manage_sets'] = simple_button(sidebar, "📂  Manage Sets", command=lambda: self.load_page(self.page_manage_sets))
        self.nav_buttons['manage_sets'].pack(**nav_cfg)
        self.nav_buttons['manage_users'] = simple_button(sidebar, "👤 Manage Users", command=lambda: self.load_page(self.page_manage_users))
        self.nav_buttons['manage_users'].pack(**nav_cfg)
        self.nav_buttons['results'] = simple_button(sidebar, "📑  View Results", command=lambda: self.load_page(self.page_view_results))
        self.nav_buttons['results'].pack(**nav_cfg)

        # Logout (bottom)
        logout_btn = simple_button(sidebar, "🔓  Logout", command=self.logout)
        logout_btn.pack(side="bottom", fill="x", padx=12, pady=12)

        # Load default page
        self.load_page(self.page_dashboard)

    def logout(self):
        if messagebox.askyesno("Logout", "Log out from admin panel?"):
            if self.main_frame:
                self.main_frame.destroy()
            self.main_frame = None
            self.show_login()

    def load_page(self, page_func):
        # clear content frame
        for w in self.content_frame.winfo_children():
            w.destroy()
        page_func(self.content_frame)

    # ---------------------------
    # Page: Dashboard
    # ---------------------------
    def page_dashboard(self, frame):
        frame.configure(bg=BG)
        header = tk.Frame(frame, bg=HDR_BG, padx=12, pady=8)
        header.pack(fill="x", padx=16, pady=(16,8))
        tk.Label(header, text="📊 Dashboard", font=self.header_font, bg=HDR_BG).pack(anchor="w")
        
        # Stats
        stats_frame = tk.Frame(frame, bg=BG)
        stats_frame.pack(fill="x", padx=20)

        try:
            with Database() as db:
                db.cursor.execute("SELECT COUNT(*) FROM sets")
                total_sets = db.cursor.fetchone()[0] or 0
                db.cursor.execute("SELECT COUNT(DISTINCT user_name) FROM results")
                total_users = db.cursor.fetchone()[0] or 0
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))
            return

        tk.Label(stats_frame, text=f"Total Sets: {total_sets}", font=self.default_font, bg=BG).pack(anchor="w", pady=2)
        tk.Label(stats_frame, text=f"Total Users Who Took Exams: {total_users}", font=self.default_font, bg=BG).pack(anchor="w", pady=2)

        # Averages table
        table_frame = tk.Frame(frame, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=20, pady=12)

        cols = ("Set ID", "Set Name", "Average Score")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        tree.column("Set ID", width=40, minwidth=60, anchor="w", stretch=True)
        tree.column("Set Name", width=200, minwidth=120, anchor="w", stretch=True)
        tree.column("Average Score", width=40, minwidth=140, anchor="w", stretch=True)
        for c in cols:
            tree.heading(c, text=c)
        tree.pack(fill="both", expand=True, side="left")
        
        self.limit_treeview_column_widths(tree)
        self.make_treeview_sortable(tree)


        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        try:
            with Database() as db:
                db.cursor.execute("SELECT set_id, set_name FROM sets ORDER BY set_id DESC")
                sets = db.cursor.fetchall()
                for s in sets:
                    db.cursor.execute("SELECT AVG(score/NULLIF(total,0))*100 FROM results WHERE set_id=%s", (s[0],))
                    avg = db.cursor.fetchone()[0]
                    avg_display = f"{avg:.2f}%" if avg is not None else "No results"
                    tree.insert("", "end", values=(s[0], s[1], avg_display))
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))

    # ---------------------------
    # Page: Create Set
    # ---------------------------
    def page_create_set(self, frame):
        frame.configure(bg=BG)
        header = tk.Frame(frame, bg=HDR_BG, padx=12, pady=8)
        header.pack(fill="x", padx=16, pady=(16,8))
        tk.Label(header, text="📝 Create Question Set", font=self.header_font, bg=HDR_BG).pack(anchor="w")

        form = tk.Frame(frame, bg=BG)
        form.pack(fill="x", padx=20, pady=6)

        tk.Label(form, text="Set Name:", font=self.default_font, bg=BG).grid(row=0, column=0, sticky="w")
        set_name_var = tk.StringVar()
        tk.Entry(form, textvariable=set_name_var, font=self.default_font, width=48).grid(row=0, column=1, sticky="w", padx=8, pady=6)

        qframe = tk.Frame(frame, bg=BG)
        qframe.pack(fill="both", padx=20, pady=(6,12), expand=True)

        tk.Label(qframe, text="Questions (enter question and answer then click Add):", font=self.default_font, bg=BG).pack(anchor="w")

        qinput_frame = tk.Frame(qframe, bg=BG)
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

        add_btn = simple_button(qinput_frame, "Add", command=add_question_to_list)
        add_btn.grid(row=0, column=2, padx=(8,0))

        lstbox = tk.Listbox(qframe, height=8, font=self.default_font)
        lstbox.pack(fill="both", expand=False, pady=(8,0), ipadx=2, ipady=2)

        def remove_selected_question():
            sel = lstbox.curselection()
            if not sel:
                messagebox.showinfo("Remove", "Select a question to remove.")
                return
            idx = sel[0]
            lstbox.delete(idx)
            del questions_list[idx]

        rem_btn = simple_button(qframe, "Remove Selected Question", command=remove_selected_question)
        rem_btn.pack(anchor="e", pady=6)

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
                # Integrity error (duplicate name) or others
                messagebox.showerror("Database Error", str(e))

        save_btn = simple_button(frame, "Save Set", command=save_set_gui)
        save_btn.pack(pady=(6,12))

    # ---------------------------
    # Page: Manage Sets / Questions
    # ---------------------------
    def page_manage_sets(self, frame):
        frame.configure(bg=BG)
        header = tk.Frame(frame, bg=HDR_BG, padx=12, pady=8)
        header.pack(fill="x", padx=16, pady=(16,8))
        tk.Label(header, text="📂 Manage Sets / Questions", font=self.header_font, bg=HDR_BG).pack(anchor="w")

        pane = tk.PanedWindow(frame, orient="horizontal", sashwidth=6)
        pane.pack(fill="both", expand=True, padx=20, pady=10)

        # Left: sets list
        left = tk.Frame(pane, bg=PANEL_BG)
        pane.add(left, width=300)

        tk.Label(left, text="Sets:", font=self.default_font, bg=PANEL_BG).pack(anchor="nw", padx=8, pady=(8,6))
        sets_tree = ttk.Treeview(left, columns=("ID", "Name"), show="headings", height=18)
        sets_tree.heading("ID", text="ID")
        sets_tree.heading("Name", text="Name")
        sets_tree.column("ID", width=60, anchor="center", stretch=True)
        sets_tree.column("Name", width=220, minwidth=140, anchor="w", stretch=True)
        sets_tree.pack(fill="both", expand=True, padx=8, pady=(0,8))

        # Right: questions for selected set
        right = tk.Frame(pane, bg=PANEL_BG)
        pane.add(right)

        tk.Label(right, text="Questions in selected set:", font=self.default_font, bg=PANEL_BG).pack(anchor="nw", padx=8, pady=(8,6))
        q_tree = ttk.Treeview(
            right,
            columns=("ID", "Question", "Answer"),
            show="headings",
            height=14,
            selectmode="extended"   # allow multi-select
            )
        q_tree.heading("ID", text="Q ID")
        q_tree.heading("Question", text="Question")
        q_tree.heading("Answer", text="Answer")
        q_tree.column("ID", width=30, anchor="center", stretch=False)
        q_tree.column("Question", width=90, anchor="w", stretch=True)
        q_tree.column("Answer", width=20, minwidth=140, anchor="w", stretch=True)
        q_tree.pack(fill="both", expand=True, padx=8, pady=(0,8))
        
        self.make_treeview_sortable(sets_tree)
        self.make_treeview_sortable(q_tree)

        btn_frame = tk.Frame(right, bg=PANEL_BG)
        btn_frame.pack(fill="x", padx=8, pady=(4,8))

        def load_sets():
            sets_tree.delete(*sets_tree.get_children())
            try:
                with Database() as db:
                    db.cursor.execute("SELECT set_id, set_name FROM sets ORDER BY set_id DESC")
                    rows = db.cursor.fetchall()
                    for r in rows:
                        sets_tree.insert("", "end", values=r)
                # select first set automatically
                if sets_tree.get_children():
                    first = sets_tree.get_children()[0]
                    sets_tree.selection_set(first)
                    sets_tree.focus(first)
                    load_questions_for_set()
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

        # --- Single loader for selection ---
        def load_questions_for_set(event=None):
            sel = sets_tree.selection()
            q_tree.delete(*q_tree.get_children())
            if not sel:
                return
            set_id = sets_tree.item(sel[0])["values"][0]
            try:
                with Database() as db:
                    db.cursor.execute("SELECT question_id, question_text, answer FROM questions WHERE set_id=%s", (set_id,))
                    for q in db.cursor.fetchall():
                        q_tree.insert("", "end", values=(q[0], q[1], q[2]))
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        sets_tree.bind("<<TreeviewSelect>>", load_questions_for_set)

        def on_set_select(event):
            # wrapper to reload questions (keeps old API used by some buttons)
            load_questions_for_set(event)

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
                load_questions_for_set()
                messagebox.showinfo("Success", "Question added.")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        def edit_question():
            sel = q_tree.selection()
            if not sel:
                messagebox.showinfo("Select Question", "Select a question to edit.")
                return
            q_id, qtext, ans = q_tree.item(sel[0])["values"]
            new_q = self.large_text_dialog("Edit Question", "New question text:", qtext)
            if new_q is None or new_q.strip() == "":
                return
            new_a = self.large_text_dialog("Edit Answer", "New answer:", ans)
            if new_a is None:
                return
            try:
                with Database() as db:
                    db.cursor.execute("UPDATE questions SET question_text=%s, answer=%s WHERE question_id=%s", (new_q.strip(), new_a.strip(), q_id))
                load_questions_for_set()
                messagebox.showinfo("Success", "Question updated.")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        def delete_question():
            sel = q_tree.selection()
            if not sel:
                messagebox.showinfo("Select Question", "Select one or more questions to delete.")
                return

            # Collect selected question IDs
            q_ids = [q_tree.item(item)["values"][0] for item in sel]

            if not messagebox.askyesno(
                "Confirm",
                f"Delete {len(q_ids)} selected question(s)?"
            ):
                return

            try:
                with Database() as db:
                    db.cursor.executemany(
                        "DELETE FROM questions WHERE question_id=%s",
                        [(qid,) for qid in q_ids]
                    )
                load_questions_for_set()
                messagebox.showinfo("Deleted", f"Deleted {len(q_ids)} question(s).")
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
        left_pad = {"side": "left", "padx": 6}
        simple_button(btn_frame, "Add Question", command=add_question_to_set).pack(**left_pad)
        simple_button(btn_frame, "Edit Question", command=edit_question).pack(**left_pad)
        simple_button(btn_frame, "Delete Question", command=delete_question).pack(**left_pad)
        simple_button(btn_frame, "Delete Set", command=delete_set).pack(**left_pad)

        # initial load
        load_sets()

    def page_manage_users(self, frame):
        frame.configure(bg=BG)
        header = tk.Frame(frame, bg=HDR_BG, padx=12, pady=8)
        header.pack(fill="x", padx=16, pady=(16,8))
        tk.Label(header, text="👤 Manage Users", font=self.header_font, bg=HDR_BG).pack(anchor="w")

        table_frame = tk.Frame(frame, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("User ID", "Username", "PIN")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=20)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center" if c=="User ID" else "w", width=100 if c=="PIN" else 160)

        tree.pack(fill="both", expand=True, side="left")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.make_treeview_sortable(tree)

        def load_users():
            tree.delete(*tree.get_children())
            try:
                with Database() as db:
                    db.cursor.execute("SELECT user_id, user_name, pin FROM users ORDER BY user_id DESC")
                    for row in db.cursor.fetchall():
                        tree.insert("", "end", values=row)
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        def add_user():
            username = simpledialog.askstring("Add User", "Enter username:")
            if not username: return
            pin = simpledialog.askstring("PIN", "Enter 4-10 digit PIN:")
            if not pin: return
            try:
                with Database() as db:
                    db.cursor.execute("INSERT INTO users (user_name, pin) VALUES (%s, %s)", (username, pin))
                load_users()
                messagebox.showinfo("Success", f"User '{username}' added.")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        def edit_user():
            sel = tree.selection()
            if not sel: return
            user_id, username, pin = tree.item(sel[0])["values"]
            new_pin = simpledialog.askstring("Edit PIN", f"Edit PIN for {username}:", initialvalue=pin)
            if not new_pin: return
            try:
                with Database() as db:
                    db.cursor.execute("UPDATE users SET pin=%s WHERE user_id=%s", (new_pin, user_id))
                load_users()
                messagebox.showinfo("Success", "PIN updated.")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        def delete_user():
            sel = tree.selection()
            if not sel: return
            user_id, username, _ = tree.item(sel[0])["values"]
            if not messagebox.askyesno("Confirm", f"Delete user '{username}'? This cannot be undone."):
                return
            try:
                with Database() as db:
                    db.cursor.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
                load_users()
                messagebox.showinfo("Deleted", f"User '{username}' deleted.")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        btn_frame = tk.Frame(frame, bg=BG)
        btn_frame.pack(fill="x", padx=20, pady=(4,8))
        simple_button(btn_frame, "Add User", command=add_user).pack(side="left", padx=6)
        simple_button(btn_frame, "Edit User PIN", command=edit_user).pack(side="left", padx=6)
        simple_button(btn_frame, "Delete User", command=delete_user).pack(side="left", padx=6)

        load_users()


    # ---------------------------
    # Page: View Results
    # ---------------------------
    def page_view_results(self, frame):
        frame.configure(bg=BG)
        header = tk.Frame(frame, bg=HDR_BG, padx=12, pady=8)
        header.pack(fill="x", padx=16, pady=(16,8))
        tk.Label(header, text="📘 View All Results", font=self.header_font, bg=HDR_BG).pack(anchor="w")

        table_frame = tk.Frame(frame, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("Result ID", "User", "Set", "Score", "Total", "Date")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=20)

        # Consistent column setup
        tree.column("Result ID", width=80, anchor="center", stretch=False)
        tree.column("User", width=160, anchor="w", stretch=True)
        tree.column("Set", width=240, anchor="w", stretch=True)
        tree.column("Score", width=80, anchor="center", stretch=False)
        tree.column("Total", width=80, anchor="center", stretch=False)
        tree.column("Date", width=90, minwidth=90, anchor="center", stretch=False)

        for c in cols:
            tree.heading(c, text=c)

        tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.make_treeview_sortable(tree)

        def load_results():
            tree.delete(*tree.get_children())
            try:
                with Database() as db:
                    db.cursor.execute("""
                        SELECT r.result_id, r.user_name, s.set_name, r.score, r.total, r.date_taken
                        FROM results r
                        LEFT JOIN sets s ON r.set_id = s.set_id
                        ORDER BY r.date_taken DESC
                    """)
                    rows = db.cursor.fetchall()
                    for r in rows:
                        date_val = r[5]
                        if isinstance(date_val, datetime):
                            date_val = date_val.strftime("%Y-%m-%d %H:%M:%S")
                        display_set = r[2] or "(deleted set)"
                        tree.insert("", "end", values=(r[0], r[1], display_set, r[3], r[4], date_val))
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))


        # Refresh button
        refresh_btn = simple_button(frame, "🔁  Refresh Results", command=load_results)
        refresh_btn.pack(anchor="ne", padx=24, pady=(0,8))

        load_results()

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    app = ExamAdminApp()
    try:
        app.mainloop()
    except Exception:
        pass
