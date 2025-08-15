import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import csv

class BMICalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced BMI Calculator")
        self.root.geometry("1000x700")

     
        self.setup_database()
        self.setup_styles()
        self.create_main_ui()

       
        self.user_map = {} 
        self.user_list = []
        self.current_user = None
        self.load_users()
        if self.user_list:
            self.current_user = self.user_list[0]
            self.user_combobox.current(0)
            self.load_user_data()

    def setup_styles(self):
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10), padding=5)
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Result.TLabel', font=('Arial', 16))

    def setup_database(self):
        self.conn = sqlite3.connect('bmi_data.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                email TEXT,
                birth_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                weight REAL,
                height REAL,
                bmi REAL,
                date TEXT DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        self.conn.commit()

    def create_main_ui(self):
       
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)

       
        input_frame = ttk.LabelFrame(main_frame, text="Input Data", padding=10)
        input_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        for i in range(3):
            input_frame.columnconfigure(i, weight=1)

       
        result_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        result_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        result_frame.rowconfigure(3, weight=1) 
      
        self.user_var = tk.StringVar()
        ttk.Label(input_frame, text="Select User:").grid(row=0, column=0, sticky="w", pady=(0,5))
        self.user_combobox = ttk.Combobox(input_frame, textvariable=self.user_var, state="readonly")
        self.user_combobox.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0,10))
        self.user_combobox.bind("<<ComboboxSelected>>", self.on_user_change)

        ttk.Button(input_frame, text="New User", command=self.add_new_user)\
            .grid(row=1, column=2, padx=(5,0), sticky="e")

        
        ttk.Label(input_frame, text="Weight (kg):").grid(row=2, column=0, sticky="w")
        self.weight_entry = ttk.Entry(input_frame)
        self.weight_entry.grid(row=3, column=0, sticky="ew", pady=(0,10))

        ttk.Label(input_frame, text="Height (m):").grid(row=2, column=1, sticky="w")
        self.height_entry = ttk.Entry(input_frame)
        self.height_entry.grid(row=3, column=1, sticky="ew", pady=(0,10))

        ttk.Label(input_frame, text="Notes:").grid(row=4, column=0, sticky="w", columnspan=3)
        self.notes_entry = tk.Text(input_frame, height=4, width=30)
        self.notes_entry.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=(0,10))

      
        ttk.Button(input_frame, text="Calculate BMI", command=self.calculate_bmi)\
            .grid(row=6, column=0, pady=10, sticky="ew")
        ttk.Button(input_frame, text="Clear", command=self.clear_fields)\
            .grid(row=6, column=1, pady=10, sticky="ew")

       
        self.result_label = ttk.Label(result_frame, text="BMI: --", style="Result.TLabel")
        self.result_label.grid(row=0, column=0, sticky="w", pady=(0,10))

       
        self.category_label = tk.Label(result_frame, text="Category: --", font=('Arial', 16))
        self.category_label.grid(row=1, column=0, sticky="w", pady=(0,10))

       
        self.figure_frame = ttk.Frame(result_frame)
        self.figure_frame.grid(row=2, column=0, sticky="nsew", pady=(0,10))
        result_frame.rowconfigure(2, weight=1)

       
        ttk.Label(result_frame, text="Measurement History").grid(row=3, column=0, sticky="w")
        self.history_tree = ttk.Treeview(
            result_frame,
            columns=("date", "weight", "height", "bmi", "category"),
            show="headings", height=10
        )
        self.history_tree.grid(row=4, column=0, sticky="nsew")
        result_frame.rowconfigure(4, weight=1)

        self.history_tree.heading("date", text="Date")
        self.history_tree.heading("weight", text="Weight (kg)")
        self.history_tree.heading("height", text="Height (m)")
        self.history_tree.heading("bmi", text="BMI")
        self.history_tree.heading("category", text="Category")

        self.history_tree.column("date", width=160, anchor="w")
        self.history_tree.column("weight", width=100, anchor="center")
        self.history_tree.column("height", width=100, anchor="center")
        self.history_tree.column("bmi", width=80, anchor="center")
        self.history_tree.column("category", width=120, anchor="center")

       
        ttk.Button(result_frame, text="Export History", command=self.export_history)\
            .grid(row=5, column=0, pady=10, sticky="e")

    def load_users(self):
        self.cursor.execute("SELECT id, name FROM users ORDER BY name COLLATE NOCASE")
        users = self.cursor.fetchall()
        self.user_list = users
        self.user_map = {name: (uid, name) for uid, name in users}
        names = [u[1] for u in users]
        self.user_combobox['values'] = names
      
        if self.current_user:
            name = self.current_user[1]
            if name in names:
                self.user_combobox.set(name)

    def on_user_change(self, event=None):
        name = self.user_var.get()
        if name in self.user_map:
            self.current_user = self.user_map[name]
            self.load_user_data()

    def load_user_data(self):
        if not self.current_user:
            return

       
        for widget in self.figure_frame.winfo_children():
            widget.destroy()

       
        self.cursor.execute('''
            SELECT id, weight, height, bmi, date, notes
            FROM measurements
            WHERE user_id = ?
            ORDER BY date DESC
        ''', (self.current_user[0],))
        measurements = self.cursor.fetchall()

       
        self.history_tree.delete(*self.history_tree.get_children())
        for measure in measurements:
            bmi_val = measure[3]
            category, _ = self.classify_bmi(bmi_val)
            self.history_tree.insert(
                "",
                "end",
                values=(measure[4], measure[1], measure[2], f"{bmi_val:.1f}", category)
            )

      
        if len(measurements) >= 2:
            self.create_trend_chart(measurements[::-1])  

    def create_trend_chart(self, measurements):
        
        dates = []
        bmis = []
        for m in measurements:
            date_str = m[4]
           
            try:
                dt = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
              
                try:
                    dt = datetime.datetime.fromisoformat(date_str)
                except ValueError:
                  
                    continue
            dates.append(dt)
            bmis.append(m[3])

        if len(dates) < 2:
            return

        
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(dates, bmis, marker='o')
        ax.set_title('BMI Trend Over Time')
        ax.set_ylabel('BMI')
        ax.grid(True)
        fig.autofmt_xdate()

      
        canvas = FigureCanvasTkAgg(fig, master=self.figure_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

      
        plt.close(fig)

    def classify_bmi(self, bmi):
        if bmi < 18.5:
            return "Underweight", "#3498db" 
        elif 18.5 <= bmi < 25:
            return "Normal", "#2ecc71"     
        elif 25 <= bmi < 30:
            return "Overweight", "#f39c12" 
        else:
            return "Obese", "#e74c3c"     

    def calculate_bmi(self):
        try:
            weight = float(self.weight_entry.get())
            height = float(self.height_entry.get())
            if weight <= 0 or height <= 0:
                raise ValueError("Values must be positive")

            bmi = weight / (height ** 2)
            category, color = self.classify_bmi(bmi)

          
            self.result_label.config(text=f"BMI: {bmi:.1f}")
            self.category_label.config(text=f"Category: {category}", fg=color)

          
            notes = self.notes_entry.get("1.0", tk.END).strip()
            if self.current_user:
                self.cursor.execute('''
                    INSERT INTO measurements (user_id, weight, height, bmi, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.current_user[0], weight, height, bmi, notes))
                self.conn.commit()
                self.load_user_data()

        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def clear_fields(self):
        self.weight_entry.delete(0, tk.END)
        self.height_entry.delete(0, tk.END)
        self.notes_entry.delete("1.0", tk.END)
        self.result_label.config(text="BMI: --")
        self.category_label.config(text="Category: --", fg="black")

    def add_new_user(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New User")
        dialog.grab_set()

        ttk.Label(dialog, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        name_entry = ttk.Entry(dialog)
        name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(dialog, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        email_entry = ttk.Entry(dialog)
        email_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(dialog, text="Birth Date (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        birth_entry = ttk.Entry(dialog)
        birth_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        dialog.columnconfigure(1, weight=1)

        def save_user():
            name = name_entry.get().strip()
            email = email_entry.get().strip()
            birth_date = birth_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Name is required")
                return
            try:
                self.cursor.execute('''
                    INSERT INTO users (name, email, birth_date)
                    VALUES (?, ?, ?)
                ''', (name, email, birth_date))
                self.conn.commit()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "A user with this name already exists.")
                return

           
            self.load_users()
            self.user_combobox.set(name)
            self.current_user = self.user_map.get(name)
            self.load_user_data()
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save_user)\
            .grid(row=3, column=0, columnspan=2, pady=10)

    def export_history(self):
        if not self.current_user:
            messagebox.showerror("Error", "No user selected.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return

        self.cursor.execute('''
            SELECT date, weight, height, bmi, notes
            FROM measurements
            WHERE user_id = ?
            ORDER BY date DESC
        ''', (self.current_user[0],))
        measurements = self.cursor.fetchall()

        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Date', 'Weight (kg)', 'Height (m)', 'BMI', 'Category', 'Notes'])
            for measure in measurements:
                bmi_val = measure[3]
                category, _ = self.classify_bmi(bmi_val)
                writer.writerow([
                    measure[0],
                    measure[1],
                    measure[2],
                    f"{bmi_val:.1f}",
                    category,
                    measure[4]
                ])

        messagebox.showinfo("Export Complete", f"Data exported to {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BMICalculatorApp(root)
    root.mainloop()

