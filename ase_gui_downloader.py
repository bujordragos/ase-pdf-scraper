#!/usr/bin/env python3
"""
ASE PDF Scraper - Enhanced GUI Version
Universal interface that configures downloads for ANY ASE faculty
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
import json
import sys
from datetime import datetime
import logging
from pathlib import Path

# Import the scraping logic WITHOUT modification
import ase_universal_downloader as downloader

# ALL ASE FACULTIES - Complete list!
FACULTY_CONFIGS = {
    "Cibernetică, Statistică și Informatică Economică (CSIE)": {
        'keywords': ['CIBERNETICA', 'CYBERNETICS', 'STATISTICA', 'INFORMATICA'],
        'programs': {
            # 4-year Bachelor programs (Licență)
            'Informatica economica': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Cibernetica economica': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Informatica economica  (Engleza)': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Statistica ?i previziune economica': ['2021-2024', '2022-2025', '2023-2026', '2024-2027'],
            'Statistica economica si data science': ['2025-2028'],
            # 2-year Master programs
            'Informatica economica (Master)': ['2024-2026', '2025-2027'],
            'E-Business': ['2022-2024', '2023-2025', '2024-2026', '2025-2027'],
            'Baze de date - suport pentru afaceri': ['2022-2024', '2023-2025', '2024-2026', '2025-2027'],
            'Statistica aplicata si data science': ['2022-2024', '2023-2025', '2024-2026', '2025-2027'],
        }
    },
    "Marketing": {
        'keywords': ['MARKETING'],
        'programs': {
            'Marketing': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Marketing (English)': ['2022-2025', '2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Management": {
        'keywords': ['MANAGEMENT'],
        'programs': {
            'Management': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Management (English)': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Antreprenoriat': ['2022-2025', '2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Finanțe, Asigurări, Bănci și Burse de Valori (FABV)": {
        'keywords': ['FINANTE', 'FINANCE', 'ASIGURARI', 'BANCI', 'BURSE'],
        'programs': {
            'Finante': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Finance (English)': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Asigurari': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Banci': ['2022-2025', '2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Contabilitate și Informatică de Gestiune (CIG)": {
        'keywords': ['CONTABILITATE', 'INFORMATICA DE GESTIUNE'],
        'programs': {
            'Contabilitate si informatica de gestiune': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Contabilitate (English)': ['2022-2025', '2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Relații Economice Internaționale (REI)": {
        'keywords': ['REI', 'INTERNATIONALE', 'RELATII ECONOMICE'],
        'programs': {
            'Relatii economice internationale': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'International Business': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Business Administration': ['2022-2025', '2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Economie Teoretică și Aplicată": {
        'keywords': ['ECONOMIE', 'TEORETICA', 'APLICATA'],
        'programs': {
            'Economie': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Economie si afaceri internationale': ['2022-2025', '2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Administrație și Management Public": {
        'keywords': ['ADMINISTRATIE', 'MANAGEMENT PUBLIC', 'PUBLICA'],
        'programs': {
            'Administratie publica': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Management public': ['2022-2025', '2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Drept și Administrație Publică": {
        'keywords': ['DREPT', 'JURIDICA'],
        'programs': {
            'Drept': ['2021-2025', '2022-2026', '2023-2027', '2024-2028', '2025-2029'],
            'Drept antreprenorial': ['2020-2022', '2021-2023', '2022-2024', '2023-2025'],
            'Dreptul european al afacerilor': ['2024-2025', '2025-2026']
        }
    },
    "Comerț": {
        'keywords': ['COMERT', 'COMMERCE'],
        'programs': {
            'Comert': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Comert international': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Turism': ['2022-2025', '2023-2026', '2024-2027', '2025-2028']
        }
    },
    "Studii Economice în Limbi Străine (FABIZ)": {
        'keywords': ['LIMBI STRAINE', 'ECONOMICE', 'FRANCEZA', 'GERMANA', 'FABIZ'],
        'programs': {
            'Administrarea afacerilor (Franceza)': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Administrarea afacerilor (Engleza)': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Economie (Franceza)': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
        }
    },
    "Agribusiness și Economia Mediului": {
        'keywords': ['AGRIBUSINESS', 'MEDIU', 'AGRICULTURA'],
        'programs': {
            'Agribusiness': ['2022-2025', '2023-2026', '2024-2027', '2025-2028'],
            'Economia mediului': ['2022-2025', '2023-2026', '2024-2027', '2025-2028']
        }
    }
}

class TkinterLogHandler(logging.Handler):
    """Custom logging handler to redirect logs to the GUI"""
    def __init__(self, text_widget, progress_callback):
        super().__init__()
        self.text_widget = text_widget
        self.progress_callback = progress_callback

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)

            # Parse progress from log messages
            if "Downloading" in msg and "/" in msg:
                try:
                    # Extract "X/Y" pattern
                    import re
                    match = re.search(r'(\d+)/(\d+)', msg)
                    if match:
                        current = int(match.group(1))
                        total = int(match.group(2))
                        self.progress_callback(current, total)
                except:
                    pass

        self.text_widget.after(0, append)

class ASEDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ASE PDF Scraper - Universal Edition")
        self.root.geometry("750x750")

        # Config file path
        self.config_file = Path(__file__).parent / "gui_settings.json"

        # Variables
        self.selected_faculty = tk.StringVar()
        self.selected_program = tk.StringVar()
        self.selected_years = tk.StringVar()
        self.selected_form = tk.StringVar(value="FRECVENTA")
        self.selected_language = tk.StringVar(value="romanian")
        self.selected_year = tk.StringVar(value="Anul III")

        # Download control variables
        self.is_downloading = False
        self.download_thread = None
        self.current_progress = tk.StringVar(value="")

        # Load saved settings
        self.load_settings()

        self.setup_ui()
        self.setup_logging()

    def setup_logging(self):
        """Setup logging to GUI and file"""
        # Create logs directory
        log_dir = Path(__file__).parent / "ASE_PDFs" / "_logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create log file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = log_dir / f"gui_{timestamp}.log"

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Clear existing handlers
        root_logger.handlers.clear()

        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(file_handler)

        # GUI handler
        gui_handler = TkinterLogHandler(self.status_text, self.update_progress_bar)
        gui_handler.setLevel(logging.INFO)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        root_logger.addHandler(gui_handler)

        logging.info(f"GUI started - Log file: {log_file}")

    def setup_ui(self):
        """Create the user interface"""
        # Title
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)

        title_label = ttk.Label(title_frame, text="ASE PDF Scraper - All Faculties",
                               font=("Arial", 16, "bold"))
        title_label.pack()

        subtitle_label = ttk.Label(title_frame,
                                  text="Download obligatory subject PDFs from ANY ASE faculty!")
        subtitle_label.pack()

        # Main frame with scrollbar
        main_canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        main_frame = ttk.Frame(main_canvas, padding="20")

        main_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

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

        # Button frame
        button_frame = ttk.Frame(download_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # Download button
        self.download_btn = ttk.Button(button_frame, text="Download Subject PDFs",
                                      command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Cancel button
        self.cancel_btn = ttk.Button(button_frame, text="Cancel",
                                    command=self.cancel_download, state="disabled")
        self.cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Progress label
        self.progress_label = ttk.Label(download_frame, textvariable=self.current_progress)
        self.progress_label.pack(fill=tk.X, pady=(0, 5))

        # Progress bar
        self.progress = ttk.Progressbar(download_frame, mode='determinate', maximum=100)
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # Status area
        status_frame = ttk.LabelFrame(main_frame, text="Download Status", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)

        self.status_text = scrolledtext.ScrolledText(status_frame, height=12, width=80, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True)

    def update_programs(self, event=None):
        """Update program dropdown based on selected faculty"""
        faculty = self.selected_faculty.get()
        if faculty and faculty in FACULTY_CONFIGS:
            programs = list(FACULTY_CONFIGS[faculty]['programs'].keys())
            self.program_combo['values'] = programs
            self.program_combo.set('')
            self.years_combo.set('')
            self.save_settings()

    def update_years(self, event=None):
        """Update years dropdown based on selected program"""
        faculty = self.selected_faculty.get()
        program = self.selected_program.get()

        if faculty and program and faculty in FACULTY_CONFIGS:
            if program in FACULTY_CONFIGS[faculty]['programs']:
                years = FACULTY_CONFIGS[faculty]['programs'][program]
                self.years_combo['values'] = years
                self.years_combo.set('')
                self.save_settings()

    def update_progress_bar(self, current, total):
        """Update the progress bar based on downloads completed"""
        if total > 0:
            percentage = (current / total) * 100
            self.progress['value'] = percentage
            self.current_progress.set(f"Downloading: {current}/{total} PDFs")

    def load_settings(self):
        """Load saved settings from JSON file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                self.selected_faculty.set(settings.get('faculty', ''))
                self.selected_program.set(settings.get('program', ''))
                self.selected_years.set(settings.get('years', ''))
                self.selected_form.set(settings.get('form', 'FRECVENTA'))
                self.selected_language.set(settings.get('language', 'romanian'))
                self.selected_year.set(settings.get('year', 'Anul III'))

                logging.info("Loaded saved settings")
            except Exception as e:
                logging.error(f"Failed to load settings: {e}")

    def save_settings(self):
        """Save current settings to JSON file"""
        try:
            settings = {
                'faculty': self.selected_faculty.get(),
                'program': self.selected_program.get(),
                'years': self.selected_years.get(),
                'form': self.selected_form.get(),
                'language': self.selected_language.get(),
                'year': self.selected_year.get()
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logging.error(f"Failed to save settings: {e}")

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

    def start_download(self):
        """Start the download process"""
        if not self.validate_selection():
            return

        if self.is_downloading:
            return

        # Save settings for next time
        self.save_settings()

        self.is_downloading = True

        # Show configuration
        config_info = (f"Faculty: {self.selected_faculty.get()}\n"
                      f"Program: {self.selected_program.get()}\n"
                      f"Years: {self.selected_years.get()}\n"
                      f"Form: {self.selected_form.get()}\n"
                      f"Language: {self.selected_language.get()}\n"
                      f"Year: {self.selected_year.get()}")

        # Clear status
        self.status_text.delete(1.0, tk.END)
        logging.info("Configuration validated!")
        logging.info(config_info)
        logging.info("=" * 50)

        # Update UI
        self.download_btn.config(state="disabled", text="Downloading...")
        self.cancel_btn.config(state="normal")
        self.progress['value'] = 0
        self.current_progress.set("Starting download...")

        # Start download in separate thread
        self.download_thread = threading.Thread(target=self.download_worker, daemon=True)
        self.download_thread.start()

    def cancel_download(self):
        """Cancel the current download"""
        if not self.is_downloading:
            return

        logging.warning("Canceling download...")
        self.is_downloading = False

        # Reset UI
        self.download_btn.config(state="normal", text="Download Subject PDFs")
        self.cancel_btn.config(state="disabled")
        self.current_progress.set("Download canceled")

        messagebox.showinfo("Canceled", "Download has been canceled.")

    def archive_old_downloads(self, current_dir):
        """Move old downloads to _archive folder for comparison"""
        try:
            # Count PDFs in current directory (including semester subdirectories)
            pdf_count = len(list(current_dir.rglob("*.pdf")))
            if pdf_count == 0:
                return  # Nothing to archive

            # Create archive directory
            archive_dir = current_dir.parent / "_archive"
            archive_dir.mkdir(exist_ok=True)

            # Create timestamped archive folder
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            folder_name = current_dir.name
            archive_folder = archive_dir / f"{folder_name}_{timestamp}"

            # Move the entire current directory to archive
            import shutil
            shutil.move(str(current_dir), str(archive_folder))

            logging.info(f"Archived old downloads to: {archive_folder}")
            logging.info(f"Archived {pdf_count} PDFs for comparison")

        except Exception as e:
            logging.warning(f"Could not archive old downloads: {e}")

    def download_worker(self):
        """Worker thread for downloading PDFs"""
        try:
            if not self.is_downloading:
                return

            # Get user configuration
            faculty = self.selected_faculty.get()
            config = FACULTY_CONFIGS[faculty]

            # Configure the downloader module directly
            downloader.USER_CONFIG = {
                'faculty_keywords': config['keywords'],
                'program_name': self.selected_program.get(),
                'study_years': self.selected_years.get(),
                'study_form': self.selected_form.get(),
                'language': self.selected_language.get(),
                'target_year': self.selected_year.get()
            }

            # Setup clean directory structure: ASE_PDFs/Informatica_economica_Anul_III_2023-2026/
            gui_dir = Path(__file__).parent
            downloads_dir = gui_dir / "ASE_PDFs"

            # Create folder name with program, year and study period
            program = self.selected_program.get().replace(" ", "_")  # "Informatica economica"
            year = self.selected_year.get().replace(" ", "_")  # "Anul III" -> "Anul_III"
            period = self.selected_years.get()  # "2023-2026"

            # Remove diacritics from folder name too
            import ase_universal_downloader as downloader_module
            folder_name = f"{program}_{year}_{period}"
            folder_name = downloader_module.remove_diacritics(folder_name)

            current_dir = downloads_dir / folder_name

            # Archive old downloads if they exist
            if current_dir.exists():
                self.archive_old_downloads(current_dir)

            # Create the current directory
            current_dir.mkdir(parents=True, exist_ok=True)

            downloader.RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
            downloader.DOWNLOAD_DIR = str(current_dir)
            downloader.BASE_DOWNLOAD_DIR = str(downloads_dir)

            logging.info("Starting download with configured settings...")
            logging.info("=" * 50)

            # Validate config
            downloader.validate_config()

            # Create session
            session = downloader.create_session()

            # Navigate to subjects page
            if not self.is_downloading:
                return
            soup = downloader.navigate_to_subjects(session, logging.getLogger())

            if not soup:
                logging.error("Failed to navigate to subjects page")
                self.show_error("Navigation failed", "Could not reach the subjects page. Check your configuration.")
                return

            # Find subjects
            if not self.is_downloading:
                return
            subjects = downloader.find_obligatory_subjects(soup, logging.getLogger())

            if not subjects:
                logging.error("No obligatory subjects found")
                self.show_error("No subjects found", "No obligatory subjects were found. Check your configuration.")
                return

            # Download PDFs
            if not self.is_downloading:
                return

            # Pass cancel check function to downloader
            def is_canceled():
                return not self.is_downloading

            success_count = downloader.download_pdfs(session, subjects, soup, logging.getLogger(), cancel_check=is_canceled)

            # Check if we were canceled
            if not self.is_downloading:
                return

            # Summary
            logging.info("=" * 50)
            logging.info(f"COMPLETED! Downloaded {success_count}/{len(subjects)} PDFs")
            logging.info(f"All files saved to: {current_dir}")

            self.show_success(success_count, len(subjects), current_dir)

        except Exception as e:
            if self.is_downloading:
                logging.error(f"Unexpected error: {str(e)}", exc_info=True)
                self.show_error("Download failed", f"An error occurred: {str(e)}")
        finally:
            if self.is_downloading:
                self.is_downloading = False
                self.reset_ui()

    def show_error(self, title, message):
        """Show error message in main thread"""
        def show():
            messagebox.showerror(title, message)
        self.root.after(0, show)

    def show_success(self, success_count, total_count, output_dir):
        """Show success message in main thread"""
        def show():
            messagebox.showinfo("Success",
                f"Download completed successfully!\n\n"
                f"Downloaded: {success_count}/{total_count} PDFs\n"
                f"Location: {output_dir}\n\n"
                f"Configuration: {self.selected_faculty.get()}")
        self.root.after(0, show)

    def reset_ui(self):
        """Reset UI to ready state"""
        def reset():
            self.download_btn.config(state="normal", text="Download Subject PDFs")
            self.cancel_btn.config(state="disabled")
            self.current_progress.set("")
            self.progress['value'] = 0
        self.root.after(0, reset)

def main():
    """Main function"""
    root = tk.Tk()
    app = ASEDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
