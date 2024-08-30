import sys
import re
import hashlib
import json
import os
import requests

DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url, filename):
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)

def update_pkgbuild(pkgbuild, json_data):
    download_link = json_data['download_link']
    new_version = json_data['new_version']
    new_rel = json_data['new_rel']
    download_sha512 = json_data['download_sha512']

    # Update pkgver
    pkgbuild = re.sub(r'pkgver=.*', f'pkgver={new_version}', pkgbuild)

    # Update pkgrel
    pkgbuild = re.sub(r'pkgrel=\d+', f'pkgrel={new_rel}', pkgbuild)

    # Update source_x86_64 and add cursor.png
    pkgbuild = re.sub(r'source_x86_64=\(".*"', f'source_x86_64=("{download_link}" "cursor.png"', pkgbuild)

    # Update noextract
    pkgbuild = re.sub(r'noextract=\(".*"\)', 'noextract=("$(basename ${source_x86_64[0]})")', pkgbuild)

    # Update sha512sums_x86_64
    pkgbuild = re.sub(r'sha512sums_x86_64=\(.*\)', f"sha512sums_x86_64=('{download_sha512}' 'SKIP')", pkgbuild)

    # Replace the entire package() function
    new_package_function = r'''
package() {
    install -Dm755 "${srcdir}/$(basename ${source_x86_64[0]})" "${pkgdir}/opt/${pkgname}/${pkgname}.AppImage"

    # Symlink executable to be called 'cursor'
    mkdir -p "${pkgdir}/usr/bin"
    ln -s "/opt/${pkgname}/${pkgname}.AppImage" "${pkgdir}/usr/bin/cursor"

    # Install the icon
    install -Dm644 "${srcdir}/cursor.png" "${pkgdir}/usr/share/icons/hicolor/512x512/apps/cursor.png"

    # Create a .desktop Entry
    mkdir -p "${pkgdir}/usr/share/applications"
    cat <<EOF > "${pkgdir}/usr/share/applications/cursor.desktop"
[Desktop Entry]
Name=Cursor
Exec=/usr/bin/cursor --no-sandbox %U
Terminal=false
Type=Application
Icon=cursor
StartupWMClass=cursor-url-handler
X-AppImage-Version=${pkgver}
MimeType=x-scheme-handler/cursor;
Categories=Utility;
EOF
}
'''
    # Replace everything from package() to the end of the file
    pkgbuild = re.sub(r'package\(\) \{.*', new_package_function.strip(), pkgbuild, flags=re.DOTALL)

    # Add post_install() function if it doesn't exist
    if 'post_install()' not in pkgbuild:
        pkgbuild += '\n\npost_install() {\n    update-desktop-database -q\n    xdg-icon-resource forceupdate\n}'

    return pkgbuild

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