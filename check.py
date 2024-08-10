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

def get_aur_version(url):
    response = requests.get(url)
    response.raise_for_status()
    pkgbuild_content = response.text
    version_match = re.search(r'pkgver=(\d+\.\d+\.\d+)', pkgbuild_content)
    if version_match:
        return version_match.group(1)
    else:
        raise ValueError("Unable to find current version in AUR PKGBUILD")

url = 'https://downloader.cursor.sh/linux/appImage/x64'
aur_url = 'https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=cursor-bin'

try:
    latest_version = get_latest_version(url)
    aur_version = get_aur_version(aur_url)
except Exception as e:
    print(f"Error: {str(e)}")
    exit(1)

if latest_version != aur_version:
    print(f'update_needed=true')
    print(f'latest_version={latest_version}')
else:
    print(f'update_needed=false')