import requests
import json
import os
from bs4 import BeautifulSoup


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

valid_states = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
}