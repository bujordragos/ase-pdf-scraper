#!/usr/bin/env python3
"""
ASE PDF Downloader - Full Navigation Version
This script navigates through the forms step-by-step like a real user
"""

import requests
from bs4 import BeautifulSoup
import os
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
import logging

# Configuration
BASE_URL = "https://fisadisciplina.ase.ro/"
BASE_DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ASE_PDFs")
DATE_FORMAT = "%Y%m%d_%H%M%S"

# Create a folder for this specific run
RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
DOWNLOAD_DIR = os.path.join(BASE_DOWNLOAD_DIR, f"Run_{RUN_TIMESTAMP}")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ro-RO,ro;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Referer': BASE_URL
}

def setup_logging():
    """Setup logging"""
    # Create the run-specific directory
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    log_dir = os.path.join(DOWNLOAD_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"navigation_{RUN_TIMESTAMP}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def get_form_data(soup, form_selector=None):
    """Extract form data including hidden fields and viewstate"""
    form = soup.find('form') if not form_selector else soup.select_one(form_selector)
    if not form:
        return None, None
    
    action = form.get('action', '')
    if action.startswith('./'):
        action = action[2:]  # Remove './'
    action = urljoin(BASE_URL, action) if action else BASE_URL
    
    # Get all form inputs
    form_data = {}
    
    # Hidden inputs (including ViewState)
    for input_tag in form.find_all('input', type='hidden'):
        name = input_tag.get('name')
        value = input_tag.get('value', '')
        if name:
            form_data[name] = value
    
    # Regular inputs
    for input_tag in form.find_all('input', type=['text', 'submit', 'button']):
        name = input_tag.get('name')
        value = input_tag.get('value', '')
        if name:
            form_data[name] = value
    
    # Select dropdowns
    for select in form.find_all('select'):
        name = select.get('name')
        if name:
            # Get the first option as default, or look for selected
            selected = select.find('option', selected=True)
            if selected:
                form_data[name] = selected.get('value', '')
            else:
                first_option = select.find('option')
                if first_option:
                    form_data[name] = first_option.get('value', '')
    
    return action, form_data

def clean_filename(filename):
    """Clean filename to be Windows-compatible and extract Romanian-only subject name"""
    # Extract only Romanian part (before English translation)
    if '\n' in filename:
        # Split at newline (from HTML <br />)
        romanian_part = filename.split('\n')[0].strip()
    else:
        # Split at capital letter that indicates English translation
        romanian_match = re.match(r'^([^A-Z]*(?:[A-ZĂÂÎȘȚ][a-zăâîșț]*\s*)*[a-zăâîșț]+)', filename)
        if romanian_match:
            romanian_part = romanian_match.group(1).strip()
        else:
            # Alternative: split at common English translation patterns
            romanian_part = re.split(r'(?<=[a-zăâîșț])\s+(?=[A-Z][a-z])', filename)[0].strip()
    
    # Use the Romanian part if found, otherwise use the original
    clean_name = romanian_part if romanian_part and len(romanian_part) > 3 else filename
    
    # Clean for Windows filesystem
    clean_name = re.sub(r'[<>:"/\\|?*]', '_', clean_name)
    clean_name = re.sub(r'\s+', '_', clean_name)  # Replace spaces with underscores
    clean_name = clean_name.strip('._')  # Remove leading/trailing dots and underscores
    
    # Limit length to avoid path issues
    return clean_name[:80]

def is_subjects_page(soup, logger):
    """Check if we're actually on the subjects page (not year selection)"""
    # Look for download buttons - these only exist on the actual subjects page
    download_buttons = soup.find_all('input', type='image')
    ro_buttons = [btn for btn in download_buttons if 'ProgramaRO' in btn.get('onclick', '')]
    
    logger.info(f"Found {len(download_buttons)} download buttons, {len(ro_buttons)} Romanian PDF buttons")
    
    # Also check for semester headers
    semester_text = soup.get_text()
    has_semesters = 'Semestrul I' in semester_text or 'Semestrul II' in semester_text
    
    logger.info(f"Page contains semester information: {has_semesters}")
    
    # We're on the subjects page if we have download buttons AND semester info
    return len(ro_buttons) > 0 and has_semesters

def find_obligatory_pdfs(soup, logger):
    """Find PDFs marked as obligatory and get download parameters"""
    logger.info("Searching for obligatory PDFs...")
    
    # First verify we're on the right page
    if not is_subjects_page(soup, logger):
        logger.warning("This doesn't appear to be the subjects page - no download buttons found")
        return []
    
    pdf_downloads = []
    seen_subjects = set()  # Track subjects we've already found to avoid duplicates
    
    # Look for all download buttons with Romanian PDF links
    download_buttons = soup.find_all('input', type='image')
    ro_buttons = [btn for btn in download_buttons if 'ProgramaRO' in btn.get('onclick', '')]
    
    logger.info(f"Found {len(ro_buttons)} Romanian PDF download buttons")
    
    for button in ro_buttons:
        # Get the row containing this button
        row = button.find_parent('tr')
        if not row:
            continue
            
        # Check if this row contains an obligatory subject (marked with 'O')
        cells = row.find_all(['td', 'th'])
        is_obligatory = False
        subject_name = "Unknown_Subject"
        
        # Look for 'O' in the type column and extract subject name
        for i, cell in enumerate(cells):
            cell_text = cell.get_text(strip=True)
            
            # Check if this is the type column with 'O'
            if cell_text == 'O':
                is_obligatory = True
                
                # Get subject name from first cell (subject column)
                if len(cells) > 0:
                    subject_cell = cells[0]
                    full_text = subject_cell.get_text(strip=True)
                    
                    # Extract Romanian part - split at newline or common English patterns
                    if '\n' in full_text:
                        romanian_part = full_text.split('\n')[0].strip()
                    else:
                        # Split at patterns that indicate English translation
                        patterns = [
                            r'(?<=\w)\s+(?=[A-Z][a-z])',  # Split at word boundary before capital
                            'Design of', 'Mobile Devices', 'Web Technologies', 
                            'Software', 'Computer', 'Time Series', 'Economic',
                            'Quality', 'Sociology', 'Business Law'
                        ]
                        
                        romanian_part = full_text
                        for pattern in patterns:
                            if isinstance(pattern, str) and pattern in full_text:
                                romanian_part = full_text.split(pattern)[0].strip()
                                break
                            elif hasattr(pattern, 'pattern'):  # regex
                                split_result = re.split(pattern, full_text)
                                if len(split_result) > 1:
                                    romanian_part = split_result[0].strip()
                                    break
                    
                    if romanian_part and len(romanian_part) > 3:
                        subject_name = romanian_part
                    else:
                        subject_name = full_text[:50] if full_text else "Unknown_Subject"
                
                break
        
        if is_obligatory:
            # Clean subject name for deduplication
            clean_subject = re.sub(r'[^a-zA-ZăâîșțĂÂÎȘȚ\s]', '', subject_name).lower().strip()
            
            # Skip if we've already found this subject
            if clean_subject in seen_subjects:
                logger.info(f"Skipping duplicate subject: {subject_name}")
                continue
                
            seen_subjects.add(clean_subject)
            logger.info(f"Found obligatory subject: {subject_name}")
            
            # Extract download parameters from button onclick
            onclick = button.get('onclick', '')
            match = re.search(r"'([^']+)','([^']+)'", onclick)
            if match:
                target = match.group(1)
                argument = match.group(2)
                
                pdf_downloads.append({
                    'subject': subject_name,
                    'target': target,
                    'argument': argument,
                    'type': 'O'
                })
                
                logger.info(f"  Added download: {argument}")
    
    logger.info(f"Found {len(pdf_downloads)} unique obligatory subjects")
    return pdf_downloads

def download_pdfs(session, pdf_downloads, soup, logger):
    """Download all the PDFs by triggering the postback events"""
    logger.info(f"Starting download of {len(pdf_downloads)} PDFs...")
    
    successful_downloads = 0
    failed_downloads = 0
    
    for i, pdf_info in enumerate(pdf_downloads, 1):
        subject = clean_filename(pdf_info['subject'])
        target = pdf_info['target'] 
        argument = pdf_info['argument']
        
        logger.info(f"Downloading {i}/{len(pdf_downloads)}: {subject}")
        
        try:
            # Get current form data
            action, form_data = get_form_data(soup)
            if not action or not form_data:
                logger.error(f"Failed to get form data for {subject}")
                failed_downloads += 1
                continue
            
            # Update form data for this specific download
            form_data['__EVENTTARGET'] = target
            form_data['__EVENTARGUMENT'] = argument
            
            # Submit the form to trigger PDF download
            response = session.post(action, data=form_data)
            
            if response.status_code == 200:
                # Check if we got a PDF response
                content_type = response.headers.get('content-type', '').lower()
                
                if 'pdf' in content_type or response.content.startswith(b'%PDF'):
                    # Save the PDF with clean Romanian name only
                    timestamp = datetime.now().strftime(DATE_FORMAT)
                    
                    # Use the cleaned filename function
                    clean_subject = clean_filename(subject)
                    filename = f"{clean_subject}_{timestamp}.pdf"
                    filepath = os.path.join(DOWNLOAD_DIR, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    file_size = len(response.content)
                    logger.info(f"  SUCCESS: Saved {filename} ({file_size:,} bytes)")
                    successful_downloads += 1
                    
                else:
                    # Might be an HTML page, save for debugging
                    debug_file = os.path.join(DOWNLOAD_DIR, f"debug_{subject}_{i}.html")
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    logger.warning(f"  Got HTML instead of PDF, saved debug file: {debug_file}")
                    failed_downloads += 1
            else:
                logger.error(f"  HTTP {response.status_code} for {subject}")
                failed_downloads += 1
                
        except Exception as e:
            logger.error(f"  Error downloading {subject}: {e}")
            failed_downloads += 1
        
        # Be nice to the server
        time.sleep(2)
    
    return successful_downloads, failed_downloads

def navigate_to_subjects(session, logger):
    """Navigate through the forms to reach the subjects page"""
    
    # Step 1: Get the initial page
    logger.info("Step 1: Loading initial page...")
    response = session.get(BASE_URL)
    if response.status_code != 200:
        logger.error(f"Failed to load initial page: {response.status_code}")
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    logger.info("Initial page loaded successfully")
    
    # Step 2: Find and analyze the form
    action, form_data = get_form_data(soup)
    if not action:
        logger.error("No form found on initial page")
        return None
    
    logger.info(f"Form action: {action}")
    logger.info("Form fields found:")
    for key, value in form_data.items():
        logger.info(f"  {key}: {value}")
    
    # Step 3: Look for the Cybernetics faculty
    form = soup.find('form')
    if form:
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    text = cell.get_text(strip=True)
                    # Look for the Cybernetics faculty
                    if 'CIBERNETICĂ' in text or 'CYBERNETICS' in text.upper():
                        logger.info(f"Found target faculty: {text}")
                        
                        # Find the link in this row
                        link = row.find('a', href=True)
                        if link and 'doPostBack' in link.get('href', ''):
                            # Extract the postback parameters
                            href = link.get('href', '')
                            if 'plan$' in href:
                                match = re.search(r"'GridView1','(plan\$\d+)'", href)
                                if match:
                                    plan_param = match.group(1)
                                    logger.info(f"Found plan parameter: {plan_param}")
                                    
                                    # Update form data for postback
                                    form_data['__EVENTTARGET'] = 'GridView1'
                                    form_data['__EVENTARGUMENT'] = plan_param
                                    break
    
    # Step 4: Submit the form
    logger.info("\nStep 2: Submitting form...")
    
    # Add referer header
    session.headers['Referer'] = BASE_URL
    
    try:
        response = session.post(action, data=form_data)
        logger.info(f"Form submitted, status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse the new page
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Save page for debugging
            debug_file = os.path.join(DOWNLOAD_DIR, "step2_result.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"Page saved to: {debug_file}")
            
            # Look for more forms or the subjects table
            forms = soup.find_all('form')
            logger.info(f"Found {len(forms)} form(s) on result page")
            
            # Look for tables that might contain subjects
            tables = soup.find_all('table')
            logger.info(f"Found {len(tables)} table(s) on result page")
            
            # Check if we have PDF links yet
            pdf_links = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
            logger.info(f"Found {len(pdf_links)} PDF link(s)")
            
            # Check if we're on the subjects page or need to continue navigation
            if is_subjects_page(soup, logger):
                logger.info("SUCCESS: Found subjects page with download buttons!")
                return soup
            else:
                logger.info("Found program page - need to select Year III...")
                return navigate_further(session, soup, logger)
        else:
            logger.error(f"Form submission failed: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error during form submission: {e}")
        return None

def navigate_further(session, soup, logger):
    """Continue navigation to select the specific year"""
    logger.info("Step 3: Looking for Informatica Economics 2023-2026...")
    
    # Look for the specific program and year
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            
            # Check if this row contains our target program
            row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
            
            # Look for regular "Informatica economica" (not "Engleza" version) AND "2023-2026" AND "la frecvență"
            # Note: Check for both old (Ţ) and new (Ț) Romanian characters
            if ('Informatica economica' in row_text and '2023-2026' in row_text and 
                ('FRECVENȚĂ' in row_text.upper() or 'FRECVENŢĂ' in row_text.upper()) and
                'DISTANȚĂ' not in row_text.upper() and 'DISTANŢĂ' not in row_text.upper() and
                'ENGLEZA' not in row_text.upper() and 'ENGLISH' not in row_text.upper()):
                
                logger.info(f"Found target program: {row_text}")
                
                # Look for "Anul III" link in this row
                links = row.find_all('a', href=True)
                for link in links:
                    link_text = link.get_text(strip=True)
                    if 'Anul III' in link_text or 'trei' in link.get('href', ''):
                        href = link.get('href', '')
                        logger.info(f"Found Year III link: {href}")
                        
                        # Extract postback parameters
                        if 'doPostBack' in href:
                            match = re.search(r"'GridView1','(trei\$\d+)'", href)
                            if match:
                                target_param = match.group(1)
                                logger.info(f"Extracted parameter: {target_param}")
                                
                                # Get form data and update for postback
                                action, form_data = get_form_data(soup)
                                if action and form_data:
                                    form_data['__EVENTTARGET'] = 'GridView1'
                                    form_data['__EVENTARGUMENT'] = target_param
                                    
                                    # Submit the form
                                    try:
                                        response = session.post(action, data=form_data)
                                        logger.info(f"Year III selected, status: {response.status_code}")
                                        
                                        if response.status_code == 200:
                                            soup = BeautifulSoup(response.content, 'html.parser')
                                            
                                            # Save this page
                                            debug_file = os.path.join(DOWNLOAD_DIR, "year3_subjects.html")
                                            with open(debug_file, 'w', encoding='utf-8') as f:
                                                f.write(response.text)
                                            logger.info(f"Year 3 subjects page saved to: {debug_file}")
                                            
                                            return soup
                                        
                                    except Exception as e:
                                        logger.error(f"Error selecting Year III: {e}")
                                        
                                return soup
    
    logger.warning("Could not find Informatica Economics 2023-2026 program")
    return soup

def main():
    """Main execution"""
    print("ASE PDF Downloader - Full Navigation v1.0")
    print("=" * 50)
    print(f"Creating run folder: Run_{RUN_TIMESTAMP}")
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    logger = setup_logging()
    
    logger.info(f"Run folder created: {DOWNLOAD_DIR}")
    
    # Create session with persistent cookies
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Navigate to subjects page
    soup = navigate_to_subjects(session, logger)
    
    if not soup:
        logger.error("Failed to navigate to subjects page")
        return
    
    # Find obligatory PDFs
    pdf_downloads = find_obligatory_pdfs(soup, logger)
    
    if not pdf_downloads:
        logger.warning("No obligatory PDFs found")
        logger.info("Check the saved HTML files in the download directory for manual inspection")
        return
    
    logger.info(f"Found {len(pdf_downloads)} obligatory PDFs to download")
    
    # Download PDFs
    successful, failed = download_pdfs(session, pdf_downloads, soup, logger)
    
    # Summary
    logger.info("=" * 50)
    logger.info("Download Summary:")
    logger.info(f"Successful downloads: {successful}")
    logger.info(f"Failed downloads: {failed}")
    logger.info(f"Total PDFs processed: {len(pdf_downloads)}")
    logger.info(f"All files saved to: {DOWNLOAD_DIR}")
    
    print(f"\nDownload complete! Check {DOWNLOAD_DIR} for your files.")
    print(f"Structure:")
    print(f"   {DOWNLOAD_DIR}/")
    print(f"      [12 PDF files]")
    print(f"      logs/")
    print(f"         navigation_{RUN_TIMESTAMP}.log")
    print(f"      step2_result.html")
    print(f"      year3_subjects.html")
    print(f"Log files are in: {os.path.join(DOWNLOAD_DIR, 'logs')}")

if __name__ == "__main__":
    main()
