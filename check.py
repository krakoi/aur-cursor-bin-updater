#!/usr/bin/env python
import requests
import re

def get_latest_version(url):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'}
    
    with requests.get(url, headers=headers, stream=True) as response:
        response.raise_for_status()
        content_disposition = response.headers.get('Content-Disposition', '')
        
        version_match = re.search(r'filename="cursor-(\d+\.\d+\.\d+).*\.AppImage"', content_disposition)
        if version_match:
            return version_match.group(1)
        else:
            raise ValueError("Unable to extract version from Content-Disposition header")

url = 'https://downloader.cursor.sh/linux/appImage/x64'
try:
    latest_version = get_latest_version(url)
except Exception as e:
    print(f"Error: {str(e)}")
    exit(1)

with open('PKGBUILD', 'r') as file:
    pkgbuild = file.read()

current_version_match = re.search(r'pkgver=(\d+\.\d+\.\d+)', pkgbuild)
if current_version_match:
    current_version = current_version_match.group(1)
else:
    print("Error: Unable to find current version in PKGBUILD")
    exit(1)

if latest_version != current_version:
    print(f'update_needed=true')
    print(f'latest_version={latest_version}')
else:
    print(f'update_needed=false')