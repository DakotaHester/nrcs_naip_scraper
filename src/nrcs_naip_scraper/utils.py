import requests
import json
import os
from bs4 import BeautifulSoup
from urllib3 import HTTPResponse
from tqdm import tqdm


def parse_json_response(response: requests.Response) -> dict:
    """Parse JSON data from Box response."""
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')
    script = soup.find_all('script')[-1].string
    raw_json = script.split('Box.postStreamData = ', 1)[-1].rsplit(';', 1)[0]
    data = json.loads(raw_json)
    return data


def extract_folders(data: dict) -> list[dict]:
    """Extract folder items from parsed Box data."""
    folders = data['/app-api/enduserapp/shared-folder']['items']
    return [folder for folder in folders if folder['type'] == 'folder']


def extract_files(data: dict) -> list[dict]:
    """Extract file items from parsed Box data."""
    files = data['/app-api/enduserapp/shared-folder']['items']
    return [file for file in files if file['type'] == 'file']


def create_directory(directory: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(directory, exist_ok=True)


def validate_state_abbreviation(state: str) -> str:
    """Validate and normalize state abbreviation."""
    if not state:
        return None
    
    state_upper = state.upper()
    if state_upper in valid_states:
        return state_upper
    
    return state  # Return as-is if not in our validation list


def get_page_count(data: dict) -> int:
    """Get the total number of pages from the Box data."""
    return data.get('/app-api/enduserapp/shared-folder', {}).get("pageCount", 1)


# https://stackoverflow.com/a/16696317
def download_file(response: requests.Response, filepath: str, chunk_size: int = 1048576) -> None:
    """Download a file from a requests response and save it to the specified filepath.

    Args:
        response (requests.Response): The response object from a requests call that contains the file to be downloaded.
        filepath (str): The path where the downloaded file will be saved.
        chunk_size (int, optional): The size of each chunk to read from the response in bytes. Defaults to 1048576 (1 MB).
    """
    if isinstance(response.raw, HTTPResponse):
        content_length = response.headers.get('Content-Length')
        total_size = int(content_length) if content_length else None
        
        with open(filepath, 'wb') as f:
            with tqdm(
                total=total_size,
                desc=f"Downloading {os.path.basename(filepath).replace('.PART', '')}",
                unit='B',
                unit_scale=True,
                unit_divisor=1024,  # Standard binary divisor for KB/MB/GB
                disable=total_size is None,  # Disable if we don't know the size
                leave=False,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
                        pbar.update(len(chunk))
    
    else:
        with open(filepath, 'wb') as f:
            f.write(response.content)



valid_states = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
}