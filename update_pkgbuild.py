import sys
import re
import subprocess
import hashlib
import json
import os
from packaging import version

DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def update_pkgbuild(pkgbuild, json_data):
    download_link = json_data['download_link']
    aur_source = json_data['aur_source']
    aur_rel = int(json_data['aur_rel'])

    # Extract version from download_link
    version_match = re.search(r'cursor-(\d+\.\d+\.\d+)', download_link)
    if not version_match:
        raise ValueError(f"Unable to extract version from download link: {download_link}")
    latest_version = version_match.group(1)

    # Update pkgver
    pkgbuild = re.sub(r'pkgver=.*', f'pkgver={latest_version}', pkgbuild)

    # Reset pkgrel to 1 if download_link and aur_source are different
    if download_link != aur_source:
        new_pkgrel = 1
    else:
        # Increment pkgrel
        new_pkgrel = aur_rel + 1

    # Update pkgrel in PKGBUILD
    pkgbuild = re.sub(r'pkgrel=\d+', f'pkgrel={new_pkgrel}', pkgbuild)

    # Update source
    pkgbuild = re.sub(r'source=\(".*"\)', f'source=("{download_link}")', pkgbuild)

    # Update sha256sums
    sha256sum = calculate_sha256(download_link)
    pkgbuild = re.sub(r'sha256sums=\(".*"\)', f'sha256sums=("{sha256sum}")', pkgbuild)

    return pkgbuild

def calculate_sha256(download_link):
    appimage_filename = os.path.basename(download_link)
    subprocess.run(['wget', '-O', appimage_filename, download_link], check=True)

    with open(appimage_filename, 'rb') as f:
        new_sha256 = hashlib.sha256(f.read()).hexdigest()
    return new_sha256

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_pkgbuild.py <check_output_file>")
        sys.exit(1)
    
    debug_print(f"Reading check output from {sys.argv[1]}")
    with open(sys.argv[1], 'r') as f:
        check_output = json.load(f)
    
    debug_print(f"Check output content: {json.dumps(check_output, indent=2)}")
    
    if check_output["update_needed"]:
        debug_print("Update needed, reading current PKGBUILD")
        with open('PKGBUILD', 'r') as f:
            current_pkgbuild = f.read()
        
        debug_print("Calling update_pkgbuild()")
        updated_pkgbuild = update_pkgbuild(current_pkgbuild, check_output)
        
        with open('PKGBUILD', 'w') as f:
            f.write(updated_pkgbuild)
        debug_print(f"PKGBUILD updated to version {check_output['aur_version']} with new download link")
    else:
        print("No update needed.")