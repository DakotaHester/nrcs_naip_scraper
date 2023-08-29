from bs4 import BeautifulSoup
import requests
import re
import html5lib
import json

def main():
    
    NAIP_ROOT_URL = 'https://nrcs.app.box.com/v/naip/folder/17936490251/'
    NAIP_URL = 'https://nrcs.app.box.com/v/naip/folder/'
    
    desired_year = 2021
    desired_state = 'MS'
    desired_counties = ['']
    
    # Get the HTML content of the NAIP_ROOT_URL
    response = requests.get(NAIP_ROOT_URL)
    folders = get_fodlers_from_response(response)
    for folder in folders:
        if folder['name'] == str(desired_year):
            year_folder = folder
            year_url = str(year_folder['id'])
            break
        
    response = requests.get(NAIP_URL + year_url)
    year_folders = get_fodlers_from_response(response)
    print(year_folders)
    
    for state in year_folders:
        if state['name'] == desired_state:
            state_folder = state
            state_url = str(state_folder['id'])
            break
    
    print(state_url)
    response = requests.get(NAIP_URL + state_url)
    composite_folder_urls = []
    for color_folders in get_fodlers_from_response(response):
        if (desired_state.lower() + '_c' in color_folders['name'].lower() or \
            desired_state.lower() + '_n' in color_folders['name'].lower()) and \
            color_folders['type'] == 'folder':
            composite_folder_urls.append(color_folders['id'])
        n_files = color_folders['num_items']
    
    print(composite_folder_urls)
    for id in composite_folder_urls:
        n_files = 
        i = 1
        response = requests.get(NAIP_URL + str(id))
        
        # https://stackoverflow.com/a/21069605
        soup = BeautifulSoup(response.content, 'html.parser')
        script = soup.find_all('script')[-1].string
        print(script)
        raw_json = script.split('Box.postStreamData = ', 1)[-1].rsplit(';', 1)[0]
        data = json.loads(raw_json)
        files = data['/app-api/enduserapp/shared-folder']['items']
        
        print(files)
        print(len(files))
        break
        
    # print(json.dumps(data['/app-api/enduserapp/shared-folder'], sort_keys=True, indent=4))
    
def get_fodlers_from_response(response):
    html = response.content
    
    # https://stackoverflow.com/a/21069605
    soup = BeautifulSoup(html, 'html.parser')
    script = soup.find_all('script')[-1].string
    raw_json = script.split('Box.postStreamData = ', 1)[-1].rsplit(';', 1)[0]
    data = json.loads(raw_json)
    folders = data['/app-api/enduserapp/shared-folder']['items']
    for folder in folders:
        if folder['type'] != 'folder':
            folders.remove(folder)
    return folders



if __name__ == '__main__':
    main()