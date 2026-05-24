#!/usr/bin/env bash
set -e

check_python() {
    if ! command -v python3 &>/dev/null; then
        echo "ERROR: python3 not found. Please install Python 3.10 or newer."
        exit 1
    fi
    major=$(python3 -c "import sys; print(sys.version_info.major)")
    minor=$(python3 -c "import sys; print(sys.version_info.minor)")
    if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 10 ]; }; then
        echo "ERROR: Python 3.10+ required (found $major.$minor)."
        exit 1
    fi
}

missing_deps() {
    local missing=()
    python3 -c "import PyQt5" 2>/dev/null \
        || missing+=("pyqt5")
    python3 -c "from PyQt5.QtMultimedia import QMediaPlayer" 2>/dev/null \
        || missing+=("qt5-multimedia")
    python3 -c "from PyQt5.QtMultimediaWidgets import QVideoWidget" 2>/dev/null \
        || missing+=("qt5-multimedia-widgets")
    command -v ffmpeg &>/dev/null \
        || missing+=("ffmpeg")

    # Check GStreamer backend — try instantiating a player and probing availability.
    # p.service() is deprecated in Qt 5.15+; fall back to isAvailable().
    if ! python3 -c "
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QApplication
import sys
app = QApplication.instance() or QApplication(sys.argv)
p = QMediaPlayer()
if hasattr(p, 'service'):
    ok = p.service() is not None
else:
    ok = p.isAvailable()
sys.exit(0 if ok else 1)
" 2>/dev/null; then
        missing+=("gst-libav")
    fi

    echo "${missing[@]}"
}

# Enable RPM Fusion Free on Fedora — required for ffmpeg and gstreamer1-libav.
enable_rpmfusion() {
    if rpm -q rpmfusion-free-release &>/dev/null; then
        return 0
    fi
    local ver
    ver=$(rpm -E %fedora 2>/dev/null)
    if [[ -z "$ver" || "$ver" == "%fedora" ]]; then
        echo ""
        echo "WARNING: Could not detect Fedora version."
        echo "  ffmpeg and GStreamer codecs require RPM Fusion Free."
        echo "  See: https://rpmfusion.org/Configuration"
        return 1
    fi
    echo "Enabling RPM Fusion Free (required for ffmpeg / GStreamer codecs)…"
    sudo dnf install -y \
        "https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-${ver}.noarch.rpm"
}

# Deduplicate an array while preserving order.
dedup() {
    local -A seen=()
    for item in "$@"; do
        [[ -z "${seen[$item]+x}" ]] && { echo "$item"; seen[$item]=1; }
    done
}

install_deps() {
    local pkgs=("$@")
    [ ${#pkgs[@]} -eq 0 ] && return

    if command -v pacman &>/dev/null; then
        declare -A pm_map=(
            [pyqt5]="python-pyqt5"
            [qt5-multimedia]="qt5-multimedia"
            [qt5-multimedia-widgets]="qt5-multimedia"
            [gst-libav]="gst-plugins-good gst-libav"
            [ffmpeg]="ffmpeg"
        )
        local to_install=()
        for dep in "${pkgs[@]}"; do
            to_install+=( ${pm_map[$dep]} )
        done
        mapfile -t to_install < <(dedup "${to_install[@]}")
        echo "Installing: ${to_install[*]}"
        sudo pacman -S --needed --noconfirm "${to_install[@]}"

    elif command -v apt-get &>/dev/null; then
        declare -A pm_map=(
            [pyqt5]="python3-pyqt5"
            [qt5-multimedia]="python3-pyqt5.qtmultimedia"
            [qt5-multimedia-widgets]="python3-pyqt5.qtmultimedia"
            [gst-libav]="gstreamer1.0-plugins-good gstreamer1.0-libav gstreamer1.0-plugins-bad"
            [ffmpeg]="ffmpeg"
        )
        local to_install=()
        for dep in "${pkgs[@]}"; do
            to_install+=( ${pm_map[$dep]} )
        done
        mapfile -t to_install < <(dedup "${to_install[@]}")
        echo "Installing: ${to_install[*]}"
        sudo apt-get install -y "${to_install[@]}"

    elif command -v dnf &>/dev/null; then
        # ffmpeg and gstreamer1-libav are in RPM Fusion Free, not default Fedora repos.
        local needs_rpmfusion=false
        for dep in "${pkgs[@]}"; do
            [[ "$dep" == "ffmpeg" || "$dep" == "gst-libav" ]] && needs_rpmfusion=true
        done
        $needs_rpmfusion && enable_rpmfusion

        declare -A pm_map=(
            [pyqt5]="python3-PyQt5"
            [qt5-multimedia]="qt5-qtmultimedia"
            [qt5-multimedia-widgets]="qt5-qtmultimedia"
            [gst-libav]="gstreamer1-plugins-good gstreamer1-libav"
            [ffmpeg]="ffmpeg"
        )
        local to_install=()
        for dep in "${pkgs[@]}"; do
            to_install+=( ${pm_map[$dep]} )
        done
        mapfile -t to_install < <(dedup "${to_install[@]}")
        echo "Installing: ${to_install[*]}"
        sudo dnf install -y "${to_install[@]}"

    elif command -v zypper &>/dev/null; then
        declare -A pm_map=(
            [pyqt5]="python3-qt5"
            [qt5-multimedia]="libqt5-qtmultimedia python3-qt5"
            [qt5-multimedia-widgets]="libqt5-qtmultimedia"
            [gst-libav]="gstreamer-plugins-good gstreamer-plugins-libav"
            [ffmpeg]="ffmpeg"
        )
        local to_install=()
        for dep in "${pkgs[@]}"; do
            to_install+=( ${pm_map[$dep]} )
        done
        mapfile -t to_install < <(dedup "${to_install[@]}")
        echo "Installing: ${to_install[*]}"
        sudo zypper install -y "${to_install[@]}"

    else
        echo ""
        echo "Could not detect a supported package manager (pacman/apt/dnf/zypper)."
        echo "Please install the following manually, then re-run this script:"
        for dep in "${pkgs[@]}"; do
            echo "  - $dep"
        done
        exit 1
    fi
}

echo "Checking dependencies…"
check_python

missing=( $(missing_deps) )

if [ ${#missing[@]} -gt 0 ]; then
    echo ""
    echo "Missing dependencies: ${missing[*]}"
    read -rp "Install them now? [Y/n] " answer
    answer=${answer:-Y}
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        install_deps "${missing[@]}"
    else
        echo "Aborted. Install the missing dependencies and re-run."
        exit 1
    fi
else
    echo "All dependencies satisfied."
fi

INSTALL_DIR="$HOME/.local/bin"
ICONS_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
APPS_DIR="$HOME/.local/share/applications"

mkdir -p "$INSTALL_DIR" "$ICONS_DIR" "$APPS_DIR"

cp fuetem_video.py "$INSTALL_DIR/fuetem-video"
chmod +x "$INSTALL_DIR/fuetem-video"

cp icons/fuetem-video.svg "$ICONS_DIR/"

cat > "$APPS_DIR/fuetem-video.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Fuetem Video
Comment=Video converter, trimmer, editor, and player
Exec=$INSTALL_DIR/fuetem-video %f
Icon=fuetem-video
MimeType=video/mp4;video/x-matroska;video/quicktime;video/x-msvideo;video/webm;
Categories=AudioVideo;Video;
StartupNotify=false
EOF

echo ""
echo "Fuetem Video installed successfully."
echo "Launch with: fuetem-video"
