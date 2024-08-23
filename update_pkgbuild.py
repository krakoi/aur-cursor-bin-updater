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

def update_pkgbuild(latest_version, current_version, current_rel):
    debug_print(f"Updating PKGBUILD from version {current_version} to {latest_version}")

    # Read the current PKGBUILD
    with open('PKGBUILD', 'r') as f:
        pkgbuild = f.read()

    # Update pkgver
    pkgbuild = re.sub(r'pkgver=.*', f'pkgver={latest_version}', pkgbuild)

    # Update pkgrel only if version has changed
    if latest_version != current_version:
        pkgbuild = re.sub(r'pkgrel=\d+', 'pkgrel=1', pkgbuild)
    else:
        debug_print("Version unchanged, pkgrel not updated")

    debug_print(f"Downloading AppImage for version {latest_version}")
    # Download new AppImage
    subprocess.run(['wget', '-O', f'cursor-{latest_version}.AppImage', 'https://downloader.cursor.sh/linux/appImage/x64'], check=True)

    # Calculate new SHA256
    with open(f'cursor-{latest_version}.AppImage', 'rb') as f:
        new_sha256 = hashlib.sha256(f.read()).hexdigest()
    debug_print(f"New SHA256: {new_sha256}")

    # Update source URL in PKGBUILD to point to our repository
    artifact_url = f"https://github.com/Gunther-Schulz/aur-cursor-bin-updater/releases/download/v${{pkgver}}/cursor-${{pkgver}}.AppImage"
    debug_print(f"New artifact URL: {artifact_url}")
    
    # Update source_x86_64
    source_pattern = r'source_x86_64=\([^)]+\)'
    new_source = f'source_x86_64=("{artifact_url}" "cursor.png")'
    pkgbuild = re.sub(source_pattern, new_source, pkgbuild)

    # Update sha256sums_x86_64
    sha256_pattern = r'sha256sums_x86_64=\([^)]+\)'
    new_sha256sums = f"sha256sums_x86_64=('{new_sha256}' 'SKIP')"
    pkgbuild = re.sub(sha256_pattern, new_sha256sums, pkgbuild)

    # Write updated PKGBUILD
    with open('PKGBUILD', 'w') as f:
        f.write(pkgbuild)

    debug_print(f"PKGBUILD updated to version {latest_version} with SHA256 {new_sha256}")
    debug_print(f"AppImage file saved as cursor-{latest_version}.AppImage")

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
            check_output["latest_version"],
            check_output["current_version"],
            check_output["current_rel"]
        )
    else:
        print("No update needed.")