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

def update_pkgbuild(download_link, current_version, current_rel):
    debug_print(f"Updating PKGBUILD with new download link: {download_link}")

    # Read the current PKGBUILD
    with open('PKGBUILD', 'r') as f:
        pkgbuild = f.read()

    # Extract version from download_link
    version_match = re.search(r'cursor-(\d+\.\d+\.\d+)', download_link)
    if not version_match:
        raise ValueError(f"Unable to extract version from download link: {download_link}")
    latest_version = version_match.group(1)

    # Update pkgver
    pkgbuild = re.sub(r'pkgver=.*', f'pkgver={latest_version}', pkgbuild)

    # Reset pkgrel to 1 since we have a new version
    pkgbuild = re.sub(r'pkgrel=\d+', 'pkgrel=1', pkgbuild)

    debug_print(f"Downloading AppImage from {download_link}")
    # Download new AppImage
    appimage_filename = os.path.basename(download_link)
    subprocess.run(['wget', '-O', appimage_filename, download_link], check=True)

    # Calculate new SHA256
    with open(appimage_filename, 'rb') as f:
        new_sha256 = hashlib.sha256(f.read()).hexdigest()
    debug_print(f"New SHA256: {new_sha256}")

    # Update source_x86_64
    source_pattern = r'source_x86_64=\([^)]+\)'
    new_source = f'source_x86_64=("{download_link}" "cursor.png")'
    pkgbuild = re.sub(source_pattern, new_source, pkgbuild)

    # Update sha256sums_x86_64
    sha256_pattern = r'sha256sums_x86_64=\([^)]+\)'
    new_sha256sums = f"sha256sums_x86_64=('{new_sha256}' 'SKIP')"
    pkgbuild = re.sub(sha256_pattern, new_sha256sums, pkgbuild)

    # Write updated PKGBUILD
    with open('PKGBUILD', 'w') as f:
        f.write(pkgbuild)

    debug_print(f"PKGBUILD updated to version {latest_version} with SHA256 {new_sha256}")
    debug_print(f"AppImage file saved as {appimage_filename}")

    debug_print("\nFinal PKGBUILD content:")
    debug_print(pkgbuild)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_pkgbuild.py <check_output_file>")
        sys.exit(1)
    
    debug_print(f"Reading check output from {sys.argv[1]}")
    with open(sys.argv[1], 'r') as f:
        check_output = json.load(f)
    
    debug_print(f"Check output content: {json.dumps(check_output, indent=2)}")
    
    if check_output["update_needed"]:
        debug_print("Update needed, calling update_pkgbuild()")
        update_pkgbuild(
            check_output["download_link"],
            check_output["current_version"],
            check_output["current_rel"]
        )
    else:
        print("No update needed.")