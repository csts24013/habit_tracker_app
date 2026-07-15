import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


DB_FILE = "habit_tracker.db"


class Database:
    def __init__(self, db_file: str = DB_FILE) -> None:
        self.connection = sqlite3.connect(db_file)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self) -> None:
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    unit TEXT NOT NULL,
                    created_date TEXT NOT NULL
                )
                """
            )
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id INTEGER NOT NULL,
                    record_date TEXT NOT NULL,
                    value REAL NOT NULL CHECK(value >= 0),
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(habit_id) REFERENCES habits(id) ON DELETE CASCADE,
                    UNIQUE(habit_id, record_date)
                )
                """
            )
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id INTEGER NOT NULL UNIQUE,
                    target_value REAL NOT NULL CHECK(target_value >= 0),
                    comparison_type TEXT NOT NULL DEFAULT 'gte',
                    FOREIGN KEY(habit_id) REFERENCES habits(id) ON DELETE CASCADE
                )
                """
            )

    def close(self) -> None:
        self.connection.close()

    # 日課項目
    def add_habit(self, name: str, unit: str) -> int:
        with self.connection:
            cursor = self.connection.execute(
                "INSERT INTO habits(name, unit, created_date) VALUES (?, ?, ?)",
                (name, unit, date.today().isoformat()),
            )
            return int(cursor.lastrowid)

    def get_habits(self):
        return self.connection.execute(
            "SELECT id, name, unit, created_date FROM habits ORDER BY name"
        ).fetchall()

    def get_habit(self, habit_id: int):
        return self.connection.execute(
            "SELECT id, name, unit, created_date FROM habits WHERE id = ?",
            (habit_id,),
        ).fetchone()

    def update_habit(self, habit_id: int, name: str, unit: str) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE habits SET name = ?, unit = ? WHERE id = ?",
                (name, unit, habit_id),
            )

    def delete_habit(self, habit_id: int) -> None:
        with self.connection:
            self.connection.execute(
                "DELETE FROM habits WHERE id = ?",
                (habit_id,),
            )

    # 記録
    def add_record(self, habit_id: int, record_date: str, value: float) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO records(habit_id, record_date, value, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    habit_id,
                    record_date,
                    value,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )

    def get_recent_records(self, habit_id: int, limit: int = 30):
        return self.connection.execute(
            """
            SELECT id, record_date, value
            FROM records
            WHERE habit_id = ?
            ORDER BY record_date DESC
            LIMIT ?
            """,
            (habit_id, limit),
        ).fetchall()

    def get_records(self, habit_id: int, start_date: str, end_date: str):
        return self.connection.execute(
            """
            SELECT id, record_date, value
            FROM records
            WHERE habit_id = ?
              AND record_date BETWEEN ? AND ?
            ORDER BY record_date
            """,
            (habit_id, start_date, end_date),
        ).fetchall()

    # 目標
    def set_goal(self, habit_id: int, target_value: float) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO goals(habit_id, target_value, comparison_type)
                VALUES (?, ?, 'gte')
                ON CONFLICT(habit_id)
                DO UPDATE SET target_value = excluded.target_value
                """,
                (habit_id, target_value),
            )

    def get_goal(self, habit_id: int):
        return self.connection.execute(
            """
            SELECT id, target_value, comparison_type
            FROM goals
            WHERE habit_id = ?
            """,
            (habit_id,),
        ).fetchone()


class HabitTrackerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("日課管理アプリ")
        self.geometry("860x560")
        self.minsize(780, 500)

        self.db = Database()
        self.habit_map = {}

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.create_style()
        self.create_widgets()
        self.refresh_habits()

    def create_style(self) -> None:
        style = ttk.Style(self)

        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure(
            "Title.TLabel",
            font=("Yu Gothic UI", 15, "bold"),
        )
        style.configure(
            "Heading.TLabel",
            font=("Yu Gothic UI", 10, "bold"),
        )
        style.configure(
            "TButton",
            padding=(5, 2),
        )
        style.configure(
            "TEntry",
            padding=2,
        )
        style.configure(
            "TCombobox",
            padding=2,
        )
        style.configure(
            "Treeview",
            rowheight=23,
        )
        style.configure(
            "Treeview.Heading",
            font=("Yu Gothic UI", 9, "bold"),
        )
        style.configure(
            "TNotebook.Tab",
            padding=(10, 4),
        )

    def create_widgets(self) -> None:
        ttk.Label(
            self,
            text="日課管理アプリ",
            style="Title.TLabel",
        ).pack(pady=(5, 3))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=(0, 5),
        )
        self.notebook.bind(
            "<<NotebookTabChanged>>",
            self.on_tab_changed,
        )

        self.habit_tab = ttk.Frame(self.notebook)
        self.record_tab = ttk.Frame(self.notebook)
        self.goal_tab = ttk.Frame(self.notebook)
        self.graph_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.habit_tab, text="日課項目")
        self.notebook.add(self.record_tab, text="記録")
        self.notebook.add(self.goal_tab, text="目標")
        self.notebook.add(self.graph_tab, text="グラフ")

        self.create_habit_tab()
        self.create_record_tab()
        self.create_goal_tab()
        self.create_graph_tab()

    # -------------------------
    # 日課項目タブ
    # -------------------------
    def create_habit_tab(self) -> None:
        container = ttk.Frame(self.habit_tab, padding=5)
        container.pack(fill="both", expand=True)

        form = ttk.LabelFrame(
            container,
            text="追加・編集",
            padding=6,
        )
        form.pack(fill="x", pady=(0, 5))

        ttk.Label(form, text="項目名").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 4),
        )

        self.habit_name_var = tk.StringVar()
        ttk.Entry(
            form,
            textvariable=self.habit_name_var,
            width=24,
        ).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(0, 8),
        )

        ttk.Label(form, text="単位").grid(
            row=0,
            column=2,
            sticky="w",
            padx=(0, 4),
        )

        self.habit_unit_var = tk.StringVar()
        ttk.Entry(
            form,
            textvariable=self.habit_unit_var,
            width=14,
        ).grid(
            row=0,
            column=3,
            sticky="ew",
            padx=(0, 8),
        )

        ttk.Button(
            form,
            text="追加",
            command=self.add_habit,
        ).grid(row=0, column=4, padx=2)

        ttk.Button(
            form,
            text="編集",
            command=self.update_habit,
        ).grid(row=0, column=5, padx=2)

        ttk.Button(
            form,
            text="削除",
            command=self.delete_habit,
        ).grid(row=0, column=6, padx=2)

        ttk.Button(
            form,
            text="クリア",
            command=self.clear_habit_form,
        ).grid(row=0, column=7, padx=(2, 0))

        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        ttk.Label(
            container,
            text="登録済みの日課",
            style="Heading.TLabel",
        ).pack(anchor="w", pady=(1, 2))

        self.habit_tree = ttk.Treeview(
            container,
            columns=("name", "unit", "created"),
            show="headings",
            height=12,
        )
        self.habit_tree.heading("name", text="項目名")
        self.habit_tree.heading("unit", text="単位")
        self.habit_tree.heading("created", text="作成日")

        self.habit_tree.column("name", width=300)
        self.habit_tree.column("unit", width=130, anchor="center")
        self.habit_tree.column("created", width=130, anchor="center")

        self.habit_tree.pack(fill="both", expand=True)
        self.habit_tree.bind(
            "<<TreeviewSelect>>",
            self.on_habit_tree_select,
        )

    def validate_habit_input(self):
        name = self.habit_name_var.get().strip()
        unit = self.habit_unit_var.get().strip()

        if not name:
            messagebox.showerror(
                "入力エラー",
                "項目名を入力してください。",
            )
            return None

        if not unit:
            messagebox.showerror(
                "入力エラー",
                "単位を入力してください。",
            )
            return None

        return name, unit

    def add_habit(self) -> None:
        values = self.validate_habit_input()

        if values is None:
            return

        try:
            self.db.add_habit(*values)
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "登録エラー",
                "同じ名前の日課項目が既に存在します。",
            )
            return

        self.clear_habit_form()
        self.refresh_habits()
        messagebox.showinfo(
            "登録完了",
            "日課項目を追加しました。",
        )

    def update_habit(self) -> None:
        selection = self.habit_tree.selection()

        if not selection:
            messagebox.showwarning(
                "選択エラー",
                "編集する項目を選択してください。",
            )
            return

        values = self.validate_habit_input()

        if values is None:
            return

        habit_id = int(selection[0])

        try:
            self.db.update_habit(
                habit_id,
                values[0],
                values[1],
            )
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "更新エラー",
                "同じ名前の日課項目が既に存在します。",
            )
            return

        self.clear_habit_form()
        self.refresh_habits()
        messagebox.showinfo(
            "更新完了",
            "日課項目を編集しました。",
        )

    def delete_habit(self) -> None:
        selection = self.habit_tree.selection()

        if not selection:
            messagebox.showwarning(
                "選択エラー",
                "削除する項目を選択してください。",
            )
            return

        habit_id = int(selection[0])
        habit = self.db.get_habit(habit_id)

        if habit is None:
            return

        confirmed = messagebox.askyesno(
            "削除確認",
            f'「{habit["name"]}」を削除しますか？\n'
            "関連する記録と目標も削除されます。",
        )

        if not confirmed:
            return

        self.db.delete_habit(habit_id)

        self.clear_habit_form()
        self.record_habit_var.set("")
        self.goal_habit_var.set("")
        self.graph_habit_var.set("")

        self.refresh_habits()
        self.clear_record_tree()
        self.clear_graph()

        messagebox.showinfo(
            "削除完了",
            "日課項目を削除しました。",
        )

    def on_habit_tree_select(self, _event=None) -> None:
        selection = self.habit_tree.selection()

        if not selection:
            return

        habit = self.db.get_habit(int(selection[0]))

        if habit:
            self.habit_name_var.set(habit["name"])
            self.habit_unit_var.set(habit["unit"])

    def clear_habit_form(self) -> None:
        self.habit_name_var.set("")
        self.habit_unit_var.set("")

        for item in self.habit_tree.selection():
            self.habit_tree.selection_remove(item)

    # -------------------------
    # 記録タブ
    # -------------------------
    def create_record_tab(self) -> None:
        container = ttk.Frame(self.record_tab, padding=5)
        container.pack(fill="both", expand=True)

        form = ttk.LabelFrame(
            container,
            text="新しい記録",
            padding=6,
        )
        form.pack(fill="x", pady=(0, 4))

        ttk.Label(form, text="日課項目").grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.record_habit_var = tk.StringVar()
        self.record_habit_combo = ttk.Combobox(
            form,
            textvariable=self.record_habit_var,
            state="readonly",
            width=24,
        )
        self.record_habit_combo.grid(
            row=1,
            column=0,
            padx=(0, 8),
            pady=(2, 0),
        )
        self.record_habit_combo.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.refresh_record_list(),
        )

        ttk.Label(form, text="日付").grid(
            row=0,
            column=1,
            sticky="w",
        )

        self.record_date_var = tk.StringVar(
            value=date.today().isoformat()
        )
        ttk.Entry(
            form,
            textvariable=self.record_date_var,
            width=14,
        ).grid(
            row=1,
            column=1,
            padx=(0, 8),
            pady=(2, 0),
        )

        ttk.Label(form, text="数値").grid(
            row=0,
            column=2,
            sticky="w",
        )

        self.record_value_var = tk.StringVar()
        ttk.Entry(
            form,
            textvariable=self.record_value_var,
            width=14,
        ).grid(
            row=1,
            column=2,
            padx=(0, 8),
            pady=(2, 0),
        )

        ttk.Button(
            form,
            text="保存",
            command=self.add_record,
        ).grid(
            row=1,
            column=3,
            padx=2,
            pady=(2, 0),
        )

        self.achievement_label = ttk.Label(
            container,
            text="目標達成状況：未判定",
            style="Heading.TLabel",
        )
        self.achievement_label.pack(
            anchor="w",
            pady=(3, 3),
        )

        ttk.Label(
            container,
            text="最近の記録",
            style="Heading.TLabel",
        ).pack(anchor="w", pady=(0, 2))

        self.record_tree = ttk.Treeview(
            container,
            columns=("date", "value", "result"),
            show="headings",
            height=12,
        )
        self.record_tree.heading("date", text="日付")
        self.record_tree.heading("value", text="記録値")
        self.record_tree.heading("result", text="目標判定")

        self.record_tree.column("date", width=150, anchor="center")
        self.record_tree.column("value", width=180, anchor="center")
        self.record_tree.column("result", width=150, anchor="center")

        self.record_tree.pack(fill="both", expand=True)

    def add_record(self) -> None:
        habit_id = self.get_selected_habit_id(
            self.record_habit_var
        )

        if habit_id is None:
            messagebox.showerror(
                "入力エラー",
                "日課項目を選択してください。",
            )
            return

        record_date_text = self.record_date_var.get().strip()

        try:
            datetime.strptime(
                record_date_text,
                "%Y-%m-%d",
            )
        except ValueError:
            messagebox.showerror(
                "入力エラー",
                "日付は YYYY-MM-DD 形式で入力してください。",
            )
            return

        try:
            value = float(self.record_value_var.get())

            if value < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "入力エラー",
                "数値には0以上の値を入力してください。",
            )
            return

        try:
            self.db.add_record(
                habit_id,
                record_date_text,
                value,
            )
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "登録エラー",
                "同じ日課項目の同じ日付には、既に記録が存在します。\n"
                "記録の編集機能は設けていないため、別の日付で登録してください。",
            )
            return

        goal = self.db.get_goal(habit_id)

        if goal is None:
            result_text = "目標未設定"
        elif value >= goal["target_value"]:
            result_text = "達成"
        else:
            result_text = "未達成"

        self.achievement_label.config(
            text=f"目標達成状況：{result_text}"
        )
        self.record_value_var.set("")

        self.refresh_record_list()
        self.refresh_graph()

        messagebox.showinfo(
            "保存完了",
            "記録を保存しました。",
        )

    def refresh_record_list(self) -> None:
        self.clear_record_tree()

        habit_id = self.get_selected_habit_id(
            self.record_habit_var
        )

        if habit_id is None:
            return

        habit = self.db.get_habit(habit_id)
        goal = self.db.get_goal(habit_id)

        for record in self.db.get_recent_records(habit_id):
            if goal is None:
                result = "目標未設定"
            elif record["value"] >= goal["target_value"]:
                result = "達成"
            else:
                result = "未達成"

            self.record_tree.insert(
                "",
                "end",
                values=(
                    record["record_date"],
                    f'{record["value"]:g} {habit["unit"]}',
                    result,
                ),
            )

    def clear_record_tree(self) -> None:
        for item in self.record_tree.get_children():
            self.record_tree.delete(item)

    # -------------------------
    # 目標タブ
    # -------------------------
    def create_goal_tab(self) -> None:
        container = ttk.Frame(self.goal_tab, padding=8)
        container.pack(fill="both", expand=True)

        form = ttk.LabelFrame(
            container,
            text="目標設定",
            padding=8,
        )
        form.pack(fill="x")

        ttk.Label(form, text="日課項目").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 6),
            pady=3,
        )

        self.goal_habit_var = tk.StringVar()
        self.goal_habit_combo = ttk.Combobox(
            form,
            textvariable=self.goal_habit_var,
            state="readonly",
            width=28,
        )
        self.goal_habit_combo.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(0, 10),
            pady=3,
        )
        self.goal_habit_combo.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.load_goal(),
        )

        ttk.Label(form, text="目標値").grid(
            row=0,
            column=2,
            sticky="w",
            padx=(0, 6),
            pady=3,
        )

        self.goal_value_var = tk.StringVar()
        ttk.Entry(
            form,
            textvariable=self.goal_value_var,
            width=16,
        ).grid(
            row=0,
            column=3,
            sticky="w",
            padx=(0, 8),
            pady=3,
        )

        ttk.Button(
            form,
            text="保存・上書き",
            command=self.set_goal,
        ).grid(
            row=0,
            column=4,
            padx=2,
            pady=3,
        )

        self.goal_status_label = ttk.Label(
            container,
            text="現在の目標：未設定",
            style="Heading.TLabel",
        )
        self.goal_status_label.pack(
            anchor="w",
            pady=(8, 3),
        )

        ttk.Label(
            container,
            text=(
                "同じ日課項目に新しい目標値を入力して保存すると、"
                "以前の目標が上書きされます。"
            ),
            wraplength=720,
        ).pack(anchor="w")

    def load_goal(self) -> None:
        habit_id = self.get_selected_habit_id(
            self.goal_habit_var
        )

        if habit_id is None:
            self.goal_value_var.set("")
            self.goal_status_label.config(
                text="現在の目標：未設定"
            )
            return

        habit = self.db.get_habit(habit_id)
        goal = self.db.get_goal(habit_id)

        if goal is None:
            self.goal_value_var.set("")
            self.goal_status_label.config(
                text="現在の目標：未設定"
            )
        else:
            self.goal_value_var.set(
                f'{goal["target_value"]:g}'
            )
            self.goal_status_label.config(
                text=(
                    f'現在の目標：'
                    f'{goal["target_value"]:g} '
                    f'{habit["unit"]} 以上'
                )
            )

    def set_goal(self) -> None:
        habit_id = self.get_selected_habit_id(
            self.goal_habit_var
        )

        if habit_id is None:
            messagebox.showerror(
                "入力エラー",
                "日課項目を選択してください。",
            )
            return

        try:
            target = float(self.goal_value_var.get())

            if target < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "入力エラー",
                "目標値には0以上の数値を入力してください。",
            )
            return

        self.db.set_goal(
            habit_id,
            target,
        )
        self.load_goal()
        self.refresh_record_list()

        messagebox.showinfo(
            "保存完了",
            "目標を保存しました。",
        )

    # -------------------------
    # グラフタブ
    # -------------------------
    def create_graph_tab(self) -> None:
        container = ttk.Frame(self.graph_tab, padding=5)
        container.pack(fill="both", expand=True)

        controls = ttk.LabelFrame(
            container,
            text="表示条件",
            padding=5,
        )
        controls.pack(fill="x", pady=(0, 4))

        ttk.Label(controls, text="日課項目").grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.graph_habit_var = tk.StringVar()
        self.graph_habit_combo = ttk.Combobox(
            controls,
            textvariable=self.graph_habit_var,
            state="readonly",
            width=22,
        )
        self.graph_habit_combo.grid(
            row=1,
            column=0,
            padx=(0, 8),
            pady=(2, 0),
        )
        self.graph_habit_combo.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.refresh_graph(),
        )

        today = date.today()
        start = today - timedelta(days=29)

        ttk.Label(controls, text="開始日").grid(
            row=0,
            column=1,
            sticky="w",
        )

        self.graph_start_var = tk.StringVar(
            value=start.isoformat()
        )
        ttk.Entry(
            controls,
            textvariable=self.graph_start_var,
            width=13,
        ).grid(
            row=1,
            column=1,
            padx=(0, 8),
            pady=(2, 0),
        )

        ttk.Label(controls, text="終了日").grid(
            row=0,
            column=2,
            sticky="w",
        )

        self.graph_end_var = tk.StringVar(
            value=today.isoformat()
        )
        ttk.Entry(
            controls,
            textvariable=self.graph_end_var,
            width=13,
        ).grid(
            row=1,
            column=2,
            padx=(0, 8),
            pady=(2, 0),
        )

        ttk.Button(
            controls,
            text="期間を適用",
            command=self.refresh_graph,
        ).grid(
            row=1,
            column=3,
            padx=2,
            pady=(2, 0),
        )

        ttk.Label(
            controls,
            text="期間を適用すると、最新データで自動再描画します。",
        ).grid(
            row=2,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(4, 0),
        )

        self.figure = Figure(
            figsize=(6.2, 3.4),
            dpi=100,
        )
        self.axis = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(
            self.figure,
            master=container,
        )
        self.canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
        )

    def refresh_graph(self) -> None:
        habit_id = self.get_selected_habit_id(
            self.graph_habit_var
        )

        self.axis.clear()

        if habit_id is None:
            self.axis.set_title(
                "日課項目を選択してください"
            )
            self.canvas.draw()
            return

        start_text = self.graph_start_var.get().strip()
        end_text = self.graph_end_var.get().strip()

        try:
            start_date = datetime.strptime(
                start_text,
                "%Y-%m-%d",
            ).date()
            end_date = datetime.strptime(
                end_text,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            messagebox.showerror(
                "期間エラー",
                "開始日と終了日は YYYY-MM-DD 形式で入力してください。",
            )
            return

        if start_date > end_date:
            messagebox.showerror(
                "期間エラー",
                "開始日は終了日以前にしてください。",
            )
            return

        habit = self.db.get_habit(habit_id)
        records = self.db.get_records(
            habit_id,
            start_text,
            end_text,
        )
        goal = self.db.get_goal(habit_id)

        dates = [
            datetime.strptime(
                record["record_date"],
                "%Y-%m-%d",
            )
            for record in records
        ]
        values = [
            record["value"]
            for record in records
        ]

        self.axis.set_title(
            f'{habit["name"]}の記録',
            fontsize=11,
        )
        self.axis.set_xlabel(
            "日付",
            fontsize=9,
        )
        self.axis.set_ylabel(
            habit["unit"],
            fontsize=9,
        )
        self.axis.tick_params(
            axis="both",
            labelsize=8,
        )
        self.axis.grid(
            True,
            alpha=0.3,
        )

        if records:
            self.axis.plot(
                dates,
                values,
                marker="o",
                label="記録値",
            )

            if goal is not None:
                self.axis.axhline(
                    y=goal["target_value"],
                    linestyle="--",
                    label=(
                        f'目標 '
                        f'{goal["target_value"]:g} '
                        f'{habit["unit"]}'
                    ),
                )

            self.axis.legend(fontsize=8)
            self.figure.autofmt_xdate()
        else:
            self.axis.text(
                0.5,
                0.5,
                "指定期間の記録がありません",
                ha="center",
                va="center",
                transform=self.axis.transAxes,
            )

        self.figure.tight_layout(pad=1.0)
        self.canvas.draw()

    def clear_graph(self) -> None:
        self.axis.clear()
        self.axis.set_title(
            "日課項目を選択してください"
        )
        self.canvas.draw()

    # -------------------------
    # 共通処理
    # -------------------------
    def refresh_habits(self) -> None:
        for item in self.habit_tree.get_children():
            self.habit_tree.delete(item)

        habits = self.db.get_habits()

        for habit in habits:
            self.habit_tree.insert(
                "",
                "end",
                iid=str(habit["id"]),
                values=(
                    habit["name"],
                    habit["unit"],
                    habit["created_date"],
                ),
            )

        display_values = [
            f'{habit["name"]}（{habit["unit"]}）'
            for habit in habits
        ]

        self.record_habit_combo["values"] = display_values
        self.goal_habit_combo["values"] = display_values
        self.graph_habit_combo["values"] = display_values

        self.habit_map = {
            f'{habit["name"]}（{habit["unit"]}）': habit["id"]
            for habit in habits
        }

        if habits:
            first = display_values[0]

            if self.record_habit_var.get() not in self.habit_map:
                self.record_habit_var.set(first)

            if self.goal_habit_var.get() not in self.habit_map:
                self.goal_habit_var.set(first)

            if self.graph_habit_var.get() not in self.habit_map:
                self.graph_habit_var.set(first)

            self.refresh_record_list()
            self.load_goal()
            self.refresh_graph()
        else:
            self.record_habit_var.set("")
            self.goal_habit_var.set("")
            self.graph_habit_var.set("")

            self.clear_record_tree()
            self.clear_graph()

            self.goal_value_var.set("")
            self.goal_status_label.config(
                text="現在の目標：未設定"
            )

    def get_selected_habit_id(
        self,
        variable: tk.StringVar,
    ):
        return self.habit_map.get(variable.get())

    def on_tab_changed(self, _event=None) -> None:
        selected_tab = self.notebook.index(
            self.notebook.select()
        )

        if selected_tab == 1:
            self.refresh_record_list()
        elif selected_tab == 2:
            self.load_goal()
        elif selected_tab == 3:
            self.refresh_graph()

    def on_close(self) -> None:
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = HabitTrackerApp()
    app.mainloop()