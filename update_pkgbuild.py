import sys
import re
import subprocess
import hashlib
import json

def update_pkgbuild(latest_version, current_version, current_rel):
    # Read the current PKGBUILD
    with open('PKGBUILD', 'r') as f:
        pkgbuild = f.read()

    # Update pkgver
    pkgbuild = re.sub(r'pkgver=.*', f'pkgver={latest_version}', pkgbuild)

    # Update pkgrel
    new_rel = 1 if latest_version != current_version else int(current_rel) + 1
    pkgbuild = re.sub(r'pkgrel=\d+', f'pkgrel={new_rel}', pkgbuild)

    # Download new AppImage
    subprocess.run(['wget', '-O', f'cursor-{latest_version}.AppImage', 'https://downloader.cursor.sh/linux/appImage/x64'], check=True)

    # Calculate new SHA256
    with open(f'cursor-{latest_version}.AppImage', 'rb') as f:
        new_sha256 = hashlib.sha256(f.read()).hexdigest()

    # Update SHA256 in PKGBUILD
    pkgbuild = re.sub(r"sha256sums_x86_64=\('.*?'\)", f"sha256sums_x86_64=('{new_sha256}')", pkgbuild)

    # Write updated PKGBUILD
    with open('PKGBUILD', 'w') as f:
        f.write(pkgbuild)

    # Clean up downloaded file
    subprocess.run(['rm', f'cursor-{latest_version}.AppImage'], check=True)

    print(f"PKGBUILD updated to version {latest_version} with SHA256 {new_sha256}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_pkgbuild.py <check_output_file>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        check_output = json.load(f)
    
    if check_output["update_needed"]:
        update_pkgbuild(
            check_output["latest_version"],
            check_output["current_version"],
            check_output["current_rel"]
        )
    else:
        print("No update needed.")