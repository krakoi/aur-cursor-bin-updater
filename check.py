#!/usr/bin/env python
import requests
import re
from packaging import version
import sys

def get_latest_version(url):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'}
    
    with requests.get(url, headers=headers, stream=True) as response:
        response.raise_for_status()
        content_disposition = response.headers.get('Content-Disposition', '')
        
        version_match = re.search(r'filename="cursor-(\d+\.\d+\.\d+).*\.AppImage"', content_disposition)
        if version_match:
            return version_match.group(1)
        else:
            print(f"::error::Unable to extract version from Content-Disposition header: {content_disposition}")
            return None

def get_local_pkgbuild_info():
    with open('PKGBUILD', 'r') as file:
        content = file.read()
    version_match = re.search(r'pkgver=(\d+\.\d+\.\d+)', content)
    rel_match = re.search(r'pkgrel=(\d+)', content)
    if version_match and rel_match:
        return version_match.group(1), rel_match.group(1)
    else:
        print(f"::error::Unable to find current version or release in local PKGBUILD")
        return None, None

def get_aur_version(url):
    response = requests.get(url)
    response.raise_for_status()
    pkgbuild_content = response.text
    version_match = re.search(r'pkgver=(\d+\.\d+\.\d+)', pkgbuild_content)
    rel_match = re.search(r'pkgrel=(\d+)', pkgbuild_content)
    if version_match and rel_match:
        return version_match.group(1), rel_match.group(1)
    else:
        print(f"::error::Unable to find current version or release in AUR PKGBUILD")
        return None, None

url = 'https://downloader.cursor.sh/linux/appImage/x64'
aur_url = 'https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=cursor-bin'

try:
    latest_version = get_latest_version(url)
    if latest_version is None:
        raise ValueError("Failed to get latest version")
    
    aur_version, aur_rel = get_aur_version(aur_url)
    if aur_version is None or aur_rel is None:
        raise ValueError("Failed to get AUR version or release")
    
    local_version, local_rel = get_local_pkgbuild_info()
    if local_version is None or local_rel is None:
        raise ValueError("Failed to get local version or release")

    print(f"::debug::Latest version: {latest_version}")
    print(f"::debug::AUR version: {aur_version}, release: {aur_rel}")
    print(f"::debug::Local version: {local_version}, release: {local_rel}")

    if version.parse(latest_version) > version.parse(aur_version) or int(local_rel) > int(aur_rel):
        print(f'update_needed=true')
        print(f'latest_version={latest_version}')
    else:
        print(f'update_needed=false')
        print(f'latest_version={latest_version}')

except Exception as e:
    print(f"::error::Error in main execution: {str(e)}")
    sys.exit(1)