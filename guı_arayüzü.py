import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import math
import re
import os
import webbrowser
import subprocess
import sys
from anakod5 import CircuitDesigner

class CircuitDesignerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OpAmp Devre Tasarım Sistemi")
        self.designer = ()
        self.geometry("1000x700")
        self.selected_circuit = None
        self.parameters = {}
        self.calculated_values = {}
        self.latex_code = ""
        self.current_step = 1
        self.latex_code_dir = "latex_codes"
        self.pdf_output_dir = "pdf_outputs"
        os.makedirs(self.latex_code_dir, exist_ok=True)
        os.makedirs(self.pdf_output_dir, exist_ok=True)
        self.designer = CircuitDesigner()

        # Simulated dataset
        self.circuits = [
            {"id": 1, "input": "tersleyici yükselteç", "circuit_type": "Tersleyici Yükselteç", "description": "Girişi tersleyen ve yükselten devre"},
            {"id": 2, "input": "terslemeyen yükselteç", "circuit_type": "Terslemeyen Yükselteç", "description": "Girişi terslemeden yükselten devre"},
            {"id": 3, "input": "toplayıcı yükselteç", "circuit_type": "Toplayıcı", "description": "Birden fazla girişi toplayan devre"},
            {"id": 4, "input": "alçak geçiren filtre", "circuit_type": "Alçak Geçiren Filtre", "description": "Yüksek frekansları süzen devre"},
            {"id": 5, "input": "yüksek geçiren filtre", "circuit_type": "Yüksek Geçiren Filtre", "description": "Alçak frekansları süzen devre"},
            {"id": 6, "input": "schmitt trigger", "circuit_type": "Schmitt Trigger", "description": "Eşik değerli anahtarlama devresi"},
            {"id": 7, "input": "gerilim izleyici", "circuit_type": "Gerilim İzleyici", "description": "Girişi doğrudan çıkışa aktaran devre"},
            {"id": 8, "input": "türev alıcı", "circuit_type": "Türev Alıcı", "description": "Giriş sinyalinin türevini alan devre"},
            {"id": 9, "input": "integral alıcı", "circuit_type": "Integral Alıcı", "description": "Giriş sinyalinin integralini alan devre"},
            {"id": 10, "input": "fark yükselteci", "circuit_type": "Fark Yükselteci", "description": "İki giriş arasındaki farkı yükselten devre"}
        ]
        
        self.default_config = {
            "default_resistor": "10k",
            "default_capacitor": "1u",
            "default_voltage": "15",
            "default_gain": "10",
            "default_cutoff": "1000",
            "default_time_constant": "1ms"
        }
        
        self.init_ui()
        
    def init_ui(self):
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#EBF4FF')
        self.style.configure('TLabel', background='#EBF4FF', font=('Segoe UI', 10))
        self.style.configure('TButton', font=('Segoe UI', 10), padding=6)
        self.style.configure('Title.TLabel', font=('Segoe UI', 24, 'bold'), foreground='#1F2937')
        self.style.configure('Subtitle.TLabel', font=('Segoe UI', 12), foreground='#6B7280')
        self.style.configure('Step.TLabel', font=('Segoe UI', 12, 'bold'))
        self.style.configure('StepActive.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#2563EB')
        self.style.configure('Info.TLabel', background='#EBF8FF', foreground='#0C4A6E', 
                           relief='solid', borderwidth=1, padding=8, wraplength=600)
        self.style.configure('Success.TLabel', background='#ECFDF5', foreground='#065F46', 
                           relief='solid', borderwidth=1, padding=8)
        self.style.configure('Warning.TLabel', background='#FFFBEB', foreground='#92400E', 
                           relief='solid', borderwidth=1, padding=8, wraplength=600)
        
        # Main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        self.create_header()
        
        # Progress steps
        self.create_progress_steps()
        
        # Notebook for different steps
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True, pady=10)
        self.notebook.enable_traversal()
        
        # Create step frames
        self.step_frames = {}
        self.create_step1_circuit_selection()
        self.create_step2_parameters()
        self.create_step3_results()
        self.create_step4_latex()
        self.create_step5_pdflatex()
        
        # Set initial step
        self.update_progress_display()
        
    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Title with icon
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(fill='x')
        
        icon_label = ttk.Label(title_frame, text="⚡", font=('Segoe UI', 24))
        icon_label.pack(side='left', padx=5)
        
        title_label = ttk.Label(title_frame, text="OpAmp Devre Tasarım Sistemi", style='Title.TLabel')
        title_label.pack(side='left')
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Profesyonel elektronik devre tasarımı ve analizi", 
                                 style='Subtitle.TLabel')
        subtitle_label.pack()
        
    def create_progress_steps(self):
        progress_frame = ttk.Frame(self.main_frame)
        progress_frame.pack(fill='x', pady=(0, 20))
        
        self.step_labels = []
        steps = [
            ("🔍", "Devre Seçimi"),
            ("⚙️", "Parametreler"), 
            ("🧮", "Hesaplama"),
            ("📄", "LaTeX Kodu"),
            ("🖼️", "PDF Oluştur")
        ]
        
        for i, (icon, title) in enumerate(steps):
            step_frame = ttk.Frame(progress_frame)
            step_frame.pack(side='left')
            
            # Step circle
            circle_label = ttk.Label(step_frame, text=str(i+1), style='Step.TLabel')
            circle_label.config(width=3, relief='solid', borderwidth=1, background='#D1D5DB', 
                              foreground='#6B7280', anchor='center')
            circle_label.pack()
            
            # Step title
            title_label = ttk.Label(step_frame, text=f"{icon} {title}", style='Step.TLabel')
            title_label.pack(pady=(5, 0))
            
            self.step_labels.append((circle_label, title_label))
            
            # Add connector line (except for last step)
            if i < len(steps) - 1:
                line_label = ttk.Label(progress_frame, text="──────", foreground='#D1D5DB')
                line_label.pack(side='left', padx=5, pady=15)
        
    def update_progress_display(self):
        for i, (circle_label, title_label) in enumerate(self.step_labels):
            if i + 1 <= self.current_step:
                circle_label.config(background='#2563EB', foreground='white')
                if i + 1 < self.current_step:
                    circle_label.config(text="✓")
                else:
                    circle_label.config(text=str(i + 1))
                title_label.config(style='StepActive.TLabel')
            else:
                circle_label.config(background='#D1D5DB', foreground='#6B7280', text=str(i + 1))
                title_label.config(style='Step.TLabel')
        
        # Show the current step frame
        self.notebook.select(self.current_step - 1)
    
    def create_step1_circuit_selection(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Devre Seçimi")
        self.step_frames[1] = frame
        
        # Group frame
        group_frame = ttk.LabelFrame(frame, text="🔍 Devre Türü Seçimi", padding=10)
        group_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Search section
        search_frame = ttk.Frame(group_frame)
        search_frame.pack(fill='x', pady=5)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        search_entry.bind('<Return>', lambda e: self.handle_search())
        
        search_btn = ttk.Button(search_frame, text="🔍 Ara", command=self.handle_search)
        search_btn.pack(side='left')
        
        # Circuit list
        list_frame = ttk.Frame(group_frame)
        list_frame.pack(fill='both', expand=True)
        
        self.circuit_list = tk.Listbox(list_frame, height=15, font=('Segoe UI', 10))
        self.circuit_list.pack(fill='both', expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.circuit_list.yview)
        scrollbar.pack(side='right', fill='y')
        self.circuit_list.config(yscrollcommand=scrollbar.set)
        
        for circuit in self.circuits:
            self.circuit_list.insert('end', f"{circuit['circuit_type']}\n{circuit['description']}")
        
        self.circuit_list.bind('<Double-1>', lambda e: self.select_circuit_from_list())
        
    def create_step2_parameters(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Parametreler")
        self.step_frames[2] = frame
        
        # Group frame
        self.param_group = ttk.LabelFrame(frame, text="⚙️ Parametre Girişi", padding=10)
        self.param_group.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Info label
        self.circuit_info_label = ttk.Label(
            self.param_group, 
            style='Info.TLabel',
            wraplength=600
        )
        self.circuit_info_label.pack(fill='x', pady=5)
        
        # Parameter inputs will be added dynamically
        self.param_inputs_frame = ttk.Frame(self.param_group)
        self.param_inputs_frame.pack(fill='both', expand=True, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(self.param_group)
        button_frame.pack(fill='x', pady=10)
        
        back_btn = ttk.Button(button_frame, text="Geri Dön", command=lambda: self.set_step(1))
        back_btn.pack(side='left')
        
        self.calculate_btn = ttk.Button(
            button_frame, 
            text="🧮 Hesapla", 
            command=self.calculate_parameters
        )
        self.calculate_btn.pack(side='right')
        
    def create_step3_results(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Hesaplama")
        self.step_frames[3] = frame
        
        # Group frame
        group_frame = ttk.LabelFrame(frame, text="🧮 Hesaplama Sonuçları", padding=10)
        group_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Results display
        self.results_frame = ttk.Frame(group_frame)
        self.results_frame.pack(fill='both', expand=True)
        
        # Buttons
        button_frame = ttk.Frame(group_frame)
        button_frame.pack(fill='x', pady=10)
        
        back_btn = ttk.Button(
            button_frame, 
            text="Parametreleri Düzenle", 
            command=lambda: self.set_step(2)
        )
        back_btn.pack(side='left')
        
        latex_btn = ttk.Button(
            button_frame, 
            text="📄 LaTeX Kodu Oluştur", 
            command=self.generate_latex_code
        )
        latex_btn.pack(side='right')
        
    def create_step4_latex(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="LaTeX Kodu")
        self.step_frames[4] = frame
        
        # Group frame
        group_frame = ttk.LabelFrame(frame, text="📄 LaTeX Devre Kodu", padding=10)
        group_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Toggle button
        self.show_latex_btn = ttk.Button(
            group_frame, 
            text="Kodu Göster", 
            command=self.toggle_latex_display
        )
        self.show_latex_btn.pack(pady=5)
        
        # LaTeX code display
        self.latex_display = scrolledtext.ScrolledText(
            group_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=20,
            font=('Courier New', 10),
            background='#1F2937',
            foreground='#10B981'
        )
        self.latex_display.pack(fill='both', expand=True, pady=5)
        self.latex_display.pack_forget()  # Initially hidden
        
        # Warning label
        warning_label = ttk.Label(
            group_frame,
            text="⚠️ PDF Oluşturma\nLaTeX kodunu PDF'e dönüştürmek için bilgisayarınızda LaTeX derleyicisi (pdflatex) kurulu olmalıdır.\nKodu kopyalayıp yerel ortamınızda derleyebilirsiniz.",
            style='Warning.TLabel'
        )
        warning_label.pack(fill='x', pady=5)
        
        # Buttons
        button_frame = ttk.Frame(group_frame)
        button_frame.pack(fill='x', pady=10)
        
        back_btn = ttk.Button(
            button_frame, 
            text="Geri Dön", 
            command=lambda: self.set_step(3)
        )
        back_btn.pack(side='left')
        
        copy_btn = ttk.Button(
            button_frame, 
            text="📋 Kopyala", 
            command=self.copy_latex_code
        )
        copy_btn.pack(side='right', padx=(0, 5))
        
        save_btn = ttk.Button(
            button_frame, 
            text="💾 Kaydet", 
            command=self.save_latex_code
        )
        save_btn.pack(side='right')
        
    def create_step5_pdflatex(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="PDF Oluştur")
        self.step_frames[5] = frame

        group_frame = ttk.LabelFrame(frame, text="📄 LaTeX Dosyası Seçimi ve PDF İşlemleri", padding=10)
        group_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # LaTeX Dosyası Listesi
        latex_files_label = ttk.Label(group_frame, text="Kaydedilmiş LaTeX Dosyaları:")
        latex_files_label.pack(pady=5)

        self.latex_file_list = tk.Listbox(group_frame, height=10, font=('Segoe UI', 10))
        self.latex_file_list.pack(fill='x', pady=5)

        scrollbar = ttk.Scrollbar(group_frame, orient='vertical', command=self.latex_file_list.yview)
        scrollbar.pack(side='right', fill='y')
        self.latex_file_list.config(yscrollcommand=scrollbar.set)

        # Butonlar
        button_frame = ttk.Frame(group_frame)
        button_frame.pack(fill='x', pady=10)

        back_btn = ttk.Button(button_frame, text="Geri Dön", command=lambda: self.set_step(4))
        back_btn.pack(side='left')

        self.compile_btn = ttk.Button(button_frame, text="PDF Oluştur", command=self.compile_selected_latex, state='disabled')
        self.compile_btn.pack(side='right', padx=5)

        self.view_btn = ttk.Button(button_frame, text="PDF'i Görüntüle", command=self.view_compiled_pdf, state='disabled')
        self.view_btn.pack(side='right')

        # Dosya listesini doldur
        self.populate_latex_file_list()
        
        # Çift tıklama olayını bağla
        self.latex_file_list.bind('<Double-1>', self.compile_and_view_selected_latex)

    def populate_latex_file_list(self):
        self.latex_file_list.delete(0, tk.END)
        try:
            for filename in os.listdir(self.latex_code_dir):
                if filename.endswith(".tex"):
                    self.latex_file_list.insert('end', filename)
            
            if self.latex_file_list.size() > 0:
                self.compile_btn.config(state='normal')
                self.view_btn.config(state='normal')
            else:
                self.compile_btn.config(state='disabled')
                self.view_btn.config(state='disabled')
        except FileNotFoundError:
            messagebox.showerror("Hata", f"LaTeX kodları klasörü bulunamadı: {self.latex_code_dir}")

    def compile_selected_latex(self):
        selected_file_index = self.latex_file_list.curselection()
        if not selected_file_index:
            messagebox.showerror("Hata", "Lütfen bir LaTeX dosyası seçin.")
            return

        selected_filename = self.latex_file_list.get(selected_file_index[0])
        latex_file_path = os.path.join(self.latex_code_dir, selected_filename)
        output_pdf_path = os.path.join(self.pdf_output_dir, selected_filename.replace(".tex", ".pdf"))

        self.compile_latex(latex_file_path, output_pdf_path)

    def compile_and_view_selected_latex(self, event):
        self.compile_selected_latex()
        self.view_compiled_pdf()

    def compile_latex(self, latex_file_path, output_pdf_path):
        try:
            # Önce PDF dosyasını sil (eğer varsa)
            if os.path.exists(output_pdf_path):
                os.remove(output_pdf_path)
                
            # pdflatex komutunu çalıştır
            command = ["pdflatex", "-interaction=nonstopmode", "-output-directory", self.pdf_output_dir, latex_file_path]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(timeout=30)  # 30 saniye zaman aşımı

            if process.returncode == 0:
                messagebox.showinfo("Başarılı", f"PDF başarıyla oluşturuldu:\n{output_pdf_path}")
                self.view_btn.config(state='normal')
                return True
            else:
                error_log = stderr.decode('utf-8', errors='replace') if stderr else stdout.decode('utf-8', errors='replace')
                messagebox.showerror("LaTeX Derleme Hatası", 
                                   f"LaTeX derlenirken bir hata oluştu:\n\n{error_log[:500]}...")
                return False
                
        except FileNotFoundError:
            messagebox.showerror("Hata", "pdflatex komutu bulunamadı. Lütfen LaTeX dağıtımının (TeX Live veya MiKTeX) kurulu olduğundan emin olun.")
            return False
        except subprocess.TimeoutExpired:
            messagebox.showerror("Hata", "LaTeX derleme işlemi zaman aşımına uğradı.")
            return False
        except Exception as e:
            messagebox.showerror("Hata", f"Beklenmeyen bir hata oluştu: {str(e)}")
            return False

    def view_compiled_pdf(self):
        selected_file_index = self.latex_file_list.curselection()
        if not selected_file_index:
            messagebox.showerror("Hata", "Lütfen görüntülemek için bir LaTeX dosyası seçin.")
            return

        selected_filename = self.latex_file_list.get(selected_file_index[0])
        pdf_file_path = os.path.join(self.pdf_output_dir, selected_filename.replace(".tex", ".pdf"))

        if os.path.exists(pdf_file_path):
            try:
                if sys.platform.startswith('darwin'):
                    subprocess.run(['open', pdf_file_path], check=True)
                elif sys.platform.startswith('win'):
                    os.startfile(pdf_file_path)
                elif sys.platform.startswith('linux'):
                    subprocess.run(['xdg-open', pdf_file_path], check=True)
                else:
                    messagebox.showinfo("Bilgi", f"PDF dosyası burada: {pdf_file_path}\nManuel olarak açmanız gerekebilir.")
            except FileNotFoundError:
                messagebox.showerror("Hata", "PDF görüntüleyici bulunamadı.")
            except Exception as e:
                messagebox.showerror("Hata", f"PDF görüntülenirken bir hata oluştu: {str(e)}")
        else:
            messagebox.showerror("Hata", "PDF dosyası henüz oluşturulmamış. Önce 'PDF Oluştur' butonuna tıklayın.")
        
    def set_step(self, step):
        self.current_step = step
        self.update_progress_display()
        
        # 5. adıma geçerken dosya listesini güncelle
        if step == 5:
            self.populate_latex_file_list()
        
    def find_best_match(self, query):
        if not query.strip():
            return None
            
        normalized_query = query.lower().strip()
        
        # Exact match first
        for circuit in self.circuits:
            if circuit['input'].lower() == normalized_query:
                return circuit
                
        # Partial match
        for circuit in self.circuits:
            if (normalized_query in circuit['input'].lower() or 
                normalized_query in circuit['circuit_type'].lower()):
                return circuit
                
        return None
        
    def handle_search(self):
        query = self.search_var.get()
        match = self.find_best_match(query)
        if match:
            # Find and select the item in the list
            for i in range(len(self.circuits)):
                if self.circuits[i]['id'] == match['id']:
                    self.circuit_list.selection_clear(0, 'end')
                    self.circuit_list.selection_set(i)
                    self.circuit_list.see(i)
                    self.circuit_list.activate(i)
                    self.select_circuit(match)
                    break
        else:
            messagebox.showinfo("Arama Sonucu", "Eşleşen devre bulunamadı.")
            
    def select_circuit_from_list(self):
        selection = self.circuit_list.curselection()
        if not selection:
            return
            
        index = selection[0]
        circuit = self.circuits[index]
        self.select_circuit(circuit)
        
    def select_circuit(self, circuit):
        self.selected_circuit = circuit
        self.parameters = {}
        self.calculated_values = {}
        
        # Update parameter input section
        self.update_parameter_inputs()
        
        self.set_step(2)
        
    def update_parameter_inputs(self):
        if not self.selected_circuit:
            return
            
        # Clear existing inputs
        for widget in self.param_inputs_frame.winfo_children():
            widget.destroy()
                
        # Update info label
        self.circuit_info_label.config(
            text=f"Seçilen Devre: {self.selected_circuit['circuit_type']}\n{self.selected_circuit['description']}"
        )
        
        circuit_type = self.selected_circuit['circuit_type'].lower()
        
        # Add parameter inputs based on circuit type
        if 'tersleyici' in circuit_type or 'terslemeyen' in circuit_type or 'fark yükselteci' in circuit_type:
            gain_label = ttk.Label(self.param_inputs_frame, text="Kazanç Değeri:")
            gain_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
            
            gain_input = ttk.Spinbox(
                self.param_inputs_frame, 
                from_=0.1, 
                to=1000, 
                increment=0.1,
                format="%.2f"
            )
            gain_input.set(self.default_config['default_gain'])
            gain_input.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
            self.parameters['gain'] = gain_input
            
        elif 'alçak geçiren' in circuit_type or 'yüksek geçiren' in circuit_type:
            cutoff_label = ttk.Label(self.param_inputs_frame, text="Kesim Frekansı (Hz):")
            cutoff_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
            
            cutoff_input = ttk.Spinbox(
                self.param_inputs_frame, 
                from_=1, 
                to=100000, 
                increment=1,
                format="%.2f"
            )
            cutoff_input.set(self.default_config['default_cutoff'])
            cutoff_input.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
            self.parameters['cutoff'] = cutoff_input
            
        elif 'toplayıcı' in circuit_type:
            gain1_label = ttk.Label(self.param_inputs_frame, text="Birinci Giriş Kazancı:")
            gain1_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
            
            gain1_input = ttk.Spinbox(
                self.param_inputs_frame, 
                from_=0.1, 
                to=1000, 
                increment=0.1,
                format="%.2f"
            )
            gain1_input.set(self.default_config['default_gain'])
            gain1_input.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
            self.parameters['gain1'] = gain1_input
            
            gain2_label = ttk.Label(self.param_inputs_frame, text="İkinci Giriş Kazancı:")
            gain2_label.grid(row=1, column=0, sticky='w', padx=5, pady=5)
            
            gain2_input = ttk.Spinbox(
                self.param_inputs_frame, 
                from_=0.1, 
                to=1000, 
                increment=0.1,
                format="%.2f"
            )
            gain2_input.set(self.default_config['default_gain'])
            gain2_input.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
            self.parameters['gain2'] = gain2_input
            
        elif 'schmitt' in circuit_type:
            vut_label = ttk.Label(self.param_inputs_frame, text="Üst Eşik Değeri (V):")
            vut_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
            
            vut_input = ttk.Spinbox(
                self.param_inputs_frame, 
                from_=0.1, 
                to=50, 
                increment=0.1,
                format="%.2f"
            )
            vut_input.set(5.0)
            vut_input.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
            self.parameters['vut'] = vut_input
            
        elif 'türev alıcı' in circuit_type or 'integral alıcı' in circuit_type:
            tau_label = ttk.Label(self.param_inputs_frame, text="Zaman Sabiti (RC):")
            tau_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
            
            tau_input = ttk.Entry(self.param_inputs_frame)
            tau_input.insert(0, self.default_config['default_time_constant'])
            tau_input.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
            self.parameters['tau'] = tau_input
            
    def calculate_parameters(self):
        if not self.selected_circuit:
            return
            
        self.calculate_btn.config(text="Hesaplanıyor...", state='disabled')
        self.update()
        
        circuit_type = self.selected_circuit['circuit_type'].lower()
        self.calculated_values = {}
        
        try:
            if 'tersleyici' in circuit_type:
                gain = float(self.parameters['gain'].get())
                R1 = self.parse_numeric_value(self.default_config['default_resistor'])
                R2 = R1 * abs(gain)
                
                self.calculated_values = {
                    'R1': self.format_resistance(R1),
                    'R2': self.format_resistance(R2),
                    'gain': f"{-gain:.2f}x",
                    'formula': "A_v = -R₂/R₁"
                }
                
            elif 'terslemeyen' in circuit_type:
                gain = float(self.parameters['gain'].get())
                R1 = self.parse_numeric_value(self.default_config['default_resistor'])
                R2 = R1 * (gain - 1)
                
                self.calculated_values = {
                    'R1': self.format_resistance(R1),
                    'R2': self.format_resistance(R2),
                    'gain': f"{gain:.2f}x",
                    'formula': "A_v = 1 + R₂/R₁"
                }
                
            elif 'alçak geçiren' in circuit_type or 'yüksek geçiren' in circuit_type:
                cutoff = float(self.parameters['cutoff'].get())
                C = self.parse_numeric_value(self.default_config['default_capacitor'])
                R = 1 / (2 * math.pi * cutoff * C)
                
                self.calculated_values = {
                    'R': self.format_resistance(R),
                    'C': self.format_capacitance(C),
                    'cutoff': f"{cutoff:.2f} Hz",
                    'formula': "f_c = 1/(2πRC)"
                }
                
            elif 'toplayıcı' in circuit_type:
                gain1 = float(self.parameters['gain1'].get())
                gain2 = float(self.parameters['gain2'].get())
                Rf = self.parse_numeric_value(self.default_config['default_resistor'])
                R1 = Rf / abs(gain1)
                R2 = Rf / abs(gain2)
                
                self.calculated_values = {
                    'Rf': self.format_resistance(Rf),
                    'R1': self.format_resistance(R1),
                    'R2': self.format_resistance(R2),
                    'formula': "V_out = -(R_f/R₁)V₁ - (R_f/R₂)V₂"
                }
                
            elif 'schmitt' in circuit_type:
                vut = float(self.parameters['vut'].get())
                Vcc = self.parse_numeric_value(self.default_config['default_voltage'])
                R1 = self.parse_numeric_value(self.default_config['default_resistor'])
                R2 = R1 * (vut / (Vcc - vut))
                
                self.calculated_values = {
                    'R1': self.format_resistance(R1),
                    'R2': self.format_resistance(R2),
                    'vut': f"{vut:.2f} V",
                    'vlt': f"{-vut:.2f} V"
                }
                
            elif 'gerilim izleyici' in circuit_type:
                self.calculated_values = {
                    'gain': "1.00x",
                    'formula': "V_out = V_in"
                }
                
            elif 'türev alıcı' in circuit_type:
                tau = self.parse_numeric_value(self.parameters['tau'].get())
                R = self.parse_numeric_value(self.default_config['default_resistor'])
                C = tau / R
                
                self.calculated_values = {
                    'R': self.format_resistance(R),
                    'C': self.format_capacitance(C),
                    'tau': f"{tau * 1000:.2f} ms",
                    'formula': "V_out = -RC(dV_in/dt)"
                }
                
            elif 'integral alıcı' in circuit_type:
                tau = self.parse_numeric_value(self.parameters['tau'].get())
                R = self.parse_numeric_value(self.default_config['default_resistor'])
                C = tau / R
                Rf = R * 10
                
                self.calculated_values = {
                    'R': self.format_resistance(R),
                    'C': self.format_capacitance(C),
                    'Rf': self.format_resistance(Rf),
                    'tau': f"{tau * 1000:.2f} ms",
                    'formula': "V_out = -(1/RC)∫V_in dt"
                }
                
            elif 'fark yükselteci' in circuit_type:
                gain = float(self.parameters['gain'].get())
                R1 = self.parse_numeric_value(self.default_config['default_resistor'])
                R3 = R1 * gain
                
                self.calculated_values = {
                    'R1': self.format_resistance(R1),
                    'R2': self.format_resistance(R1),
                    'R3': self.format_resistance(R3),
                    'R4': self.format_resistance(R3),
                    'gain': f"{gain:.2f}x",
                    'formula': "A_v = R₃/R₁"
                }
            
            self.update_results_display()
            self.set_step(3)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama sırasında hata oluştu: {str(e)}")
            
        
        finally:
            self.calculate_btn.config(text="🧮 Hesapla", state='normal')
    
    def update_results_display(self):
        # Clear existing results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        if not self.calculated_values:
            return
            
        # Add success header
        header_label = ttk.Label(
            self.results_frame, 
            text="✅ Hesaplanan Değerler",
            style='Success.TLabel',
            font=('Segoe UI', 14, 'bold')
        )
        header_label.pack(fill='x', pady=(0, 10))
        
        # Add calculated values in grid
        canvas = tk.Canvas(self.results_frame)
        scrollbar = ttk.Scrollbar(self.results_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        row = 0
        col = 0
        for key, value in self.calculated_values.items():
            result_frame = ttk.Frame(
                scrollable_frame, 
                relief='solid', 
                borderwidth=1,
                padding=10
            )
            result_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            key_label = ttk.Label(
                result_frame, 
                text=key.upper(),
                foreground='#6B7280',
                font=('Segoe UI', 9, 'bold')
            )
            key_label.pack(anchor='w')
            
            value_label = ttk.Label(
                result_frame, 
                text=str(value),
                foreground='#1F2937',
                font=('Segoe UI', 12, 'bold')
            )
            value_label.pack(anchor='w')
            
            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1
    
    def parse_numeric_value(self, value_str):
        clean_str = str(value_str).replace(' ', '')
        
        # Extract number and unit
        match = re.match(r'^([\d.]+)([kKMuμnp]?)', clean_str)
        if not match:
            try:
                return float(clean_str)
            except:
                return 0
        
        number = float(match.group(1))
        unit = match.group(2)
        
        # Convert based on unit
        multipliers = {
            'p': 1e-12,  # pico
            'n': 1e-9,   # nano
            'μ': 1e-6,   # micro
            'u': 1e-6,   # micro (alternative)
            'k': 1e3,    # kilo
            'K': 1e3,    # kilo (alternative)
            'M': 1e6     # mega
        }
        
        if unit in multipliers:
            return number * multipliers[unit]
        else:
            return number
    
    def format_resistance(self, value):
        if value >= 1e6:
            return f"{value/1e6:.2f} MΩ"
        elif value >= 1e3:
            return f"{value/1e3:.2f} kΩ"
        else:
            return f"{value:.2f} Ω"
    
    def format_capacitance(self, value):
        if value >= 1e-3:
            return f"{value*1e3:.2f} mF"
        elif value >= 1e-6:
            return f"{value*1e6:.2f} μF"
        elif value >= 1e-9:
            return f"{value*1e9:.2f} nF"
        else:
            return f"{value*1e12:.2f} pF"
    
    def generate_latex_code(self):
        
        if not self.selected_circuit or not self.calculated_values:
            return
        
        converted_params = {k: str(v) for k, v in self.calculated_values.items()}

        latex_code = self.designer.generate_latex_code(self.selected_circuit["circuit_type"], converted_params)

        if latex_code is None:
            messagebox.showerror("Hata", "LaTeX şablonu bulunamadı.")
            return
        
        self.latex_code = latex_code
        self.latex_display.delete('1.0', 'end')
        self.latex_display.insert('1.0', latex_code)
        self.set_step(4)

        # Otomatik dosya ismi
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", self.selected_circuit['circuit_type'])
        tex_filename = f"{safe_name}.tex"
        tex_path = os.path.join(self.latex_code_dir, tex_filename)

        try:
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(self.latex_code)
        except Exception as e:
            messagebox.showerror("Hata", f"LaTeX kodu kaydedilirken hata oluştu: {e}")
            return

        # PDF derle
        pdf_filename = tex_filename.replace(".tex", ".pdf")
        pdf_path = os.path.join(self.pdf_output_dir, pdf_filename)
        self.compile_latex(tex_path, pdf_path)

        # PDF görüntüle
        if os.path.exists(pdf_path):
            try:
                if sys.platform.startswith('darwin'):
                    subprocess.run(['open', pdf_path], check=True)
                elif sys.platform.startswith('win'):
                    os.startfile(pdf_path)
                elif sys.platform.startswith('linux'):
                    subprocess.run(['xdg-open', pdf_path], check=True)
                else:
                    messagebox.showinfo("Bilgi", f"PDF dosyası burada: {pdf_path}\nManuel olarak açabilirsiniz.")
            except Exception as e:
                messagebox.showerror("Hata", f"PDF görüntülerken hata oluştu: {e}")

        self.latex_code = latex_code
        self.latex_display.delete('1.0', 'end')
        self.latex_display.insert('1.0', latex_code)
        self.set_step(4)
            
        template = f"""\\documentclass{{article}}
\\usepackage{{circuitikz}}
\\usepackage{{amsmath}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[turkish]{{babel}}

\\begin{{document}}

\\title{{{self.selected_circuit['circuit_type']} Devresi}}
\\author{{OpAmp Devre Tasarım Sistemi}}
\\date{{\\today}}
\\maketitle

\\section{{Devre Bilgileri}}
\\textbf{{Devre Türü:}} {self.selected_circuit['circuit_type']} \\\\
\\textbf{{Açıklama:}} {self.selected_circuit['description']}

\\section{{Hesaplanan Değerler}}
\\begin{{itemize}}"""

        for key, value in self.calculated_values.items():
            if key != 'formula':
                template += f"\n\\item \\textbf{{{key.upper()}:}} {value}"
        
        if 'formula' in self.calculated_values:
            template += f"""
\\end{{itemize}}

\\section{{Formül}}
\\begin{{equation}}

{self.calculated_values['formula']}
\\end{{equation}}"""
        else:
            template += "\n\\end{itemize}"

        template += f"""

\\section{{Devre Şeması}}
\\begin{{figure}}[h]
\\centering
\\begin{{circuitikz}}[scale=1.2]
% {self.selected_circuit['circuit_type']} devre şeması buraya eklenecek
% Hesaplanan değerler ile birlikte çizilecek
\\draw (0,0) to[short] (2,0);
\\node at (1,-0.5) {{Devre şeması LaTeX ortamında tamamlanacak}};
\\end{{circuitikz}}
\\caption{{{self.selected_circuit['circuit_type']} Devresi}}
\\end{{figure}}

\\section{{Notlar}}
Bu devre LaTeX ile oluşturulmuştur. Hesaplanan değerler:
\\begin{{verbatim}}
{json.dumps(self.calculated_values, indent=2, ensure_ascii=False)}
\\end{{verbatim}}

\\end{{document}}"""
        
        self.latex_code = template
        self.latex_display.delete('1.0', 'end')
        self.latex_display.insert('1.0', template)
        self.set_step(4)
    
    def toggle_latex_display(self):
        if self.latex_display.winfo_ismapped():
            self.latex_display.pack_forget()
            self.show_latex_btn.config(text="Kodu Göster")
        else:
            self.latex_display.pack(fill='both', expand=True, pady=5)
            self.show_latex_btn.config(text="Kodu Gizle")
    
    def copy_latex_code(self):
        self.clipboard_clear()
        self.clipboard_append(self.latex_code)
        messagebox.showinfo("Kopyalandı", "LaTeX kodu panoya kopyalandı!")
    
    def save_latex_code(self):
        if not self.latex_code:
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".tex",
            filetypes=[("LaTeX Dosyaları", "*.tex"), ("Tüm Dosyalar", "*.*")],
            title="LaTeX Kodunu Kaydet"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.latex_code)
                messagebox.showinfo("Başarılı", f"LaTeX kodu başarıyla kaydedildi:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Hata", f"Kaydetme sırasında hata oluştu: {str(e)}")
        self.populate_latex_file_list()
        # Kod bloğunun SONUNA şu kısmı ekleyin:
if __name__ == "__main__":
    app = CircuitDesignerGUI()
    app.mainloop()