#!/usr/bin/env python3
"""
ASE PDF Scraper - Dynamic GUI Version
Universal interface that configures downloads for ANY ASE faculty
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import os
import tempfile
from datetime import datetime

# ALL ASE FACULTIES - Complete list!
FACULTY_CONFIGS = {
    "Cibernetică, Statistică și Informatică Economică": {
        'keywords': ['CIBERNETICA', 'CYBERNETICS', 'STATISTICA', 'INFORMATICA'],
        'programs': {
            'Informatica economica': ['2023-2026', '2024-2027', '2025-2028'],
            'Cibernetica economica': ['2023-2026', '2024-2027', '2025-2028'],
            'Statistica': ['2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Marketing": {
        'keywords': ['MARKETING'],
        'programs': {
            'Marketing': ['2023-2026', '2024-2027', '2025-2028'],
            'Marketing (English)': ['2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Management": {
        'keywords': ['MANAGEMENT'],
        'programs': {
            'Management': ['2023-2026', '2024-2027', '2025-2028'],
            'Management (English)': ['2023-2026', '2024-2027', '2025-2028'],
            'Antreprenoriat': ['2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Finanțe, Asigurări, Bănci și Burse de Valori": {
        'keywords': ['FINANTE', 'FINANCE', 'ASIGURARI', 'BANCI', 'BURSE'],
        'programs': {
            'Finante': ['2023-2026', '2024-2027', '2025-2028'],
            'Finance (English)': ['2023-2026', '2024-2027', '2025-2028'],
            'Asigurari': ['2023-2026', '2024-2027', '2025-2028'],
            'Banci': ['2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Contabilitate și Informatică de Gestiune": {
        'keywords': ['CONTABILITATE', 'INFORMATICA DE GESTIUNE'],
        'programs': {
            'Contabilitate si informatica de gestiune': ['2023-2026', '2024-2027', '2025-2028'],
            'Contabilitate (English)': ['2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Relații Economice Internaționale": {
        'keywords': ['REI', 'INTERNATIONALE', 'RELATII ECONOMICE'],
        'programs': {
            'Relatii economice internationale': ['2023-2026', '2024-2027', '2025-2028'],
            'International Business': ['2023-2026', '2024-2027', '2025-2028'],
            'Business Administration': ['2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Economie Teoretică și Aplicată": {
        'keywords': ['ECONOMIE', 'TEORETICA', 'APLICATA'],
        'programs': {
            'Economie': ['2023-2026', '2024-2027', '2025-2028'],
            'Economie si afaceri internationale': ['2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Administrație și Management Public": {
        'keywords': ['ADMINISTRATIE', 'MANAGEMENT PUBLIC', 'PUBLICA'],
        'programs': {
            'Administratie publica': ['2023-2026', '2024-2027', '2025-2028'],
            'Management public': ['2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Drept și Administrație Publică": {
        'keywords': ['DREPT', 'JURIDICA'],
        'programs': {
            'Drept': ['2024-2028', '2023-2027', '2022-2026', '2021-2025', '2020-2024'],
            'Drept antreprenorial': ['2023-2025', '2022-2024', '2021-2023', '2020-2022'],
            'Dreptul european al afacerilor': ['2024-2025']
        }
    },
    "Comerț": {
        'keywords': ['COMERT', 'COMMERCE'],
        'programs': {
            'Comert': ['2023-2026', '2024-2027', '2025-2028'],
            'Comert international': ['2023-2026', '2024-2027', '2025-2028'],
            'Turism': ['2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Studii Economice în Limbi Străine": {
        'keywords': ['LIMBI STRAINE', 'ECONOMICE', 'FRANCEZA', 'GERMANA'],
        'programs': {
            'Economie (Franceza)': ['2023-2026', '2024-2027', '2025-2028'],
            'Economie (Germana)': ['2023-2026', '2024-2027', '2025-2028'],
            'Management (Franceza)': ['2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Agribusiness și Economia Mediului": {
        'keywords': ['AGRIBUSINESS', 'MEDIU', 'AGRICULTURA'],
        'programs': {
            'Agribusiness': ['2023-2026', '2024-2027', '2025-2028'],
            'Economia mediului': ['2023-2026', '2024-2027', '2025-2028']
        }
    }
}

class ASEDownloaderDynamicGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ASE PDF Scraper - Universal Edition")
        self.root.geometry("700x700")
        
        # Variables
        self.selected_faculty = tk.StringVar()
        self.selected_program = tk.StringVar()
        self.selected_years = tk.StringVar()
        self.selected_form = tk.StringVar(value="FRECVENTA")
        self.selected_language = tk.StringVar(value="romanian")
        self.selected_year = tk.StringVar(value="Anul III")
        
        # Download control variables
        self.is_downloading = False
        self.download_process = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the user interface"""
        # Title
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(title_frame, text="🎓 ASE PDF Scraper - All Faculties", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, 
                                  text="Download obligatory subject PDFs from ANY ASE faculty!")
        subtitle_label.pack()
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Faculty selection
        faculty_frame = ttk.LabelFrame(main_frame, text="1. Select Your Faculty", padding="10")
        faculty_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.faculty_combo = ttk.Combobox(faculty_frame, textvariable=self.selected_faculty,
                                         values=list(FACULTY_CONFIGS.keys()),
                                         state="readonly", width=60)
        self.faculty_combo.pack(fill=tk.X)
        self.faculty_combo.bind('<<ComboboxSelected>>', self.update_programs)
        
        # Program selection
        program_frame = ttk.LabelFrame(main_frame, text="2. Select Your Program", padding="10")
        program_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.program_combo = ttk.Combobox(program_frame, textvariable=self.selected_program,
                                         state="readonly", width=60)
        self.program_combo.pack(fill=tk.X)
        self.program_combo.bind('<<ComboboxSelected>>', self.update_years)
        
        # Years selection
        years_frame = ttk.LabelFrame(main_frame, text="3. Select Study Years", padding="10")
        years_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.years_combo = ttk.Combobox(years_frame, textvariable=self.selected_years,
                                       state="readonly", width=20)
        self.years_combo.pack(fill=tk.X)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="4. Additional Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Study form
        form_frame = ttk.Frame(options_frame)
        form_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(form_frame, text="Study Form:").pack(side=tk.LEFT)
        ttk.Radiobutton(form_frame, text="La frecvența (In-person)", 
                       variable=self.selected_form, value="FRECVENTA").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Radiobutton(form_frame, text="La distanța (Distance)", 
                       variable=self.selected_form, value="DISTANTA").pack(side=tk.LEFT, padx=(10, 0))
        
        # Language
        lang_frame = ttk.Frame(options_frame)
        lang_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(lang_frame, text="Language:").pack(side=tk.LEFT)
        ttk.Radiobutton(lang_frame, text="Romanian", 
                       variable=self.selected_language, value="romanian").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Radiobutton(lang_frame, text="English", 
                       variable=self.selected_language, value="english").pack(side=tk.LEFT, padx=(10, 0))
        
        # Current year
        year_frame = ttk.Frame(options_frame)
        year_frame.pack(fill=tk.X)
        
        ttk.Label(year_frame, text="Current Year:").pack(side=tk.LEFT)
        year_combo = ttk.Combobox(year_frame, textvariable=self.selected_year,
                                 values=["Anul I", "Anul II", "Anul III", "Anul IV"],
                                 state="readonly", width=15)
        year_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Download section
        download_frame = ttk.LabelFrame(main_frame, text="5. Download", padding="10")
        download_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Button frame for download and cancel buttons
        button_frame = ttk.Frame(download_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Download button
        self.download_btn = ttk.Button(button_frame, text="🚀 Download Subject PDFs", 
                                      command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Cancel button
        self.cancel_btn = ttk.Button(button_frame, text="⏹ Cancel", 
                                    command=self.cancel_download, state="disabled")
        self.cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(download_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # Status area
        status_frame = ttk.LabelFrame(main_frame, text="Download Status", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=12, width=80)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
    def update_programs(self, event=None):
        """Update program dropdown based on selected faculty"""
        faculty = self.selected_faculty.get()
        if faculty and faculty in FACULTY_CONFIGS:
            programs = list(FACULTY_CONFIGS[faculty]['programs'].keys())
            self.program_combo['values'] = programs
            self.program_combo.set('')  # Clear selection
            self.years_combo.set('')    # Clear years
        
    def update_years(self, event=None):
        """Update years dropdown based on selected program"""
        faculty = self.selected_faculty.get()
        program = self.selected_program.get()
        
        if faculty and program and faculty in FACULTY_CONFIGS:
            if program in FACULTY_CONFIGS[faculty]['programs']:
                years = FACULTY_CONFIGS[faculty]['programs'][program]
                self.years_combo['values'] = years
                self.years_combo.set('')  # Clear selection
        
    def log_message(self, message):
        """Add message to status area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.status_text.insert(tk.END, formatted_message)
        self.status_text.see(tk.END)
        self.root.update_idletasks()
    
    def validate_selection(self):
        """Validate that all required fields are selected"""
        if not self.selected_faculty.get():
            messagebox.showerror("Error", "Please select your faculty")
            return False
        if not self.selected_program.get():
            messagebox.showerror("Error", "Please select your program")
            return False
        if not self.selected_years.get():
            messagebox.showerror("Error", "Please select your study years")
            return False
        return True
    
    def create_dynamic_config_script(self):
        """Create a temporary script with the user's configuration"""
        # Get user configuration
        faculty = self.selected_faculty.get()
        config = {
            'faculty_keywords': FACULTY_CONFIGS[faculty]['keywords'],
            'program_name': self.selected_program.get(),
            'study_years': self.selected_years.get(),
            'study_form': self.selected_form.get(),
            'language': self.selected_language.get(),
            'target_year': self.selected_year.get()
        }
        
        # Read the universal downloader template
        template_path = "ase_universal_downloader.py"
        if not os.path.exists(template_path):
            raise FileNotFoundError("ase_universal_downloader.py not found")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Get the directory where this GUI script is located
        gui_script_dir = os.path.dirname(os.path.abspath(__file__))
        downloads_dir = os.path.join(gui_script_dir, "ASE_PDFs")
        
        # Replace the USER_CONFIG section with the dynamic configuration
        new_config = f"""USER_CONFIG = {{
    'faculty_keywords': {config['faculty_keywords']},
    'program_name': '{config['program_name']}',
    'study_years': '{config['study_years']}',
    'study_form': '{config['study_form']}',
    'language': '{config['language']}',
    'target_year': '{config['target_year']}'
}}"""
        
        # Also replace the BASE_DOWNLOAD_DIR to use the GUI script's location
        # Use forward slashes or raw string to avoid escape issues
        downloads_dir_safe = downloads_dir.replace('\\', '/')
        new_download_dir = f'BASE_DOWNLOAD_DIR = "{downloads_dir_safe}"'
        
        # Find and replace the USER_CONFIG section
        import re
        pattern = r'USER_CONFIG\s*=\s*\{[^}]*\}'
        
        if 'USER_CONFIG' in template_content:
            # Replace existing config
            updated_content = re.sub(pattern, new_config, template_content, flags=re.DOTALL)
        else:
            # Add config if not found
            updated_content = new_config + "\n\n" + template_content
        
        # Also replace the BASE_DOWNLOAD_DIR line
        base_dir_pattern = r'BASE_DOWNLOAD_DIR\s*=\s*os\.path\.join\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\),\s*"ASE_PDFs"\)'
        updated_content = re.sub(base_dir_pattern, new_download_dir, updated_content)
        
        # Create temporary script file
        temp_dir = tempfile.gettempdir()
        temp_script = os.path.join(temp_dir, f"ase_dynamic_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
        
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        return temp_script
    
    def start_download(self):
        """Start the download process with dynamic configuration"""
        if not self.validate_selection():
            return
            
        if self.is_downloading:
            return
            
        self.is_downloading = True
        
        # Show configuration
        config_info = (f"Faculty: {self.selected_faculty.get()}\n"
                      f"Program: {self.selected_program.get()}\n" 
                      f"Years: {self.selected_years.get()}\n"
                      f"Form: {self.selected_form.get()}\n"
                      f"Language: {self.selected_language.get()}\n"
                      f"Year: {self.selected_year.get()}")
        
        # Clear status and start
        self.status_text.delete(1.0, tk.END)
        self.log_message("Configuration validated!")
        self.log_message(config_info)
        self.log_message("=" * 50)
        
        # Update UI for downloading state
        self.download_btn.config(state="disabled", text="Downloading...")
        self.cancel_btn.config(state="normal")
        self.progress.start()
        
        # Start download in separate thread
        thread = threading.Thread(target=self.download_worker)
        thread.daemon = True
        thread.start()
    
    def cancel_download(self):
        """Cancel the current download process"""
        if not self.is_downloading:
            return
            
        self.log_message("⚠ Canceling download...")
        self.log_message("Terminating download process...")
        
        # Terminate the download process if it's running
        if self.download_process and self.download_process.poll() is None:
            try:
                self.download_process.terminate()
                self.log_message("✅ Download process terminated")
            except Exception as e:
                self.log_message(f"Error terminating process: {e}")
        
        # Reset UI state
        self.is_downloading = False
        self.download_process = None
        self.download_btn.config(state="normal", text="🚀 Download Subject PDFs")
        self.cancel_btn.config(state="disabled")
        self.progress.stop()
        
        self.log_message("❌ Download canceled by user")
        messagebox.showinfo("Canceled", "Download has been canceled.")
    
    def download_worker(self):
        """Worker thread for downloading PDFs with dynamic configuration"""
        try:
            if not self.is_downloading:
                return
                
            self.log_message("Creating dynamic configuration...")
            
            # Create temporary script with user's configuration
            temp_script = self.create_dynamic_config_script()
            self.log_message(f"Generated configuration script: {os.path.basename(temp_script)}")
            
            if not self.is_downloading:
                return
                
            self.log_message("Starting universal PDF downloader...")
            self.log_message("=" * 50)
            
            # Run the configured script
            self.download_process = subprocess.Popen(
                ["python", temp_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=os.getcwd(),
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor the process output in real-time
            try:
                for line in iter(self.download_process.stdout.readline, ''):
                    if not self.is_downloading:
                        break
                    if line.strip():
                        self.log_message(line.strip())
                
                # Wait for process to complete (only if we're still downloading)
                if self.is_downloading:
                    self.download_process.wait()
            except Exception as e:
                if self.is_downloading:  # Only log if we didn't cancel
                    self.log_message(f"Process monitoring error: {e}")
            
            # Clean up temporary script
            try:
                os.remove(temp_script)
                if self.is_downloading:
                    self.log_message("Cleaned up temporary files")
            except:
                pass
            
            # Check results only if we weren't canceled
            if self.is_downloading:
                if self.download_process.returncode == 0:
                    self.log_message("=" * 50)
                    self.log_message("✅ Download completed successfully!")
                    self.log_message("📁 Check the ASE_PDFs folder for your files")
                    messagebox.showinfo("Success", 
                        f"Download completed successfully!\n\n"
                        f"✅ Obligatory subjects downloaded\n"
                        f"📁 Files saved in ASE_PDFs folder\n"
                        f"📅 Configuration: {self.selected_faculty.get()}")
                else:
                    self.log_message("❌ Download process failed")
                    self.log_message("Check the log above for error details")
                    messagebox.showerror("Error", 
                        "Download failed. Check the status log for details.")
            
        except Exception as e:
            if self.is_downloading:  # Only show error if we didn't cancel
                self.log_message(f"❌ Unexpected error: {str(e)}")
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            # Reset UI state only if we're still supposed to be downloading
            if self.is_downloading:
                self.is_downloading = False
                self.download_process = None
                self.download_btn.config(state="normal", text="🚀 Download Subject PDFs")
                self.cancel_btn.config(state="disabled")
                self.progress.stop()

def main():
    """Main function"""
    root = tk.Tk()
    app = ASEDownloaderDynamicGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
