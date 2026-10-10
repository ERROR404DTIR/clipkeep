#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"
APPDIR="${DIST_DIR}/Clipkeep.AppDir"
BUILD_DIR="${DIST_DIR}/build"

rm -rf "${APPDIR}" "${BUILD_DIR}"
mkdir -p "${APPDIR}" "${BUILD_DIR}"

echo "[1/4] Building with PyInstaller..."
"${SCRIPT_DIR}/.venv/bin/python" -m pip install --quiet pyinstaller 2>/dev/null || true

pushd "${BUILD_DIR}" >/dev/null
"${SCRIPT_DIR}/.venv/bin/pyinstaller" \
    --onefile \
    --windowed \
    --name clipkeep \
    --add-data "${SCRIPT_DIR}/src/clipkeep:clipkeep" \
    "${SCRIPT_DIR}/src/clipkeep/main.py"
popd >/dev/null

echo "[2/4] Setting up AppDir..."
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

cp "${BUILD_DIR}/dist/clipkeep" "${APPDIR}/usr/bin/clipkeep"
chmod +x "${APPDIR}/usr/bin/clipkeep"

cat > "${APPDIR}/clipkeep.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Clipkeep
Comment=Lightweight clipboard manager
Exec=clipkeep
Icon=clipkeep
Categories=Utility;
Terminal=false
DESKTOP

cp "${APPDIR}/clipkeep.desktop" "${APPDIR}/usr/share/applications/clipkeep.desktop"

# Placeholder icon (would need real .png in production)
cat > "${APPDIR}/clipkeep.png" <<'PNG'
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABmJLR0QA/wD/AP+gvaeTAAAAZklEQVRYhe3WMQ7AIAwEwS3G/P8X22qCC5KJh4M9uAjjgw3YgCE/2IANOfAJGvCJNeBxyoHnKQdeoDx4ngLgkOcP8D7wHvC38N7w3vDe8N7w3vAOcA5wBnAGcAZwBnAGcAZwBnAGcAa5WrgHHAMcTxC2YRoAAAAAElFTkSuQmCC
PNG
cp "${APPDIR}/clipkeep.png" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/clipkeep.png"

cat > "${APPDIR}/AppRun" <<'RUN'
#!/usr/bin/env bash
APPDIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="${APPDIR}/usr/bin:${PATH}"
exec clipkeep "$@"
RUN
chmod +x "${APPDIR}/AppRun"

echo "[3/4] Downloading linuxdeploy..."
LINUXDEPLOY="${BUILD_DIR}/linuxdeploy-x86_64.AppImage"
if [ ! -f "${LINUXDEPLOY}" ]; then
    curl -L -o "${LINUXDEPLOY}" \
        "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
    chmod +x "${LINUXDEPLOY}"
fi

echo "[4/4] Building AppImage..."
"${LINUXDEPLOY}" \
    --appdir "${APPDIR}" \
    --output appimage \
    --desktop-file "${APPDIR}/clipkeep.desktop"

# Find the actual built AppImage (not linuxdeploy itself)
APPIMAGE=$(find . -maxdepth 1 -name "Clipkeep*.AppImage" ! -name "linuxdeploy*.AppImage" -type f | head -1)
if [ -n "${APPIMAGE}" ]; then
    mv "${APPIMAGE}" "${DIST_DIR}/Clipkeep.AppImage"
else
    echo "ERROR: Built AppImage not found"
    exit 1
fi

echo ""
echo "Done! Output: ${DIST_DIR}/Clipkeep.AppImage"
ls -lh "${DIST_DIR}/Clipkeep.AppImage" 2>/dev/null || echo "AppImage not found, check errors above"
