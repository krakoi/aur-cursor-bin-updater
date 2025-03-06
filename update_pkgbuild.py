import sys
import json
import os
import base64
import hashlib
import requests

DEBUG = os.environ.get("DEBUG", "false").lower() == "true"


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def base64_to_hex(base64_string):
    return base64.b64decode(base64_string).hex()


def calculate_sha512(url):
    """Download file and calculate its SHA512."""
    print("::debug::Downloading file to calculate SHA512...")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    sha512_hash = hashlib.sha512()
    for chunk in response.iter_content(chunk_size=8192):
        sha512_hash.update(chunk)

    return sha512_hash.hexdigest()


def calculate_file_sha512(filepath):
    """Calculate SHA512 of a local file."""
    sha512_hash = hashlib.sha512()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha512_hash.update(chunk)
    return sha512_hash.hexdigest()


def update_pkgbuild(pkgbuild_lines, json_data):
    download_link = json_data["download_link"]
    new_version = json_data["new_version"]
    new_rel = json_data["new_rel"]

    # Calculate SHA512 when updating PKGBUILD
    download_sha512 = calculate_sha512(download_link)
    debug_print(f"Calculated SHA512: {download_sha512}")

    # Calculate checksums for static files
    cursor_png_checksum = calculate_file_sha512("cursor.png")
    cursor_desktop_checksum = calculate_file_sha512("cursor-bin.desktop.in")
    cursor_launcher_checksum = calculate_file_sha512("cursor-bin.sh")

    updated_lines = []
    in_sha = False

    for line in pkgbuild_lines:
        if line.startswith("pkgver="):
            updated_lines.append(f"pkgver={new_version}\n")
        elif line.startswith("pkgrel="):
            updated_lines.append(f"pkgrel={new_rel}\n")
        elif line.startswith("source_x86_64="):
            updated_lines.append(
                f'source_x86_64=("${{_appimage}}::{download_link}" "cursor.png" "${{pkgname}}.desktop.in" "${{pkgname}}.sh")\n'
            )
        elif line.startswith("sha512sums_x86_64="):
            updated_lines.append(f"sha512sums_x86_64=('{download_sha512}'\n")
            in_sha = True
        elif in_sha and line.strip().endswith(")"):
            updated_lines.append(f"                   '{cursor_png_checksum}'\n")
            updated_lines.append(f"                   '{cursor_desktop_checksum}'\n")
            updated_lines.append(f"                   '{cursor_launcher_checksum}')\n")
            in_sha = False
        elif not in_sha:
            updated_lines.append(line)

    return updated_lines


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_pkgbuild.py <check_output_file>")
        sys.exit(1)

    debug_print(f"Reading check output from {sys.argv[1]}")
    with open(sys.argv[1], "r") as f:
        check_output = json.load(f)

    debug_print(f"Check output content: {json.dumps(check_output, indent=2)}")

    if check_output["update_needed"]:
        debug_print("Update needed, reading current PKGBUILD")
        with open("PKGBUILD", "r") as f:
            current_pkgbuild = f.readlines()

        debug_print("Calling update_pkgbuild()")
        updated_pkgbuild = update_pkgbuild(current_pkgbuild, check_output)

        # Write the changes to the file
        with open("PKGBUILD", "w") as f:
            f.writelines(updated_pkgbuild)
        debug_print(
            f"PKGBUILD updated to version {check_output['new_version']} (release {check_output['new_rel']}) with new download link and SHA512"
        )
    else:
        print("No update needed.")
