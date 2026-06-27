"""
IT Operations Support Dashboard

A complete portfolio-ready Python desktop project for PyCharm.

This version uses only Python standard library modules:
- tkinter for the desktop interface
- sqlite3 for the local database
- csv for report export

How to run:
1. Open this file in PyCharm.
2. Press Run.
3. The database will be created automatically.

Project purpose:
This simulates a small IT support operations system where a team can log support
requests, track IT assets, export reports and keep an audit log.
"""

import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from tkinter import Tk, StringVar, Text, END, BOTH, LEFT, RIGHT, X, Y, W, E, N, S
from tkinter import ttk, messagebox, filedialog

DB_PATH = Path("it_operations_dashboard.db")


class Database:
    """Handles all database setup and actions."""

    def __init__(self, path: Path):
        self.path = path
        self.initialise()

    def connect(self):
        return sqlite3.connect(self.path)

    def initialise(self):
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    requester TEXT NOT NULL,
                    location TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    description TEXT NOT NULL,
                    resolution_notes TEXT
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_tag TEXT NOT NULL UNIQUE,
                    asset_type TEXT NOT NULL,
                    assigned_to TEXT,
                    location TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    notes TEXT
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_time TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_details TEXT NOT NULL
                )
                """
            )

            conn.commit()

    def add_audit_event(self, event_type: str, event_details: str):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_log (event_time, event_type, event_details)
                VALUES (?, ?, ?)
                """,
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), event_type, event_details),
            )
            conn.commit()

    def add_ticket(self, requester, location, category, priority, status, description, resolution_notes):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tickets (
                    created_at, requester, location, category, priority,
                    status, description, resolution_notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    requester,
                    location,
                    category,
                    priority,
                    status,
                    description,
                    resolution_notes,
                ),
            )
            conn.commit()

        self.add_audit_event(
            "Ticket Created",
            f"Ticket created for {requester} at {location}. Priority: {priority}. Status: {status}.",
        )

    def add_asset(self, asset_tag, asset_type, assigned_to, location, condition, notes):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO assets (asset_tag, asset_type, assigned_to, location, condition, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (asset_tag, asset_type, assigned_to, location, condition, notes),
            )
            conn.commit()

        self.add_audit_event(
            "Asset Added",
            f"Asset {asset_tag} added. Type: {asset_type}. Condition: {condition}.",
        )

    def fetch_all(self, table_name: str):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC")
            return cursor.fetchall()

    def fetch_columns(self, table_name: str):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [row[1] for row in cursor.fetchall()]

    def count_where(self, table_name: str, where_clause: str = "", parameters=()):
        with self.connect() as conn:
            cursor = conn.cursor()
            query = f"SELECT COUNT(*) FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            cursor.execute(query, parameters)
            return cursor.fetchone()[0]

    def load_sample_data(self):
        ticket_count = self.count_where("tickets")
        asset_count = self.count_where("assets")

        if ticket_count == 0:
            self.add_ticket(
                "Reception",
                "Main Office",
                "Hardware",
                "High",
                "Open",
                "Front desk monitor intermittently loses signal during use.",
                "",
            )
            self.add_ticket(
                "Student Services",
                "Room 204",
                "Software",
                "Medium",
                "In Progress",
                "Application freezes when exporting reports.",
                "Initial troubleshooting completed. Awaiting further testing.",
            )
            self.add_ticket(
                "Finance",
                "Admin Block",
                "Account Access",
                "Urgent",
                "Resolved",
                "User locked out before payroll deadline.",
                "Password reset completed and access confirmed.",
            )

        if asset_count == 0:
            self.add_asset(
                "LAP-001",
                "Laptop",
                "Reception",
                "Main Office",
                "Good",
                "Standard office laptop used for front desk duties.",
            )
            self.add_asset(
                "MON-014",
                "Monitor",
                "Front Desk",
                "Main Office",
                "Needs Attention",
                "Signal issue reported. Linked to support ticket evidence.",
            )
            self.add_asset(
                "PRN-003",
                "Printer",
                "Shared",
                "Admin Block",
                "Good",
                "Network printer used by Finance and HR.",
            )

        self.add_audit_event("Sample Data", "Sample ticket and asset records loaded for demonstration.")

    def export_table_to_csv(self, table_name: str, file_path: str):
        columns = self.fetch_columns(table_name)
        rows = self.fetch_all(table_name)

        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(rows)

        self.add_audit_event("CSV Export", f"Exported {table_name} records to {file_path}.")


class ITDashboardApp:
    """Main desktop application."""

    def __init__(self, root: Tk):
        self.root = root
        self.db = Database(DB_PATH)

        self.root.title("IT Operations Support Dashboard")
        self.root.geometry("1200x720")
        self.root.minsize(1000, 620)

        self.setup_style()
        self.build_layout()
        self.show_dashboard()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Arial", 20, "bold"))
        style.configure("Heading.TLabel", font=("Arial", 14, "bold"))
        style.configure("Metric.TLabel", font=("Arial", 12, "bold"), padding=10)
        style.configure("Nav.TButton", padding=8)
        style.configure("Action.TButton", padding=6)

    def build_layout(self):
        self.header = ttk.Frame(self.root, padding=12)
        self.header.pack(fill=X)

        title = ttk.Label(self.header, text="IT Operations Support Dashboard", style="Title.TLabel")
        title.pack(anchor=W)

        subtitle = ttk.Label(
            self.header,
            text="Portfolio-ready Python project for IT support, asset tracking, audit logging and operational reporting.",
        )
        subtitle.pack(anchor=W)

        self.main = ttk.Frame(self.root)
        self.main.pack(fill=BOTH, expand=True)

        self.nav = ttk.Frame(self.main, width=220, padding=10)
        self.nav.pack(side=LEFT, fill=Y)

        self.content = ttk.Frame(self.main, padding=12)
        self.content.pack(side=RIGHT, fill=BOTH, expand=True)

        ttk.Button(self.nav, text="Dashboard", style="Nav.TButton", command=self.show_dashboard).pack(fill=X, pady=3)
        ttk.Button(self.nav, text="Create Ticket", style="Nav.TButton", command=self.show_create_ticket).pack(fill=X, pady=3)
        ttk.Button(self.nav, text="Asset Register", style="Nav.TButton", command=self.show_asset_register).pack(fill=X, pady=3)
        ttk.Button(self.nav, text="Reports / Export", style="Nav.TButton", command=self.show_reports).pack(fill=X, pady=3)
        ttk.Button(self.nav, text="Audit Log", style="Nav.TButton", command=self.show_audit_log).pack(fill=X, pady=3)
        ttk.Button(self.nav, text="Portfolio / LinkedIn", style="Nav.TButton", command=self.show_portfolio).pack(fill=X, pady=3)
        ttk.Button(self.nav, text="About Project", style="Nav.TButton", command=self.show_about).pack(fill=X, pady=3)

        ttk.Separator(self.nav).pack(fill=X, pady=14)
        ttk.Button(self.nav, text="Load Sample Data", style="Action.TButton", command=self.load_sample_data).pack(fill=X, pady=3)
        ttk.Button(self.nav, text="Refresh", style="Action.TButton", command=self.show_dashboard).pack(fill=X, pady=3)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def add_page_heading(self, text):
        ttk.Label(self.content, text=text, style="Heading.TLabel").pack(anchor=W, pady=(0, 10))

    def make_table(self, parent, columns, rows):
        frame = ttk.Frame(parent)
        frame.pack(fill=BOTH, expand=True)

        tree = ttk.Treeview(frame, columns=columns, show="headings")
        y_scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        for column in columns:
            tree.heading(column, text=column.replace("_", " ").title())
            tree.column(column, width=140, anchor=W)

        for row in rows:
            tree.insert("", END, values=row)

        tree.grid(row=0, column=0, sticky=N + S + E + W)
        y_scroll.grid(row=0, column=1, sticky=N + S)
        x_scroll.grid(row=1, column=0, sticky=E + W)

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        return tree

    def show_dashboard(self):
        self.clear_content()
        self.add_page_heading("Operations Overview")

        total_tickets = self.db.count_where("tickets")
        open_tickets = self.db.count_where("tickets", "status IN (?, ?)", ("Open", "In Progress"))
        urgent_tickets = self.db.count_where("tickets", "priority IN (?, ?)", ("High", "Urgent"))
        resolved_tickets = self.db.count_where("tickets", "status IN (?, ?)", ("Resolved", "Closed"))
        assets_attention = self.db.count_where("assets", "condition = ?", ("Needs Attention",))

        metrics = ttk.Frame(self.content)
        metrics.pack(fill=X, pady=(0, 14))

        metric_values = [
            ("Total Tickets", total_tickets),
            ("Open / In Progress", open_tickets),
            ("High / Urgent", urgent_tickets),
            ("Resolved / Closed", resolved_tickets),
            ("Assets Needing Attention", assets_attention),
        ]

        for index, (label, value) in enumerate(metric_values):
            box = ttk.LabelFrame(metrics, text=label, padding=10)
            box.grid(row=0, column=index, padx=5, sticky=E + W)
            ttk.Label(box, text=str(value), style="Metric.TLabel").pack()
            metrics.columnconfigure(index, weight=1)

        ttk.Label(self.content, text="Latest Support Tickets", style="Heading.TLabel").pack(anchor=W, pady=(8, 8))
        self.make_table(self.content, self.db.fetch_columns("tickets"), self.db.fetch_all("tickets"))

    def show_create_ticket(self):
        self.clear_content()
        self.add_page_heading("Create Support Ticket")

        form = ttk.Frame(self.content)
        form.pack(fill=X, anchor=N)

        requester = StringVar()
        location = StringVar()
        category = StringVar(value="Hardware")
        priority = StringVar(value="Medium")
        status = StringVar(value="Open")

        self.add_labeled_entry(form, "Requester / Department", requester, 0)
        self.add_labeled_entry(form, "Location", location, 1)
        self.add_labeled_combo(form, "Category", category, ["Hardware", "Software", "Network", "Account Access", "Printer", "Other"], 2)
        self.add_labeled_combo(form, "Priority", priority, ["Low", "Medium", "High", "Urgent"], 3)
        self.add_labeled_combo(form, "Status", status, ["Open", "In Progress", "Resolved", "Closed"], 4)

        ttk.Label(form, text="Issue Description").grid(row=5, column=0, sticky=W, pady=5)
        description_text = Text(form, height=5, width=80)
        description_text.grid(row=5, column=1, sticky=E + W, pady=5)

        ttk.Label(form, text="Resolution Notes").grid(row=6, column=0, sticky=W, pady=5)
        resolution_text = Text(form, height=4, width=80)
        resolution_text.grid(row=6, column=1, sticky=E + W, pady=5)

        form.columnconfigure(1, weight=1)

        def save_ticket():
            description = description_text.get("1.0", END).strip()
            resolution = resolution_text.get("1.0", END).strip()

            if not requester.get().strip() or not location.get().strip() or not description:
                messagebox.showerror("Missing information", "Requester, location and issue description are required.")
                return

            self.db.add_ticket(
                requester.get().strip(),
                location.get().strip(),
                category.get(),
                priority.get(),
                status.get(),
                description,
                resolution,
            )
            messagebox.showinfo("Saved", "Support ticket created successfully.")
            self.show_dashboard()

        ttk.Button(form, text="Create Ticket", style="Action.TButton", command=save_ticket).grid(row=7, column=1, sticky=E, pady=12)

    def show_asset_register(self):
        self.clear_content()
        self.add_page_heading("IT Asset Register")

        form = ttk.LabelFrame(self.content, text="Add New Asset", padding=10)
        form.pack(fill=X, pady=(0, 12))

        asset_tag = StringVar()
        asset_type = StringVar(value="Laptop")
        assigned_to = StringVar()
        location = StringVar()
        condition = StringVar(value="Good")
        notes = StringVar()

        self.add_labeled_entry(form, "Asset Tag", asset_tag, 0)
        self.add_labeled_combo(form, "Asset Type", asset_type, ["Laptop", "Desktop", "Monitor", "Printer", "Phone", "Tablet", "Other"], 1)
        self.add_labeled_entry(form, "Assigned To", assigned_to, 2)
        self.add_labeled_entry(form, "Location", location, 3)
        self.add_labeled_combo(form, "Condition", condition, ["Good", "Fair", "Needs Attention", "Retired"], 4)
        self.add_labeled_entry(form, "Notes", notes, 5)

        form.columnconfigure(1, weight=1)

        def save_asset():
            if not asset_tag.get().strip() or not location.get().strip():
                messagebox.showerror("Missing information", "Asset tag and location are required.")
                return

            try:
                self.db.add_asset(
                    asset_tag.get().strip(),
                    asset_type.get(),
                    assigned_to.get().strip(),
                    location.get().strip(),
                    condition.get(),
                    notes.get().strip(),
                )
                messagebox.showinfo("Saved", "Asset added successfully.")
                self.show_asset_register()
            except sqlite3.IntegrityError:
                messagebox.showerror("Duplicate asset", "That asset tag already exists. Use a unique asset tag.")

        ttk.Button(form, text="Add Asset", style="Action.TButton", command=save_asset).grid(row=6, column=1, sticky=E, pady=10)

        ttk.Label(self.content, text="Current Assets", style="Heading.TLabel").pack(anchor=W, pady=(8, 8))
        self.make_table(self.content, self.db.fetch_columns("assets"), self.db.fetch_all("assets"))

    def show_reports(self):
        self.clear_content()
        self.add_page_heading("Reports / Export")

        ttk.Label(
            self.content,
            text="Export support ticket and asset records to CSV for evidence, reporting or portfolio screenshots.",
        ).pack(anchor=W, pady=(0, 12))

        buttons = ttk.Frame(self.content)
        buttons.pack(fill=X, pady=(0, 12))

        ttk.Button(buttons, text="Export Tickets CSV", command=lambda: self.export_csv("tickets")).pack(side=LEFT, padx=5)
        ttk.Button(buttons, text="Export Assets CSV", command=lambda: self.export_csv("assets")).pack(side=LEFT, padx=5)
        ttk.Button(buttons, text="Export Audit Log CSV", command=lambda: self.export_csv("audit_log")).pack(side=LEFT, padx=5)

        ttk.Label(self.content, text="Ticket Records", style="Heading.TLabel").pack(anchor=W, pady=(8, 8))
        self.make_table(self.content, self.db.fetch_columns("tickets"), self.db.fetch_all("tickets"))

    def show_audit_log(self):
        self.clear_content()
        self.add_page_heading("Audit Log")
        ttk.Label(self.content, text="A simple evidence trail of actions completed in the system.").pack(anchor=W, pady=(0, 12))
        self.make_table(self.content, self.db.fetch_columns("audit_log"), self.db.fetch_all("audit_log"))

    def show_portfolio(self):
        self.clear_content()
        self.add_page_heading("Portfolio / LinkedIn Showcase")

        text = Text(self.content, wrap="word", height=28)
        text.pack(fill=BOTH, expand=True)

        content = """
PROJECT HEADLINE
IT Operations Support Dashboard — Python, SQLite and Tkinter

SHORT PORTFOLIO SUMMARY
A Python-based desktop dashboard that simulates how IT support teams record, prioritise and review support tickets and IT assets. The project includes ticket logging, asset tracking, dashboard statistics, CSV reporting and local SQLite database storage.

LINKEDIN PROJECT DESCRIPTION
I built an IT Operations Support Dashboard in Python to demonstrate practical skills relevant to IT support, technical support and digital operations.

The project simulates how a support team could record and manage technical support requests, track IT assets, prioritise issues and export records for reporting.

It uses Python, Tkinter and SQLite, and includes support ticket logging, priority/status tracking, an asset register, dashboard statistics, audit logging and CSV export.

SKILLS DEMONSTRATED
- Python programming
- SQLite databases
- Tkinter desktop app development
- Data handling and reporting
- IT support workflows
- Asset tracking
- Audit logging
- Documentation and testing
- Operational thinking

INTERVIEW EXPLANATION
I wanted to build something that connected programming with a real workplace process. Instead of making a basic calculator or game, I built a small IT operations dashboard that reflects how support teams manage requests, assets and reporting. It helped me practise Python, databases, interface design, testing and thinking about accuracy in operational records.

SCREENSHOT CHECKLIST
1. Dashboard metrics
2. Ticket creation form
3. Support ticket table with sample data
4. Asset register
5. Reports / CSV export page
6. Audit log
7. Portfolio / LinkedIn page

WHAT NOT TO OVERCLAIM
Do not call this an enterprise ITSM system. The accurate wording is: portfolio project, simulated support workflow, entry-level IT operations dashboard, and built to demonstrate practical skills.
        """.strip()

        text.insert("1.0", content)
        text.configure(state="disabled")

    def show_about(self):
        self.clear_content()
        self.add_page_heading("About Project")

        text = Text(self.content, wrap="word", height=28)
        text.pack(fill=BOTH, expand=True)

        content = """
ABOUT THIS PROJECT

This project was designed as a portfolio piece for entry-level IT support, technical support, IT operations and digital operations roles.

It demonstrates the ability to:
- build a working Python application
- store and retrieve structured data
- design a simple operational workflow
- manage support tickets
- track IT assets
- produce reports
- maintain an audit trail
- document a project professionally

WHY THIS IS STRONGER THAN A BASIC CODING EXERCISE

A basic calculator or game can show coding practice, but this project links Python to a realistic workplace process. It shows awareness of support records, priorities, evidence, assets, reporting and operational accuracy.

FUTURE IMPROVEMENTS

- Add ticket editing
- Add technician assignment
- Add login roles
- Add charts for ticket trends
- Add PDF report generation
- Add email notifications
- Add advanced search and filtering
        """.strip()

        text.insert("1.0", content)
        text.configure(state="disabled")

    def add_labeled_entry(self, parent, label, variable, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=W, pady=5, padx=(0, 10))
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky=E + W, pady=5)

    def add_labeled_combo(self, parent, label, variable, values, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=W, pady=5, padx=(0, 10))
        combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly")
        combo.grid(row=row, column=1, sticky=E + W, pady=5)

    def load_sample_data(self):
        self.db.load_sample_data()
        messagebox.showinfo("Sample data", "Sample data has been loaded.")
        self.show_dashboard()

    def export_csv(self, table_name):
        file_path = filedialog.asksaveasfilename(
            title=f"Export {table_name} to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{table_name}.csv",
        )

        if not file_path:
            return

        self.db.export_table_to_csv(table_name, file_path)
        messagebox.showinfo("Export complete", f"{table_name} exported successfully.")


def main():
    root = Tk()
    ITDashboardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
