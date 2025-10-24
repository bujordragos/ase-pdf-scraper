#!/usr/bin/env python3
"""
ASE PDF Downloader - Configurable Version
Universal script for downloading obligatory subject PDFs from any ASE faculty/program

HOW TO CONFIGURE FOR YOUR FACULTY:
1. Edit the USER_CONFIG section below with your details
2. Run the script: python ase_universal_downloader.py
3. The script will find your faculty, program, and year automatically

SUPPORTED FACULTIES:
- CIBERNETICĂ, STATISTICĂ ŞI INFORMATICĂ ECONOMICĂ (CSIE)
- CONTABILITATE ŞI INFORMATICĂ DE GESTIUNE (CCIG)
- MARKETING (MK)
- MANAGEMENT (MAN)
- ECONOMIE TEORETICĂ ŞI APLICATĂ (ETAA)
- FINANȚE, ASIGURĂRI, BĂNCI ŞI BURSE DE VALORI (FABV)
- REI (Relații Economice Internaționale)
- CIEG (Comerț Internațional și Integrare Europeană)
- And more...

EXAMPLE CONFIGURATIONS:
# For Cybernetics student:
USER_CONFIG = {
    'faculty_keywords': ['CIBERNETICĂ', 'CYBERNETICS'],
    'program_name': 'Informatica economica',
    'study_years': '2023-2026',
    'study_form': 'FRECVENȚĂ',  # or 'DISTANȚĂ' 
    'language': 'romanian',  # 'romanian' or 'english'
    'target_year': 'Anul III'
}

# For Marketing student:
USER_CONFIG = {
    'faculty_keywords': ['MARKETING'],
    'program_name': 'Marketing',
    'study_years': '2024-2027',
    'study_form': 'FRECVENȚĂ',
    'language': 'romanian',
    'target_year': 'Anul II'
}
"""

import requests
from bs4 import BeautifulSoup
import os
import re
import time
from datetime import datetime
from urllib.parse import urljoin
import logging

# =============================================================================
# USER CONFIGURATION - EDIT THIS SECTION FOR YOUR FACULTY/PROGRAM
# =============================================================================

USER_CONFIG = {
    # Faculty identification - use keywords that appear in your faculty name
    'faculty_keywords': ['CIBERNETICA', 'CYBERNETICS', 'INFORMATICA ECONOMICA'],
    
    # Your exact program name as it appears on the website
    'program_name': 'Informatica economica',
    
    # Study years (format: YYYY-YYYY)
    'study_years': '2023-2026',
    
    # Study form: 'FRECVENTA' (in-person) or 'DISTANTA' (distance learning)
    'study_form': 'FRECVENTA',
    
    # Language preference: 'romanian' or 'english' 
    'language': 'romanian',
    
    # Target year: 'Anul I', 'Anul II', 'Anul III', etc.
    'target_year': 'Anul III'
}

# =============================================================================
# ALTERNATIVE CONFIGURATIONS FOR FRIENDS (copy one of these to USER_CONFIG)
# =============================================================================

EXAMPLE_CONFIGS = {
    'cybernetics_year3': {
        'faculty_keywords': ['CIBERNETICĂ', 'CYBERNETICS'],
        'program_name': 'Informatica economica',
        'study_years': '2023-2026',
        'study_form': 'FRECVENȚĂ',
        'language': 'romanian',
        'target_year': 'Anul III'
    },
    
    'marketing_year2': {
        'faculty_keywords': ['MARKETING'],
        'program_name': 'Marketing',
        'study_years': '2024-2027',
        'study_form': 'FRECVENȚĂ',
        'language': 'romanian',
        'target_year': 'Anul II'
    },
    
    'management_year1': {
        'faculty_keywords': ['MANAGEMENT'],
        'program_name': 'Management',
        'study_years': '2025-2028',
        'study_form': 'FRECVENȚĂ',
        'language': 'romanian',
        'target_year': 'Anul I'
    },
    
    'finance_year3_english': {
        'faculty_keywords': ['FINANȚE', 'FINANCE'],
        'program_name': 'Finance',
        'study_years': '2023-2026',
        'study_form': 'FRECVENȚĂ',
        'language': 'english',
        'target_year': 'Anul III'
    }
}

# =============================================================================
# SYSTEM CONFIGURATION (usually don't need to change)
# =============================================================================

BASE_URL = "https://fisadisciplina.ase.ro/"
BASE_DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ASE_PDFs")
DATE_FORMAT = "%Y%m%d_%H%M%S"

# Will be set dynamically based on user's configuration
RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
DOWNLOAD_DIR = os.path.join(BASE_DOWNLOAD_DIR, f"Run_{RUN_TIMESTAMP}")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ro-RO,ro;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Referer': BASE_URL
}

def setup_logging():
    """Setup logging"""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    log_dir = os.path.join(BASE_DOWNLOAD_DIR, "_logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"download_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_config():
    """Validate user configuration"""
    required_keys = ['faculty_keywords', 'program_name', 'study_years', 'study_form', 'language', 'target_year']
    
    for key in required_keys:
        if key not in USER_CONFIG:
            raise ValueError(f"Missing required configuration: {key}")
    
    if USER_CONFIG['language'] not in ['romanian', 'english']:
        raise ValueError("Language must be 'romanian' or 'english'")
    
    if USER_CONFIG['study_form'] not in ['FRECVENTA', 'DISTANTA']:
        raise ValueError("Study form must be 'FRECVENTA' or 'DISTANTA'")
    
    return True

def create_session():
    """Create a session with browser headers"""
    session = requests.Session()
    session.headers.update(HEADERS)
    return session

def get_form_data(soup):
    """Extract form data including ASP.NET viewstate"""
    form = soup.find('form')
    if not form:
        return None, None
    
    action = form.get('action', '')
    if action.startswith('./'):
        action = action[2:]
    action = urljoin(BASE_URL, action)
    
    form_data = {}
    for input_tag in form.find_all('input', type='hidden'):
        name = input_tag.get('name')
        value = input_tag.get('value', '')
        if name:
            form_data[name] = value
    
    return action, form_data

def find_faculty(soup, logger):
    """Find the user's faculty based on keywords"""
    logger.info(f"Looking for faculty with keywords: {USER_CONFIG['faculty_keywords']}")
    
    for row in soup.find_all('tr'):
        row_text = row.get_text().upper()
        
        # Check if any faculty keyword matches
        for keyword in USER_CONFIG['faculty_keywords']:
            if keyword.upper() in row_text:
                logger.info(f"Found faculty: {row_text.strip()}")
                
                # Find the corresponding link
                link = row.find('a', href=True)
                if link and 'plan$' in link.get('href', ''):
                    match = re.search(r"'GridView1','(plan\$\d+)'", link.get('href'))
                    if match:
                        return match.group(1)
    
    logger.error(f"Faculty not found! Available faculties:")
    for row in soup.find_all('tr'):
        if row.find('a', href=True) and 'plan$' in str(row):
            logger.error(f"  - {row.get_text().strip()}")
    
    return None

def find_program_and_year(soup, logger):
    """Find the specific program and year"""
    logger.info(f"Looking for program: {USER_CONFIG['program_name']} ({USER_CONFIG['study_years']}) - {USER_CONFIG['study_form']}")
    
    for row in soup.find_all('tr'):
        row_text = row.get_text()
        
        # Check all criteria match (handle both ASCII and special characters)
        study_form_variants = ['FRECVENTA', 'FRECVENȚĂ', 'FRECVENŢĂ'] if USER_CONFIG['study_form'] == 'FRECVENTA' else ['DISTANTA', 'DISTANȚĂ', 'DISTANŢĂ']
        
        if (USER_CONFIG['program_name'] in row_text and 
            USER_CONFIG['study_years'] in row_text and
            any(variant in row_text.upper() for variant in study_form_variants)):
            
            # Make sure it's not the wrong language version (English vs Romanian)
            if USER_CONFIG['study_form'] == 'FRECVENTA':
                # Skip English programs if we want Romanian
                if 'ENGLEZA' in row_text.upper() or 'ENGLISH' in row_text.upper():
                    continue
            
            logger.info(f"Found target program: {row_text.strip()}")
            
            # Look for the target year link
            for link in row.find_all('a', href=True):
                if USER_CONFIG['target_year'] in link.get_text():
                    href = link.get('href')
                    
                    # Extract the parameter based on year
                    year_patterns = {
                        'Anul I': r"'GridView1','(unu\$\d+)'",
                        'Anul II': r"'GridView1','(doi\$\d+)'", 
                        'Anul III': r"'GridView1','(trei\$\d+)'",
                        'Anul IV': r"'GridView1','(patru\$\d+)'"
                    }
                    
                    pattern = year_patterns.get(USER_CONFIG['target_year'])
                    if pattern:
                        match = re.search(pattern, href)
                        if match:
                            logger.info(f"Found {USER_CONFIG['target_year']} link")
                            return match.group(1)
    
    logger.error("Program/year combination not found! Available programs:")
    for row in soup.find_all('tr'):
        if (USER_CONFIG['program_name'] in row.get_text() or 
            any(keyword.lower() in row.get_text().lower() for keyword in USER_CONFIG['faculty_keywords'])):
            logger.error(f"  - {row.get_text().strip()}")
    
    return None

def remove_diacritics(text):
    """Remove Romanian diacritics from text"""
    diacritics_map = {
        'ă': 'a', 'Ă': 'A',
        'â': 'a', 'Â': 'A',
        'î': 'i', 'Î': 'I',
        'ș': 's', 'Ș': 'S',
        'ț': 't', 'Ț': 'T'
    }
    for diacritic, replacement in diacritics_map.items():
        text = text.replace(diacritic, replacement)
    return text

def extract_clean_subject_name(full_text):
    """Extract clean subject name based on language preference"""
    if USER_CONFIG['language'] == 'english':
        # For English, extract the part after <br /> (newline)
        if '\n' in full_text:
            parts = full_text.split('\n')
            if len(parts) > 1:
                return parts[1].strip()
        return full_text
    else:
        # For Romanian, extract the part before <br /> (newline)
        # The HTML structure is: "Romanian Name\nEnglish Name"
        if '\n' in full_text:
            romanian_name = full_text.split('\n')[0].strip()
            return romanian_name

        # If no newline, just return the full text (it's already Romanian-only)
        return full_text.strip()

def navigate_to_subjects(session, logger):
    """Navigate through the website to find subjects"""
    
    # Step 1: Load main page
    logger.info("Step 1: Loading main page...")
    response = session.get(BASE_URL)
    if response.status_code != 200:
        logger.error("Failed to load website")
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    logger.info("Main page loaded successfully")
    
    # Step 2: Find and select faculty
    action, form_data = get_form_data(soup)
    if not action:
        logger.error("No form found on main page")
        return None
    
    faculty_param = find_faculty(soup, logger)
    if not faculty_param:
        return None
    
    form_data['__EVENTTARGET'] = 'GridView1'
    form_data['__EVENTARGUMENT'] = faculty_param
    
    response = session.post(action, data=form_data)
    if response.status_code != 200:
        logger.error("Faculty selection failed")
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    logger.info("Faculty selected successfully")

    # Save debug page to _debug folder
    debug_dir = os.path.join(BASE_DOWNLOAD_DIR, "_debug")
    os.makedirs(debug_dir, exist_ok=True)
    debug_file = os.path.join(debug_dir, f"faculty_programs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(response.text)
    logger.debug(f"Debug page saved to: {debug_file}")
    
    # Step 3: Find and select program/year
    action, form_data = get_form_data(soup)
    if not action:
        logger.error("No form found on programs page")
        return None
    
    year_param = find_program_and_year(soup, logger)
    if not year_param:
        return None
    
    form_data['__EVENTTARGET'] = 'GridView1'
    form_data['__EVENTARGUMENT'] = year_param
    
    response = session.post(action, data=form_data)
    if response.status_code != 200:
        logger.error("Year selection failed")
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    logger.info(f"Successfully reached {USER_CONFIG['target_year']} subjects page!")

    # Save subjects page to _debug folder
    debug_dir = os.path.join(BASE_DOWNLOAD_DIR, "_debug")
    os.makedirs(debug_dir, exist_ok=True)
    debug_file = os.path.join(debug_dir, f"subjects_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(response.text)
    logger.debug(f"Subjects page saved to: {debug_file}")
    
    return soup

def find_obligatory_subjects(soup, logger):
    """Find all obligatory subjects with semester information"""
    logger.info("Searching for obligatory subjects...")

    subjects = []
    seen_subjects = set()

    # Determine which download buttons to look for
    button_pattern = 'ProgramaRO' if USER_CONFIG['language'] == 'romanian' else 'ProgramaEN'

    # Find all tables (subjects are usually in tables)
    tables = soup.find_all('table')

    for table in tables:
        current_semester = None  # Reset for each table
        rows = table.find_all('tr')

        for row in rows:
            # Check if this row is a semester header
            row_text = row.get_text(strip=True)
            if 'Semestrul I' in row_text and 'Semestrul II' not in row_text:
                current_semester = 'Semestrul_I'
                logger.info(f"Found semester header: {current_semester}")
                continue
            elif 'Semestrul II' in row_text:
                current_semester = 'Semestrul_II'
                logger.info(f"Found semester header: {current_semester}")
                continue

            # Find download button in this row
            button = row.find('input', type='image')
            if not button or button_pattern not in button.get('onclick', ''):
                continue

            # Check if this row contains an obligatory subject (marked with 'O')
            cells = row.find_all(['td', 'th'])
            is_obligatory = False
            subject_name = "Unknown_Subject"

            # Look for 'O' in the type column and extract subject name
            for cell in cells:
                cell_text = cell.get_text(strip=True)

                # Check if this is the type column with 'O'
                if cell_text == 'O':
                    is_obligatory = True

                    # Get subject name from first cell (subject column)
                    if len(cells) > 0:
                        subject_cell = cells[0]
                        # Use separator='\n' to preserve line breaks from <br> tags
                        full_text = subject_cell.get_text(separator='\n', strip=True)
                        subject_name = extract_clean_subject_name(full_text)

                    break

            if is_obligatory:
                # Clean subject name for deduplication
                clean_subject = re.sub(r'[^a-zA-ZăâîșțĂÂÎȘȚ\s]', '', subject_name).lower().strip()

                # Skip if we've already found this subject
                if clean_subject in seen_subjects:
                    continue

                seen_subjects.add(clean_subject)

                # Extract download parameters from button onclick
                onclick = button.get('onclick', '')
                match = re.search(r"'([^']+)','([^']+)'", onclick)
                if match:
                    subjects.append({
                        'name': subject_name,
                        'target': match.group(1),
                        'argument': match.group(2),
                        'semester': current_semester if current_semester else 'Unknown'
                    })
                    logger.info(f"Found: {subject_name} ({current_semester if current_semester else 'Unknown semester'})")

    logger.info(f"Total obligatory subjects found: {len(subjects)}")
    return subjects

def download_pdfs(session, subjects, soup, logger, cancel_check=None):
    """Download all PDFs organized by semester

    Args:
        cancel_check: Optional callable that returns True if download should be canceled
    """
    logger.info("Starting downloads...")

    success_count = 0

    for i, subject in enumerate(subjects, 1):
        # Check if user canceled
        if cancel_check and cancel_check():
            logger.warning("Download canceled by user")
            break

        logger.info(f"Downloading {i}/{len(subjects)}: {subject['name']} [{subject.get('semester', 'Unknown')}]")

        try:
            # Get current form data
            action, form_data = get_form_data(soup)
            if not action:
                logger.error(f"No form data for {subject['name']}")
                continue

            # Set download parameters
            form_data['__EVENTTARGET'] = subject['target']
            form_data['__EVENTARGUMENT'] = subject['argument']

            # Submit download request
            response = session.post(action, data=form_data)

            if response.status_code == 200 and response.content.startswith(b'%PDF'):
                # Create semester subfolder
                semester = subject.get('semester', 'Unknown')
                semester_dir = os.path.join(DOWNLOAD_DIR, semester)
                os.makedirs(semester_dir, exist_ok=True)

                # Clean filename: remove diacritics, clean special chars, remove extra spaces
                clean_name = remove_diacritics(subject['name'])
                clean_name = re.sub(r'[<>:"/\\|?*]', '_', clean_name)
                clean_name = re.sub(r'\s+', '_', clean_name)
                clean_name = clean_name.strip('._')

                filename = f"{clean_name}.pdf"

                filepath = os.path.join(semester_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)

                size_kb = len(response.content) // 1024
                logger.info(f"SUCCESS: Saved {semester}/{filename} ({size_kb} KB)")
                success_count += 1
            else:
                logger.error(f"Download failed for {subject['name']}")
                
        except Exception as e:
            logger.error(f"Error downloading {subject['name']}: {e}")
        
        # Be nice to the server
        time.sleep(2)
    
    return success_count

def main():
    """Main function"""
    print("ASE PDF Downloader - Universal Version")
    print("=" * 50)
    
    try:
        # Validate configuration
        validate_config()
        print(f"Configuration validated for: {USER_CONFIG['faculty_keywords'][0]} - {USER_CONFIG['program_name']}")
        print(f"Creating run folder: Run_{RUN_TIMESTAMP}")
        
        logger = setup_logging()
        session = create_session()
        
        logger.info(f"Starting download for: {USER_CONFIG}")
        
        # Navigate to subjects page
        soup = navigate_to_subjects(session, logger)
        if not soup:
            logger.error("Failed to navigate to subjects page")
            return
        
        # Find obligatory subjects
        subjects = find_obligatory_subjects(soup, logger)
        if not subjects:
            logger.error("No obligatory subjects found")
            return
        
        # Download PDFs
        success_count = download_pdfs(session, subjects, soup, logger)
        
        # Summary
        logger.info("=" * 50)
        logger.info(f"COMPLETED! Downloaded {success_count}/{len(subjects)} PDFs")
        logger.info(f"All files saved to: {DOWNLOAD_DIR}")

        print(f"\nDownload complete! Check {DOWNLOAD_DIR} for your files.")
        print(f"\nClean Structure:")
        print(f"   ASE_PDFs/")
        print(f"      {os.path.basename(DOWNLOAD_DIR)}/")
        print(f"         Semestrul_I/")
        print(f"            [PDF files - no diacritics, full names]")
        print(f"         Semestrul_II/")
        print(f"            [PDF files - no diacritics, full names]")
        print(f"      _logs/")
        print(f"         download_*.log")
        print(f"      _debug/  (for troubleshooting)")
        print(f"      _archive/  (old downloads for comparison)")
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nPlease check the USER_CONFIG section at the top of this file.")
        print("Make sure all required fields are filled in correctly.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Check the log files for more details.")

if __name__ == "__main__":
    main()
