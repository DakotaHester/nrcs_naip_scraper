"""
NRCS NAIP Scraper

A Python package for downloading NAIP (National Agriculture Imagery Program) 
imagery data from the USDA NRCS Box folder. Provides functionality to download
data by year and state with automatic file organization and extraction.
"""

import json
import requests
import os
import re
import zipfile
from typing import List, Dict, Optional, Any
from tqdm import tqdm
from .utils import parse_json_response, extract_folders, extract_files, create_directory, validate_state_abbreviation, get_page_count, valid_states

# Constants
NAIP_ROOT_URL = 'https://nrcs.app.box.com/v/naip/folder/17936490251/'
NAIP_URL = 'https://nrcs.app.box.com/v/naip/folder/'
DOWNLOAD_URL = 'https://nrcs.app.box.com/index.php?rm=box_download_shared_file&vanity_name=naip&file_id=f_'


class NAIPScraper:
    """
    Main scraper class for downloading NAIP imagery data from NRCS Box folder.
    
    This class provides methods to download NAIP (National Agriculture Imagery Program)
    data organized by year and state. It supports downloading specific combinations
    or all available data, with automatic file organization and optional zip extraction.
    
    Attributes:
        base_url (str): Base URL for the NAIP Box folder
        output_dir (str): Directory where downloaded files will be saved
        unzip (bool): Whether to automatically extract zip files after download
        session (requests.Session): HTTP session for making requests
    """
    
    def __init__(self, base_url: str = "https://nrcs.app.box.com/v/naip", 
                 output_dir: str = "data", unzip: bool = True, 
                 overwrite: bool = False) -> None:
        """
        Initialize the NAIPScraper.
        
        Args:
            base_url: Base URL for the NAIP Box folder
            output_dir: Directory where downloaded files will be saved
            unzip: Whether to automatically extract zip files after download
            overwrite: Whether to overwrite existing files (default False)
        """
        self.base_url = base_url
        self.output_dir = output_dir
        self.unzip = unzip
        self.overwrite = overwrite
        self.session = requests.Session()
        
    def get_available_years(self, state: Optional[str] = None) -> List[int]:
        """
        Get list of available years from the NAIP Box folder.
        
        Args:
            state: Optional state abbreviation to filter years for that specific state.
                  If None, returns all available years across all states.
        
        Returns:
            List of available years sorted in descending order (most recent first).
            Returns empty list if no years found or on error.
            
        Raises:
            requests.RequestException: If HTTP request fails
            ValueError: If state abbreviation is invalid
        """
        try:
            # Get all years first (fast operation)
            page = 1
            
            years = []
            while True:
                response = self.session.get(NAIP_ROOT_URL + f'?page={page}')
                response.raise_for_status()
                data = parse_json_response(response)
                folders = extract_folders(data)
                
                for folder in folders:
                    try:
                        year = int(folder['name'])
                        years.append(year)
                    except ValueError:
                        continue
                
                if page >= get_page_count(data):
                    break
                page += 1
                
            # If no state filter, return all years
            if state is None:
                return sorted(years, reverse=True)
            
            # Validate state first
            state = validate_state_abbreviation(state)
            print(f"Getting available years for state {state}...")
            
            # Now filter years by checking each one (same as working download logic)
            available_years = []
            for year in years:
                try:
                    year_states = self.get_available_states(year)
                    # Case-insensitive state matching
                    if any(s.upper() == state.upper() for s in year_states):
                        available_years.append(year)
                except Exception:
                    continue
            
            return sorted(available_years, reverse=True)
            
        except Exception as e:
            print(f"Error getting available years: {e}")
            return []
    
    def get_available_states(self, year: Optional[int] = None) -> List[str]:
        """
        Get list of available states for a given year.
        
        Args:
            year: Year to get states for. If None, returns all states across all years.
            
        Returns:
            List of state abbreviations sorted alphabetically.
            Returns empty list if no states found or on error.
            
        Raises:
            requests.RequestException: If HTTP request fails
        """
        try:
            if year is None:
                # More efficient: get all years and collect unique states
                all_states = set()
                
                # Get all year folders
                response = self.session.get(NAIP_ROOT_URL)
                response.raise_for_status()
                data = parse_json_response(response)
                year_folders = extract_folders(data)
                
                # For each year, get the states
                for year_folder in year_folders:
                    try:
                        # Get all states for this year with proper pagination
                        page = 1
                        while True:
                            year_url = NAIP_URL + str(year_folder['id']) + f'?page={page}'
                            year_response = self.session.get(year_url)
                            year_response.raise_for_status()
                            year_data = parse_json_response(year_response)
                            state_folders = extract_folders(year_data)
                            
                            if not state_folders:  # No more data
                                break
                                
                            for state_folder in state_folders:
                                try:
                                    state_name = validate_state_abbreviation(state_folder['name'])
                                    if state_name in valid_states:
                                        all_states.add(state_name)
                                except Exception:
                                    # Add original name if validation fails
                                    all_states.add(state_folder['name'])
                            
                            # Check if we've reached the last page
                            if page >= year_data.get("pageCount", 1):
                                break
                            page += 1
                            
                    except Exception:
                        # If we can't process a year, continue with others
                        continue
                
                return sorted(list(all_states))
            
            # Original logic for specific year with improved pagination
            # Get year folder
            page = 1
            year_folder = None
            
            while True:
                response = self.session.get(NAIP_ROOT_URL + f'?page={page}')
                response.raise_for_status()
                data = parse_json_response(response)
                folders = extract_folders(data)
                
                year_folder = next((folder for folder in folders if folder['name'] == str(year)), None)
                if year_folder or page >= get_page_count(data):
                    break
                page += 1
            
            if not year_folder:
                print(f"No folder found for year {year}")
                return []
            
            # Get states in that year
            page = 1
            states = []
            while True:
                year_url = NAIP_URL + str(year_folder['id']) + str(f'?page={page}')
                response = self.session.get(year_url)
                response.raise_for_status()
                data = parse_json_response(response)
                state_folders = extract_folders(data)
                
                states.extend([folder['name'] for folder in state_folders])
                if page >= get_page_count(data):
                    break
                page += 1
            
            return sorted([state for state in states if state.upper() in valid_states])
            
        except Exception as e:
            print(f"Error getting available states for year {year}: {e}")
            return []
    
    def download_naip_data(self, year: Optional[int] = None, state: Optional[str] = None, 
                          output_dir: Optional[str] = None) -> None:
        """
        Download NAIP data for specified year and state.
        
        This is the main entry point for downloading data. Depending on the parameters
        provided, it will route to the appropriate specialized download method.
        
        Args:
            year: Year of data to download. If None, downloads all years.
            state: State abbreviation to download. If None, downloads all states.
            output_dir: Directory to save files. If None, uses instance output_dir.
            
        Examples:
            >>> scraper = NAIPScraper()
            >>> scraper.download_naip_data(2020, "NC")  # NC data for 2020
            >>> scraper.download_naip_data(2020, None)  # All states for 2020
            >>> scraper.download_naip_data(None, "NC")  # NC data for all years
            >>> scraper.download_naip_data(None, None)  # All data
        """
        if output_dir is None:
            output_dir = self.output_dir
            
        if year is None and state is None:
            return self.download_all_years_all_states(output_dir)
        elif year is None:
            return self.download_all_years_for_state(state, output_dir)
        elif state is None:
            return self.download_all_states(year, output_dir)
        else:
            return self.download_state_data(year, state, output_dir)
    
    def download_all_states(self, year: Optional[int] = None, output_dir: Optional[str] = None) -> None:
        """
        Download NAIP data for all available states for a given year.
        
        Args:
            year: Year to download data for. If None, downloads all years for all states.
            output_dir: Directory to save files. If None, uses instance output_dir.
        """
        if output_dir is None:
            output_dir = self.output_dir
            
        if year is None:
            return self.download_all_years_all_states(output_dir)
            
        print(f"Getting available states for year {year}...")
        available_states = self.get_available_states(year)
        
        if not available_states:
            print(f"No states found for year {year}")
            return
            
        print(f"Found {len(available_states)} states for year {year}: {', '.join(available_states)}")
        
        for state in available_states:
            try:
                print(f"\nDownloading data for {state} in {year}...")
                self.download_state_data(year, state, output_dir)
            except Exception as e:
                print(f"Error downloading data for {state}: {e}")
                continue
    
    def download_all_years_for_state(self, state: str, output_dir: Optional[str] = None) -> None:
        """
        Download NAIP data for all available years for a given state.
        
        Args:
            state: State abbreviation to download data for
            output_dir: Directory to save files. If None, uses instance output_dir.
            
        Raises:
            ValueError: If state abbreviation is invalid
        """
        if output_dir is None:
            output_dir = self.output_dir
            
        state = validate_state_abbreviation(state)
        print(f"Getting available years for state {state}...")
        available_years = self.get_available_years(state)
        
        if not available_years:
            print("No years found")
            return
            
        print(f"Found {len(available_years)} years: {', '.join(map(str, available_years))}")
        
        for year in available_years:
            try:
                # Check if state exists for this year
                year_states = self.get_available_states(year)
                if state not in year_states:
                    print(f"State {state} not available for year {year}")
                    continue
                    
                print(f"\nDownloading data for {state} in {year}...")
                self.download_state_data(year, state, output_dir)
            except Exception as e:
                print(f"Error downloading data for {state} in {year}: {e}")
                continue
    
    def download_all_years_all_states(self, output_dir: Optional[str] = None) -> None:
        """
        Download NAIP data for all available years and states.
        
        Warning: This can download a very large amount of data and take significant time.
        
        Args:
            output_dir: Directory to save files. If None, uses instance output_dir.
        """
        if output_dir is None:
            output_dir = self.output_dir
            
        print("Getting all available years...")
        available_years = self.get_available_years()
        
        if not available_years:
            print("No years found")
            return
            
        print(f"Found {len(available_years)} years: {', '.join(map(str, available_years))}")
        
        for year in available_years:
            try:
                print(f"\nProcessing year {year}...")
                self.download_all_states(year, output_dir)
            except Exception as e:
                print(f"Error processing year {year}: {e}")
                continue
    
    def download_state_data(self, year: int, state: str, output_dir: Optional[str] = None) -> None:
        """
        Download data for a specific year and state.
        
        Creates a directory structure: output_dir/year/state/composite_type/
        Downloads all files from available composite folders (prefers multispectral).
        
        Args:
            year: Year of data to download
            state: State abbreviation (will be validated)
            output_dir: Directory to save files. If None, uses instance output_dir.
            
        Raises:
            ValueError: If state abbreviation is invalid
            requests.RequestException: If HTTP requests fail
        """
        if output_dir is None:
            output_dir = self.output_dir
            
        state = validate_state_abbreviation(state)
        
        try:
            # Get year folder
            page = 1
            while True:
                response = self.session.get(NAIP_ROOT_URL)
                response.raise_for_status()
                data = parse_json_response(response)
                folders = extract_folders(data)
                
                year_folder = next((folder for folder in folders if folder['name'] == str(year)), None)
                if year_folder or page >= get_page_count(data):
                    break
                page += 1
            # If no year folder found, exit early
            if not year_folder:
                print(f"No folder found for year {year}")
                return
            
            # Get state folder
            page = 1
            while True:
                year_url = NAIP_URL + str(year_folder['id']) + f'?page={page}'
                response = self.session.get(year_url)
                response.raise_for_status()
                data = parse_json_response(response)
                state_folders = extract_folders(data)
                
                # Case-insensitive state matching
                state_folder = next((folder for folder in state_folders if folder['name'].upper() == state.upper()), None)
                if state_folder or page >= get_page_count(data):
                    break
                page += 1

            if not state_folder:
                print(f"No folder found for state {state} in year {year}")
                return
            
            # Get composite folders (prefer multispectral over 3-band)
            state_url = NAIP_URL + str(state_folder['id'])
            response = self.session.get(state_url)
            response.raise_for_status()
            data = parse_json_response(response)
            color_folders = extract_folders(data)
            
            composite_folders = []
            for folder in color_folders:
                folder_name = folder['name'].lower()
                state_lower = state.lower()
                
                # Prefer multispectral (4-band) over 3-band composites
                if state_lower + '_m' in folder_name:
                    composite_folders = [folder]
                    break
                
                if (state_lower + '_c' in folder_name or 
                    state_lower + '_n' in folder_name):
                    composite_folders.append(folder)
            
            if not composite_folders:
                print(f"No composite folders found for {state} in {year}")
                return
            
            # Create year-based directory structure
            year_dir = os.path.join(output_dir, str(year))
            state_dir = os.path.join(year_dir, state)
            create_directory(state_dir)
            
            # Download files from each composite folder
            for folder in composite_folders:
                # Create folder for each composite type (e.g., nc_m, wv_c, etc.)
                composite_dir = os.path.join(state_dir, folder['name'])
                create_directory(composite_dir)
                self._download_all_files_in_folder(folder, composite_dir)
                
        except Exception as e:
            print(f"Error downloading {state} data for {year}: {e}")
    
    def _download_all_files_in_folder(self, folder: Dict[str, Any], output_dir: str) -> None:
        """
        Download all files from a specific folder with progress tracking.
        
        Handles pagination to download all files in the folder. If unzip is enabled,
        automatically extracts zip files and removes the original zip.
        
        Args:
            folder: Dictionary containing folder information with keys 'id', 'name', 
                   'filesCount', and optionally 'parentFolderName'
            output_dir: Directory to save downloaded files
            
        Note:
            This method handles zip file extraction if self.unzip is True.
            Non-zip files or extraction failures will leave the original file intact.
        """
        folder_url = str(folder['id'])
        n_files = folder['filesCount']
        state = folder.get('parentFolderName', 'Unknown')
        
        if n_files == 0:
            print(f"No files found in folder {folder['name']}")
            return
        
        # Get year from first file
        try:
            test_response = self.session.get(NAIP_URL + folder_url + '?page=1')
            test_response.raise_for_status()
            test_data = parse_json_response(test_response)
            test_files = extract_files(test_data)
            
            if test_files:
                year_match = re.search(r'\d{4}', test_files[0]['name'])
                year = year_match.group(0) if year_match else 'Unknown'
            else:
                year = 'Unknown'
        except Exception:
            year = 'Unknown'
        
        desc_str = f"Downloading {year} {state.upper()} NAIP files"
        
        i = 0
        page = 1
        
        with tqdm(total=n_files, desc=desc_str, unit='file') as pbar:
            while i < n_files:
                try:
                    response = self.session.get(NAIP_URL + folder_url + f'?page={page}')
                    response.raise_for_status()
                    data = parse_json_response(response)
                    files = extract_files(data)
                    
                    if not files:  # No more files
                        break
                    
                    for file in files:
                        if i >= n_files:
                            break
                        
                        # overwrite logic:
                            
                        # first - if file folder already exists (without zip extension), skip
                        filepath = os.path.join(output_dir, file['name'])
                        folder_name = filepath.replace('.zip', '')  # Remove .zip for folder name
                        
                        # skip if the folder already exists
                        if not self.overwrite and os.path.exists(folder_name):
                            print(f"Folder {file['name']} already exists, skipping")
                            i += 1
                            pbar.update(1)
                            continue
                        
                        # Skip if the zip file already exists
                        if not self.overwrite and os.path.exists(filepath):
                            print(f"Zip file for {file['name']} already exists, skipping download")
                            i += 1
                            pbar.update(1)
                            continue
                        else:
                            pbar.set_postfix({'Current File': file['name']})
                            
                            # Download file
                            file_url = DOWNLOAD_URL + str(file['id'])
                            file_response = self.session.get(file_url)
                            file_response.raise_for_status()
                            
                            with open(filepath, 'wb') as f:
                                f.write(file_response.content)
                        
                        # Unzip file if enabled and it's a zip file
                        if self.unzip and filepath.lower().endswith('.zip'):
                            try:
                                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                                    zip_ref.extractall(folder_name)
                                # Delete the zip file after successful extraction
                                os.remove(filepath)
                            except zipfile.BadZipFile:
                                print(f"\nWarning: {file['name']} is not a valid zip file, keeping original")
                            except Exception as e:
                                print(f"\nWarning: Failed to extract {file['name']}: {e}")
                        
                        i += 1
                        pbar.update(1)
                    
                    page += 1
                    
                except Exception as e:
                    print(f"\nError downloading files from page {page}: {e}")
                    break