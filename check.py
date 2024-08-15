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
            raise ValueError("Unable to extract version from Content-Disposition header")

def get_local_pkgbuild_info():
    with open('PKGBUILD', 'r') as file:
        content = file.read()
    version_match = re.search(r'pkgver=(\d+\.\d+\.\d+)', content)
    rel_match = re.search(r'pkgrel=(\d+)', content)
    if version_match and rel_match:
        return version_match.group(1), rel_match.group(1)
    else:
        raise ValueError("Unable to find current version or release in local PKGBUILD")

def get_aur_version(url):
    response = requests.get(url)
    response.raise_for_status()
    pkgbuild_content = response.text
    version_match = re.search(r'pkgver=(\d+\.\d+\.\d+)', pkgbuild_content)
    rel_match = re.search(r'pkgrel=(\d+)', pkgbuild_content)
    if version_match and rel_match:
        return version_match.group(1), rel_match.group(1)
    else:
        raise ValueError("Unable to find current version or release in AUR PKGBUILD")

url = 'https://downloader.cursor.sh/linux/appImage/x64'
aur_url = 'https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=cursor-bin'

try:
    latest_version = get_latest_version(url)
    aur_version, aur_rel = get_aur_version(aur_url)
    local_version, local_rel = get_local_pkgbuild_info()
except Exception as e:
    print(f"Error: {str(e)}")
    exit(1)

# Compare versions and release numbers
print(f"Debug: latest_version={latest_version}, aur_version={aur_version}, local_rel={local_rel}, aur_rel={aur_rel}", file=sys.stderr)

if version.parse(latest_version) > version.parse(aur_version) or int(local_rel) > int(aur_rel):
    print(f"Debug: Update needed. Reason: {'New version' if version.parse(latest_version) > version.parse(aur_version) else 'Higher local release'}", file=sys.stderr)
    # If the latest version is newer than the AUR version,
    # or if the local release number is higher than the AUR release number
    print(f'::set-output name=update_needed::true')
    print(f'::set-output name=latest_version::{latest_version}')
else:
    print("Debug: No update needed.", file=sys.stderr)
    # If the AUR version is up-to-date and the local release number is not higher
    print(f'::set-output name=update_needed::false')

print(f"Debug: Comparison results: latest > aur = {version.parse(latest_version) > version.parse(aur_version)}, local_rel > aur_rel = {int(local_rel) > int(aur_rel)}", file=sys.stderr)