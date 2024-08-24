#!/usr/bin/env python
import requests
import re
import sys
import os
import json

def get_download_link():
    url = 'https://www.cursor.com/api/dashboard/get-download-link'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.7',
        'Origin': 'https://www.cursor.com',
        'Referer': 'https://www.cursor.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        'DNT': '1'
    }
    data = {"platform": 5}  # Correct payload
    
    print("::debug::Sending request to get download link")
    print(f"::debug::URL: {url}")
    print(f"::debug::Headers: {json.dumps(headers, indent=2)}")
    print(f"::debug::Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"::debug::Response status code: {response.status_code}")
        print(f"::debug::Response headers: {json.dumps(dict(response.headers), indent=2)}")
        print(f"::debug::Response content: {response.text}")
        
        response.raise_for_status()
        response_json = response.json()
        download_url = response_json.get('cachedDownloadLink') or response_json.get('url')
        if not download_url:
            print("::error::Download URL not found in response")
        return download_url
    except requests.exceptions.RequestException as e:
        print(f"::error::Request failed: {str(e)}")
        return None

def get_aur_pkgbuild_info(url):
    response = requests.get(url)
    response.raise_for_status()
    pkgbuild_content = response.text
    
    version_match = re.search(r'pkgver=([^\n]+)', pkgbuild_content)
    rel_match = re.search(r'pkgrel=(\d+)', pkgbuild_content)
    source_match = re.search(r'source_x86_64=\("([^"]+)"', pkgbuild_content)
    
    if version_match and rel_match and source_match:
        version = version_match.group(1).strip()
        rel = rel_match.group(1)
        source = source_match.group(1)
        
        # Replace ${pkgver} with actual version in the source URL
        source = source.replace('${pkgver}', version)
        
        return version, rel, source
    else:
        print(f"::error::Unable to find current version, release, or source in AUR PKGBUILD")
        return None, None, None

def get_local_pkgbuild_info():
    with open('PKGBUILD', 'r') as file:
        content = file.read()
    version_match = re.search(r'pkgver=([^\n]+)', content)
    rel_match = re.search(r'pkgrel=(\d+)', content)
    if version_match and rel_match:
        return version_match.group(1).strip(), rel_match.group(1)
    else:
        print(f"::error::Unable to find current version or release in local PKGBUILD")
        return None, None

aur_url = 'https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=cursor-bin'

try:
    # Check if DEBUG is set to true
    debug_mode = os.environ.get('DEBUG', '').lower() == 'true'

    # Step 1: Get the download link
    download_link = get_download_link()
    if not download_link:
        raise ValueError("Failed to get download link")
    
    print(f"::debug::Download link: {download_link}")

    aur_version, aur_rel, aur_source = get_aur_pkgbuild_info(aur_url)
    if aur_version is None or aur_rel is None or aur_source is None:
        raise ValueError("Failed to get AUR version, release, or source")
    
    local_version, local_rel = get_local_pkgbuild_info()
    if local_version is None or local_rel is None:
        raise ValueError("Failed to get local version or release")

    print(f"::debug::AUR version: {aur_version}, release: {aur_rel}")
    print(f"::debug::AUR source: {aur_source}")
    print(f"::debug::Local version: {local_version}, release: {local_rel}")

    update_needed = debug_mode or download_link != aur_source or int(local_rel) > int(aur_rel)

    # Create output as JSON
    output = {
        "update_needed": update_needed,
        "current_version": local_version,
        "current_rel": local_rel,
        "aur_version": aur_version,
        "aur_rel": aur_rel,
        "download_link": download_link,
        "aur_source": aur_source
    }

    # Write JSON to file
    with open('check_output.json', 'w') as f:
        json.dump(output, f)

    print(f"::debug::Check output written to check_output.json")

except Exception as e:
    print(f"::error::Error in main execution: {str(e)}")
    sys.exit(1)