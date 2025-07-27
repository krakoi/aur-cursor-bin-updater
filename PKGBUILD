# Maintainer: Gunther Schulz <dev@guntherschulz.de>

pkgname=cursor-bin
pkgver=1.3.3
pkgrel=1
pkgdesc='AI-first coding environment'
arch=('x86_64')
url="https://www.cursor.com"
license=('LicenseRef-Cursor_EULA')
# electron* is added at package()
depends=('ripgrep' 'xdg-utils'
  'gcc-libs' 'hicolor-icon-theme' 'libxkbfile')
options=(!strip) # Don't break ext of VSCode
_appimage="${pkgname}-${pkgver}.AppImage"
source_x86_64=("${_appimage}::https://downloads.cursor.com/production/e589175333a2d938c3d944f9bf0993155e655e7f/linux/x64/Cursor-1.3.3-x86_64.AppImage" "cursor.png" "${pkgname}.desktop.in" "${pkgname}.sh"
https://gitlab.archlinux.org/archlinux/packaging/packages/code/-/raw/main/code.sh)
noextract=("${_appimage}")
sha512sums_x86_64=('38173a85ab5ee329f68d45cf36b6e0e859f6a6363b227ff79f55310d2c4e9a0c7689311fee9be42e5a83ac073c7b1dbc7ae04985b805bcf97b3777fbaa6e7cf6'
                   'f948c5718c2df7fe2cae0cbcd95fd3010ecabe77c699209d4af5438215daecd74b08e03d18d07a26112bcc5a80958105fda724768394c838d08465fce5f473e7'
                   '813d42d46f2e6aad72a599c93aeb0b11a668ad37b3ba94ab88deec927b79c34edf8d927e7bb2140f9147b086562736c3f708242183130824dd74b7a84ece67aa'
                   'ec3fa93a7df3ac97720d57e684f8745e3e34f39d9976163ea0001147961ca4caeb369de9d1e80c877bb417a0f1afa49547d154dde153be7fe6615092894cff47'
                   '937299c6cb6be2f8d25f7dbc95cf77423875c5f8353b8bd6cd7cc8e5603cbf8405b14dbf8bd615db2e3b36ed680fc8e1909410815f7f8587b7267a699e00ab37')

_app=/usr/share/cursor/resources/app
prepare() {
  rm -rf squashfs-root # for unclean build
  chmod +x ${_appimage}
  ./${_appimage} --appimage-extract > /dev/null
  cd squashfs-root
  # Shell completions
  mv usr/share/zsh/{vendor-completions,site-functions}
  # Replace vendored runtimes
  mv .${_app} usr/lib/cursor
  rm -r usr/share/cursor
  install -d usr/share/cursor/resources
  mv usr/lib/cursor .${_app}
  ln -sf /usr/bin/rg       .${_app}/node_modules/@vscode/ripgrep/bin/rg
  ln -sf /usr/bin/xdg-open .${_app}/node_modules/open/xdg-open
  # Unused icon name by desktop entries... 1024^2 is slow...
  rm -r usr/share/icons
  install -Dm644 co.anysphere.cursor.png usr/share/pixmaps/co.anysphere.cursor.png
}

package(){
  # Allop packaging with other electron by editing PKGBUILD
  _electron=electron$(rg --no-messages -N -o -r '$1' '"electron": *"[^\d]*(\d+)' squashfs-root${_app}/package.json)
  echo $_electron
  depends+=($_electron)
  cp -r --reflink=auto squashfs-root/usr "${pkgdir}/usr"
  sed -e "s|code-flags|cursor-flags|" -e "s|/usr/lib/code|${_app}|" -e "s|/usr/lib/code/code.mjs|--app=${_app}|" \
    -e "s|name=electron|name=${_electron}|" code.sh | install -Dm755 /dev/stdin "${pkgdir}"/usr/share/cursor/cursor
}
