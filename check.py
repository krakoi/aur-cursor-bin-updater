#!/usr/bin/env python
import requests
import re
import sys
import os
import json
import time
import yaml
import hashlib


def calculate_sha512(url):
    """Download file and calculate its SHA512."""
    print("::debug::Downloading file to calculate SHA512...")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    sha512_hash = hashlib.sha512()
    for chunk in response.iter_content(chunk_size=8192):
        sha512_hash.update(chunk)

    return sha512_hash.hexdigest()


def get_download_link(max_retries=2):
    cursor_url = "https://www.cursor.com/api/download?platform=linux-x64&releaseTrack=latest"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    }

    for attempt in range(max_retries + 1):
        try:
            print("::debug::Making request to:", cursor_url)
            response = requests.get(cursor_url, headers=headers)
            print(f"::debug::API status code: {response.status_code}")
            print(f"::debug::API raw response: {response.text}")

            if response.status_code == 200 and response.text.strip():
                data = response.json()
                print("::debug::API response:", json.dumps(data, indent=2))
                response.raise_for_status()

                download_url = data["downloadUrl"]
                # Extract version from the download URL
                # Format: Cursor-0.47.4-<hash>.deb.glibc2.25-x86_64.AppImage
                version_match = re.search(r"Cursor-([0-9.]+)-", download_url)
                if version_match:
                    version = version_match.group(1)
                    return download_url, version, None
                else:
                    raise ValueError("Could not extract version from download URL")

            else:
                print("::warning::Invalid response from Cursor API")
                raise requests.exceptions.RequestException(
                    "Invalid response from Cursor API"
                )

        except requests.exceptions.RequestException as e:
            print(f"::warning::Request failed: {str(e)}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"::warning::Failed to parse JSON or extract data: {str(e)}")
        except ValueError as e:
            print(f"::warning::{str(e)}")

        if attempt < max_retries:
            print("::debug::Retrying in 5 seconds...")
            time.sleep(5)

    print("::error::Failed to get download link after all retry attempts")
    return None, None, None


def get_local_pkgbuild_info():
    with open("PKGBUILD", "r") as file:
        content = file.read()
    version_match = re.search(r"pkgver=([^\n]+)", content)
    rel_match = re.search(r"pkgrel=(\d+)", content)
    source_match = re.search(r'source_x86_64=\(".*?::([^"]+)"', content)
    if version_match and rel_match and source_match:
        return version_match.group(1).strip(), rel_match.group(1), source_match.group(1)
    else:
        print(
            f"::error::Unable to find current version, release, or source in local PKGBUILD"
        )
        return None, None, None


def get_aur_pkgbuild_info():
    url = "https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=cursor-bin"
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        version_match = re.search(r"pkgver=([^\n]+)", content)
        rel_match = re.search(r"pkgrel=(\d+)", content)
        if version_match and rel_match:
            return version_match.group(1).strip(), rel_match.group(1)
        else:
            print(f"::warning::Unable to find version or release in AUR PKGBUILD")
            return None, None
    except Exception as e:
        print(f"::warning::Error fetching AUR PKGBUILD: {str(e)}")
        return None, None


try:
    # Check if DEBUG is set to true
    debug_mode = os.environ.get("DEBUG", "").lower() == "true"

    # Get the download link, version, and sha512
    download_link, download_version, download_sha512 = get_download_link()
    if not download_link:
        raise ValueError("Failed to get download link after retries")

    print(f"::debug::Download link: {download_link}")
    print(f"::debug::Download version: {download_version}")
    print(f"::debug::Download SHA512: {download_sha512}")

    local_version, local_rel, local_source = get_local_pkgbuild_info()
    if local_version is None or local_rel is None or local_source is None:
        raise ValueError("Failed to get local version, release, or source")

    print(
        f"::debug::Local version: {local_version}, release: {local_rel}, source: {local_source}"
    )

    # Determine if update is needed
    aur_version, aur_rel = get_aur_pkgbuild_info()
    print(f"::debug::AUR version: {aur_version}, release: {aur_rel}")

    # Check if this is a manual release update
    is_manual_rel_update = (
        aur_version == local_version
        and aur_rel
        and local_rel
        and int(local_rel) > int(aur_rel)
    )

    update_needed = (
        (download_version and download_version != local_version)
        or (download_link != local_source)
        or is_manual_rel_update
    )

    # Determine new_version and new_rel
    if update_needed:
        new_version = download_version if download_version else local_version
        if is_manual_rel_update:
            new_rel = local_rel  # Keep the manually set release number
        elif new_version == local_version:
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
        "new_rel": new_rel,
        "download_version": download_version,
        "download_sha512": download_sha512,
        "aur_version": aur_version,
        "aur_rel": aur_rel,
    }

    # Write JSON to file
    with open("check_output.json", "w") as f:
        json.dump(output, f)

    print(f"::debug::Check output written to check_output.json")
    print(f"::debug::Final new_version: {new_version}, new_rel: {new_rel}")

except Exception as e:
    print(f"::error::Error in main execution: {str(e)}")
    sys.exit(1)
