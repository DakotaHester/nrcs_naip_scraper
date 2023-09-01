from bs4 import BeautifulSoup
import requests
import json
import os

NAIP_ROOT_URL = 'https://nrcs.app.box.com/v/naip/folder/17936490251/'
NAIP_URL = 'https://nrcs.app.box.com/v/naip/folder/'
DOWNLOAD_URL = 'https://nrcs.app.box.com/index.php?rm=box_download_shared_file&vanity_name=naip&file_id=f_'

def main() -> None:
    
    desired_year = 2021
    desired_state = 'MS'
    # desired_counties = ['']
    out_dir = 'data'
    
    # Get the HTML content of the NAIP_ROOT_URL
    response = requests.get(NAIP_ROOT_URL)
    folders = get_folders_from_response(response)
    for folder in folders:
        if folder['name'] == str(desired_year):
            year_folder = folder
            year_url = str(year_folder['id'])
            break
        
    response = requests.get(NAIP_URL + year_url)
    year_folders = get_folders_from_response(response)
    
    for state in year_folders:
        if state['name'] == desired_state:
            state_folder = state
            state_url = str(state_folder['id'])
            break
    
    response = requests.get(NAIP_URL + state_url)
    composite_folders = []
    for color_folders in get_folders_from_response(response):
        if (desired_state.lower() + '_c' in color_folders['name'].lower() or \
            desired_state.lower() + '_n' in color_folders['name'].lower()) and \
            color_folders['type'] == 'folder':
            composite_folders.append(color_folders)
    
    os.makedirs(out_dir, exist_ok=True)
    for color_folder in composite_folders:
        dowload_all_files_in_folder(color_folder, out_dir)

def get_json_from_response(response: requests.Response) -> dict:
    html = response.content
    # https://stackoverflow.com/a/21069605
    soup = BeautifulSoup(html, 'html.parser')
    script = soup.find_all('script')[-1].string
    raw_json = script.split('Box.postStreamData = ', 1)[-1].rsplit(';', 1)[0]
    data = json.loads(raw_json)
    return data

def get_folders_from_response(response: requests.Response) -> list[dict]:
    data = get_json_from_response(response)
    folders = data['/app-api/enduserapp/shared-folder']['items']
    for folder in folders:
        if folder['type'] != 'folder':
            folders.remove(folder)
    return folders

def get_files_from_response(response: requests.Response) -> list[dict]:
    data = get_json_from_response(response)
    files = data['/app-api/enduserapp/shared-folder']['items']
    for file in files:
        if file['type'] != 'file':
            files.remove(file)
    return files

def dowload_all_files_in_folder(folder: dict, out_dir: str) -> None:
    folder_url = str(folder['id'])
    n_files = folder['filesCount']
    i = 0
    page = 1
    while i < n_files:
        response = requests.get(NAIP_URL + folder_url + f'?page={page}')
        files = get_files_from_response(response)
        for file in files:
            print_dict(file)
            filepath = os.path.join(out_dir, file['name'])
            with open(filepath, 'wb') as f:
                f.write(requests.get(DOWNLOAD_URL + str(file['id'])))
            i+=1
        page+=1

def print_dict(d: dict) -> None:
    print(json.dumps(d, sort_keys=True, indent=4))


if __name__ == '__main__':
    main()