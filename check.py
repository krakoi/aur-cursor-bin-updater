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
        print("::debug::Sending request to get download link")
        response = requests.post(url, headers=headers, json=data)
        print(f"::debug::Request sent. Waiting for response...")
        print(f"::debug::Response status code: {response.status_code}")
        print(f"::debug::Response headers: {json.dumps(dict(response.headers), indent=2)}")
        
        content_length = int(response.headers.get('Content-Length', 0))
        print(f"::debug::Expected content length: {content_length} bytes")
        
        print("::debug::Starting to receive response content...")
        content = response.text
        print(f"::debug::Received content length: {len(content)} bytes")
        print(f"::debug::First 100 characters of content: {content[:100]}")
        
        print("::debug::Parsing JSON response...")
        response_json = response.json()
        print("::debug::JSON parsed successfully")
        
        download_url = response_json.get('cachedDownloadLink') or response_json.get('url')
        if not download_url:
            print("::error::Download URL not found in response")
        return download_url
    except requests.exceptions.RequestException as e:
        print(f"::error::Request failed: {str(e)}")
        return None

def get_local_pkgbuild_info():
    with open('PKGBUILD', 'r') as file:
        content = file.read()
    version_match = re.search(r'pkgver=([^\n]+)', content)
    rel_match = re.search(r'pkgrel=(\d+)', content)
    source_match = re.search(r'source_x86_64=\("([^"]+)"', content)
    if version_match and rel_match and source_match:
        return version_match.group(1).strip(), rel_match.group(1), source_match.group(1)
    else:
        print(f"::error::Unable to find current version, release, or source in local PKGBUILD")
        return None, None, None

try:
    # Check if DEBUG is set to true
    debug_mode = os.environ.get('DEBUG', '').lower() == 'true'

    # Get the download link
    download_link = get_download_link()
    if not download_link:
        raise ValueError("Failed to get download link")
    
    print(f"::debug::Download link: {download_link}")

    local_version, local_rel, local_source = get_local_pkgbuild_info()
    if local_version is None or local_rel is None or local_source is None:
        raise ValueError("Failed to get local version, release, or source")

    print(f"::debug::Local version: {local_version}, release: {local_rel}, source: {local_source}")

    # Extract version from download_link
    version_match = re.search(r'cursor-(\d+\.\d+\.\d+)', download_link)
    download_version = version_match.group(1) if version_match else None

    # Determine if update is needed
    update_needed = debug_mode or (download_version and download_version != local_version) or (download_link != local_source)

    # Determine new_version and new_rel
    if update_needed:
        new_version = download_version if download_version else local_version
        if new_version == local_version:
            new_rel = str(int(local_rel) + 1)
        else:
            new_rel = "1"
    else:
        new_version = local_version
        new_rel = local_rel

    print(f"::debug::New version: {new_version}, new release: {new_rel}")

    # Create output as JSON
    output = {
        "update_needed": update_needed,
        "local_version": local_version,
        "local_rel": local_rel,
        "local_source": local_source,
        "download_link": download_link,
        "new_version": new_version,
        "new_rel": new_rel
    }

    # Write JSON to file
    with open('check_output.json', 'w') as f:
        json.dump(output, f)

    print(f"::debug::Check output written to check_output.json")
    print(f"::debug::Final new_version: {new_version}, new_rel: {new_rel}")

except Exception as e:
    print(f"::error::Error in main execution: {str(e)}")
    sys.exit(1)