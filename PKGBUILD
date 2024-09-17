# Maintainer: Your Name <your.email@example.com>

pkgname=cursor-bin
pkgver=0.41.0
pkgrel=1
pkgdesc="Cursor App - AI-first coding environment"
arch=('x86_64')
url="https://www.cursor.com/"
license=('custom:Proprietary')  # Replace with the correct license if known
depends=('fuse2')
options=(!strip)
source_x86_64=("https://download.todesktop.com/230313mzl4w4u92/cursor-0.41.0-build-240917hf2t71vk9-x86_64.AppImage" "cursor.png")
noextract=("$(basename ${source_x86_64[0]})")
sha512sums_x86_64=('748d59861e3227605d537d54f9b7a4cee37b5a99694bcbff177211c06ba01c05859b4c7fb0f32370da6e283e9fa7a6ea4ecd80b9006525cc85fa63cdd7091bc7'
                   'f948c5718c2df7fe2cae0cbcd95fd3010ecabe77c699209d4af5438215daecd74b08e03d18d07a26112bcc5a80958105fda724768394c838d08465fce5f473e7')
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

post_install() {
    update-desktop-database -q
    xdg-icon-resource forceupdate
}
