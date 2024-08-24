import sys
import re
import subprocess
import hashlib
import json
import os

DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def update_pkgbuild(pkgbuild, json_data):
    download_link = json_data['download_link']
    new_version = json_data['new_version']
    new_rel = json_data['new_rel']

    # Update pkgver
    pkgbuild = re.sub(r'pkgver=.*', f'pkgver={new_version}', pkgbuild)

    # Update pkgrel
    pkgbuild = re.sub(r'pkgrel=\d+', f'pkgrel={new_rel}', pkgbuild)

    # Update source
    pkgbuild = re.sub(r'source=\(".*"\)', f'source=("{download_link}")', pkgbuild)

    # Update sha256sums
    sha256sum = calculate_sha256(download_link)
    pkgbuild = re.sub(r'sha256sums=\(".*"\)', f'sha256sums=("{sha256sum}")', pkgbuild)

    return pkgbuild

def calculate_sha256(download_link):
    appimage_filename = os.path.basename(download_link)
    debug_print(f"Downloading file: {appimage_filename}")
    subprocess.run(['wget', '-O', appimage_filename, download_link], check=True)

    debug_print("Calculating SHA256 sum")
    with open(appimage_filename, 'rb') as f:
        new_sha256 = hashlib.sha256(f.read()).hexdigest()
    debug_print(f"SHA256 sum: {new_sha256}")
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
        debug_print(f"PKGBUILD updated to version {check_output['new_version']} (release {check_output['new_rel']}) with new download link")
    else:
        print("No update needed.")