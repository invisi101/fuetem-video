#!/usr/bin/env python3
"""Fuetem Video — kitchen-sink video tool."""

import sys
import os
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

# ── Constants ─────────────────────────────────────────────────────────────────

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv",
              ".m4v", ".ts", ".mts", ".m2ts", ".mpeg", ".mpg", ".ogv",
              ".3gp", ".gif", ".vob", ".f4v", ".divx", ".rmvb"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}

VIDEO_FORMATS = ["mp4", "mkv", "webm", "mov", "avi", "flv", "ts"]
VIDEO_CODECS  = ["libx264", "libx265", "libvpx-vp9", "libaom-av1", "copy", "none"]
AUDIO_CODECS  = ["aac", "libmp3lame", "libopus", "flac", "ac3", "copy", "none"]
AUDIO_FORMATS = ["mp3", "flac", "opus", "wav", "aac", "m4a", "ogg"]
RESOLUTIONS   = ["Original", "3840×2160", "2560×1440", "1920×1080",
                 "1280×720", "854×480", "640×360", "Custom…"]
FRAMERATES    = ["Original", "120", "60", "59.94", "50", "30", "29.97",
                 "25", "24", "23.976"]
PRESETS_264   = ["ultrafast", "superfast", "veryfast", "faster", "fast",
                 "medium", "slow", "slower", "veryslow"]
AUDIO_BR      = ["best", "320k", "256k", "192k", "128k", "96k", "64k"]
FRAME_FMTS    = ["png", "jpg", "bmp", "tiff", "webp"]
SUB_FMTS      = ["srt", "ass", "vtt"]
SPEED_VALUES  = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 4.0]
OVERLAY_POS   = ["Top-Left", "Top-Right", "Centre", "Bottom-Left", "Bottom-Right", "Custom"]

VAAPI_DEVICE = "/dev/dri/renderD128"
MAX_THUMBS   = 80
MAX_RECENT   = 10
CONFIG_DIR   = Path.home() / ".config" / "fuetem-video"
RECENT_FILE  = CONFIG_DIR / "recent.json"
THUMB_DIR    = Path(tempfile.gettempdir()) / "fuetem_video_thumbs"

# ── Stylesheet ────────────────────────────────────────────────────────────────

NEON_STYLESHEET = """
QWidget#MainWindow {
    background: qlineargradient(y1:0, y2:1,
        stop:0 #0f0f23, stop:1 #12122e);
}
QLabel { color: #e0e0ff; font-size: 15px; }
QLabel#brandLarge { color: #f472b6; padding-top: 8px; padding-bottom: 8px; }
QLabel#sectionLabel { color: #f472b6; font-weight: 600; font-size: 15px; }
QLabel#statusLabel  { color: #a5b4fc; font-size: 15px; }
QLabel#timeLabel    { color: #c4c4f0; font-size: 15px; font-family: monospace; }
QLabel#fileInfoLabel { color: rgba(196,196,240,0.6); font-size: 15px; }
QLabel#dimLabel     { color: rgba(196,196,240,0.4); font-size: 14px; }

QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #16213e;
    border: 1px solid #2d2d5e;
    border-radius: 6px;
    color: #e0e0ff;
    padding: 5px 10px;
    font-size: 15px;
    selection-background-color: #818cf8;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #818cf8;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #2d2d5e;
    border: none;
    width: 18px;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #818cf8;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #818cf8;
}

QComboBox {
    background-color: #16213e;
    border: 1px solid #2d2d5e;
    border-radius: 6px;
    color: #e0e0ff;
    padding: 5px 10px;
    font-size: 15px;
    min-width: 80px;
}
QComboBox:focus, QComboBox:hover { border: 1px solid #818cf8; }
QComboBox::drop-down { border: none; padding-right: 6px; }
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #818cf8;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #1a1a2e;
    border: 1px solid #2d2d5e;
    color: #e0e0ff;
    selection-background-color: rgba(129,140,248,0.3);
    outline: none;
}

QCheckBox { color: #c4c4f0; spacing: 6px; font-size: 15px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border-radius: 3px;
    border: 2px solid #2d2d5e;
    background-color: #16213e;
}
QCheckBox::indicator:checked {
    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #f472b6, stop:1 #818cf8);
    border: 2px solid #818cf8;
}
QCheckBox::indicator:hover { border-color: #818cf8; }

QSlider::groove:horizontal {
    background: #2d2d5e;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #818cf8;
    width: 16px; height: 16px;
    border-radius: 8px;
    margin: -5px 0;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, x2:1,
        stop:0 #f472b6, stop:1 #818cf8);
    border-radius: 3px;
}

QProgressBar {
    background-color: #1a1a2e;
    border: 1px solid #2d2d5e;
    border-radius: 8px;
    min-height: 18px; max-height: 18px;
    text-align: center;
    color: #e0e0ff; font-size: 13px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, x2:1,
        stop:0 #34d399, stop:0.5 #06b6d4, stop:1 #818cf8);
    border-radius: 7px;
}

QPushButton#actionBtn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #f472b6, stop:1 #818cf8);
    color: #fff; border: none; border-radius: 7px;
    padding: 8px 22px; font-size: 15px; font-weight: 600;
}
QPushButton#actionBtn:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #f9a8d4, stop:1 #a5b4fc);
}
QPushButton#actionBtn:pressed {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #ec4899, stop:1 #6366f1);
}
QPushButton#actionBtn:disabled { background: #2d2d5e; color: rgba(196,196,240,0.4); }

QPushButton#cancelBtn {
    background-color: transparent; color: #f472b6;
    border: 1px solid rgba(244,114,182,0.35); border-radius: 7px;
    padding: 8px 18px; font-size: 15px;
}
QPushButton#cancelBtn:hover {
    border-color: rgba(244,114,182,0.7);
    background-color: rgba(244,114,182,0.1);
}

QPushButton#openBtn {
    background-color: transparent; color: #06b6d4;
    border: 1px solid rgba(6,182,212,0.35); border-radius: 7px;
    padding: 6px 16px; font-size: 15px;
}
QPushButton#openBtn:hover {
    border-color: rgba(6,182,212,0.7);
    background-color: rgba(6,182,212,0.1);
}

QPushButton#transportBtn {
    background-color: #1a1a2e; color: #e0e0ff;
    border: 1px solid rgba(129,140,248,0.3);
    border-radius: 18px; font-size: 16px; font-weight: bold;
}
QPushButton#transportBtn:hover {
    border-color: rgba(129,140,248,0.7);
    background-color: rgba(129,140,248,0.12);
}
QPushButton#transportBtn:disabled { color: rgba(196,196,240,0.25); }
QPushButton#transportBtn:checked {
    background-color: rgba(129,140,248,0.2);
    border-color: #818cf8;
}

QPushButton#nudgeBtn {
    background-color: #16213e; color: #818cf8;
    border: 1px solid #2d2d5e; border-radius: 4px;
    font-size: 15px; font-weight: bold; padding: 0px;
}
QPushButton#nudgeBtn:hover {
    border-color: rgba(129,140,248,0.6);
    background-color: rgba(129,140,248,0.1);
}

QPushButton#smallBtn {
    background-color: transparent; color: #818cf8;
    border: 1px solid rgba(129,140,248,0.3); border-radius: 5px;
    padding: 4px 10px; font-size: 15px;
}
QPushButton#smallBtn:hover {
    border-color: rgba(129,140,248,0.7);
    background-color: rgba(129,140,248,0.1);
}
QPushButton#smallBtn:disabled { color: rgba(129,140,248,0.3); }

QPushButton#dangerBtn {
    background-color: transparent; color: #f87171;
    border: 1px solid rgba(248,113,113,0.3); border-radius: 7px;
    padding: 8px 18px; font-size: 15px;
}
QPushButton#dangerBtn:hover {
    border-color: rgba(248,113,113,0.7);
    background-color: rgba(248,113,113,0.1);
}

QPushButton#recentBtn {
    background-color: transparent; color: #a5b4fc;
    border: 1px solid rgba(129,140,248,0.2); border-radius: 5px;
    padding: 5px 12px; font-size: 15px;
}
QPushButton#recentBtn:hover {
    border-color: rgba(129,140,248,0.5);
    background-color: rgba(129,140,248,0.08);
}

QFrame#card {
    background-color: #1a1a2e;
    border: 1px solid rgba(129,140,248,0.15);
    border-radius: 10px;
}
QFrame#separator {
    background-color: rgba(129,140,248,0.12);
    max-height: 1px;
}
QFrame#videoFrame {
    background-color: #000;
    border: 1px solid rgba(129,140,248,0.15);
    border-radius: 6px;
}

QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: #0f0f23; width: 8px; border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: rgba(129,140,248,0.3); border-radius: 4px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: rgba(129,140,248,0.5); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

QTabWidget::pane {
    background-color: #1a1a2e;
    border: 1px solid rgba(129,140,248,0.15);
    border-radius: 0px 8px 8px 8px;
}
QTabBar::tab {
    background-color: #16213e;
    color: rgba(196,196,240,0.55);
    border: 1px solid rgba(45,45,94,0.5);
    border-bottom: none;
    padding: 5px 10px;
    font-size: 14px;
    min-width: 68px;
    margin-right: 2px;
    border-radius: 5px 5px 0 0;
}
QTabBar::tab:selected {
    background-color: #1a1a2e;
    color: #f472b6;
    border-color: rgba(129,140,248,0.25);
}
QTabBar::tab:hover:!selected {
    color: #e0e0ff;
    background-color: rgba(129,140,248,0.1);
}

QListWidget {
    background-color: #16213e;
    border: 1px solid #2d2d5e;
    border-radius: 6px;
    color: #e0e0ff;
    font-size: 15px;
    outline: none;
}
QListWidget::item { padding: 5px 8px; }
QListWidget::item:selected {
    background-color: rgba(129,140,248,0.25);
    color: #e0e0ff;
}
QListWidget::item:hover:!selected {
    background-color: rgba(129,140,248,0.1);
}

QTextEdit {
    background-color: #16213e;
    border: 1px solid #2d2d5e;
    border-radius: 6px;
    color: #c4c4f0;
    font-family: monospace;
    font-size: 13px;
    selection-background-color: rgba(129,140,248,0.3);
}

QMessageBox { background-color: #1a1a2e; }
QMessageBox QLabel { color: #e0e0ff; font-size: 15px; }
QMessageBox QPushButton {
    background-color: #2d2d5e; color: #e0e0ff;
    border: 1px solid rgba(129,140,248,0.3);
    border-radius: 5px; padding: 5px 18px; font-size: 15px;
}
QMessageBox QPushButton:hover { background-color: rgba(129,140,248,0.2); }

QSplitter::handle { background: rgba(129,140,248,0.1); }
QSplitter::handle:horizontal { width: 3px; }
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def _ms_to_hms(ms: int) -> str:
    h, rem = divmod(ms // 1000, 3600)
    m, s = divmod(rem, 60)
    frac = (ms % 1000) // 10
    return f"{h}:{m:02d}:{s:02d}.{frac:02d}"


def _secs_to_timestr(secs: float) -> str:
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = secs % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _timestr_to_secs(text: str) -> float:
    text = text.strip()
    parts = text.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except Exception:
        raise ValueError(f"Invalid time: '{text}'. Use HH:MM:SS.mmm")


def _load_recent() -> list:
    try:
        return json.loads(RECENT_FILE.read_text())
    except Exception:
        return []


def _save_recent(paths: list):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    RECENT_FILE.write_text(json.dumps(paths))


def _add_to_recent(path: str):
    paths = [p for p in _load_recent() if p != path]
    paths.insert(0, path)
    _save_recent(paths[:MAX_RECENT])


def _probe(path: str) -> dict:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format",
             "-of", "json", path],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(r.stdout)
    except Exception:
        return {}

    result = {"raw": data}
    fmt     = data.get("format", {})
    streams = data.get("streams", [])

    result["duration"]    = float(fmt.get("duration", 0) or 0)
    result["size"]        = int(fmt.get("size", 0) or 0)
    result["bit_rate"]    = int(fmt.get("bit_rate", 0) or 0)
    result["format_name"] = fmt.get("format_name", "")
    result["tags"]        = fmt.get("tags", {})

    result["video_streams"]    = [s for s in streams if s.get("codec_type") == "video"]
    result["audio_streams"]    = [s for s in streams if s.get("codec_type") == "audio"]
    result["subtitle_streams"] = [s for s in streams if s.get("codec_type") == "subtitle"]
    result["data_streams"]     = [s for s in streams if s.get("codec_type") == "data"]

    # Parse Apple QuickTime device metadata
    tag_lc = {k.lower(): v for k, v in result["tags"].items()}
    device = {}
    for qt_key, short in [
        ("com.apple.quicktime.make",              "make"),
        ("com.apple.quicktime.model",             "model"),
        ("com.apple.quicktime.software",          "software"),
        ("com.apple.quicktime.creationdate",      "creation_date"),
        ("com.apple.quicktime.location.iso6709",  "location"),
        ("com.apple.quicktime.location.accuracy.horizontal", "location_accuracy"),
    ]:
        v = tag_lc.get(qt_key, "")
        if v:
            device[short] = v
    if not device.get("creation_date"):
        device["creation_date"] = tag_lc.get("creation_time", "")
    if device:
        result["device_info"] = device

    if result["video_streams"]:
        vs = result["video_streams"][0]
        result["width"]    = vs.get("width", 0)
        result["height"]   = vs.get("height", 0)
        result["vcodec"]   = vs.get("codec_name", "")
        result["pix_fmt"]  = vs.get("pix_fmt", "")
        result["vbitrate"] = int(vs.get("bit_rate", 0) or 0)
        fr = vs.get("r_frame_rate", "25/1")
        try:
            n, d = fr.split("/")
            result["fps"] = float(n) / float(d)
        except Exception:
            result["fps"] = 25.0
    else:
        result["width"] = result["height"] = 0
        result["fps"] = 25.0
        result["vcodec"] = ""

    if result["audio_streams"]:
        as_ = result["audio_streams"][0]
        result["acodec"]      = as_.get("codec_name", "")
        result["sample_rate"] = as_.get("sample_rate", "")
        result["channels"]    = as_.get("channels", 0)
    else:
        result["acodec"] = ""

    return result


def _atempo_chain(speed: float) -> list:
    """Build a list of atempo filter strings for the given speed multiplier."""
    filters = []
    remaining = speed
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining *= 2.0
    if abs(remaining - 1.0) > 0.001:
        filters.append(f"atempo={remaining:.6f}")
    return filters


def _parse_iso6709(s: str):
    """Return (lat, lon) floats from an ISO 6709 string like +35.7070+139.7366+012/"""
    import re
    m = re.match(r'([+-]\d+\.?\d*)([+-]\d+\.?\d*)', s.strip())
    if m:
        try:
            return float(m.group(1)), float(m.group(2))
        except ValueError:
            pass
    return None


def _overlay_expr(pos: str, margin: int = 10) -> str:
    m = margin
    return {
        "Top-Left":     f"{m}:{m}",
        "Top-Right":    f"main_w-overlay_w-{m}:{m}",
        "Centre":       "(main_w-overlay_w)/2:(main_h-overlay_h)/2",
        "Bottom-Left":  f"{m}:main_h-overlay_h-{m}",
        "Bottom-Right": f"main_w-overlay_w-{m}:main_h-overlay_h-{m}",
    }.get(pos, f"{m}:{m}")


def _res_to_wh(label: str):
    table = {
        "3840×2160": (3840, 2160), "2560×1440": (2560, 1440),
        "1920×1080": (1920, 1080), "1280×720":  (1280, 720),
        "854×480":   (854,  480),  "640×360":   (640,  360),
    }
    return table.get(label)


# ── Workers ───────────────────────────────────────────────────────────────────

class FFmpegWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(bool, str)

    def __init__(self, cmd: list, total_seconds: float = 0.0):
        super().__init__()
        self.cmd = cmd
        self.total_seconds = total_seconds
        self._process = None
        self._cancelled = False

    def cancel(self):
        self._cancelled = True
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()

    def run(self):
        try:
            self._process = subprocess.Popen(
                self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
        except FileNotFoundError as e:
            self.finished.emit(False, str(e))
            return

        last_line = ""
        for line in (self._process.stdout or []):
            if self._cancelled:
                break
            line = line.rstrip()
            last_line = line
            if line.startswith("out_time_ms=") and self.total_seconds > 0:
                try:
                    us = int(line.split("=", 1)[1])
                    pct = min(100, int(us / (self.total_seconds * 1_000_000) * 100))
                    self.progress.emit(pct)
                except (ValueError, ZeroDivisionError):
                    pass

        ret = self._process.wait()
        if self._cancelled:
            self.finished.emit(False, "Cancelled.")
        else:
            self.finished.emit(ret == 0, last_line)


class MultiCmdWorker(QtCore.QThread):
    """Run a list of ffmpeg commands sequentially, reporting step progress."""
    step_done = QtCore.pyqtSignal(int, int)   # current, total
    finished  = QtCore.pyqtSignal(bool, str)

    def __init__(self, cmds: list):
        super().__init__()
        self.cmds = cmds
        self._cancelled = False
        self._proc = None

    def cancel(self):
        self._cancelled = True
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass

    def run(self):
        total = len(self.cmds)
        for i, cmd in enumerate(self.cmds, 1):
            if self._cancelled:
                self.finished.emit(False, "Cancelled.")
                return
            self._proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)
            self._proc.wait()
            if self._proc.returncode != 0:
                self.finished.emit(False, f"Step {i}/{total} failed.")
                return
            self.step_done.emit(i, total)
        self.finished.emit(True, "Done.")


class ThumbnailWorker(QtCore.QThread):
    thumbnail_ready = QtCore.pyqtSignal(int, QtGui.QPixmap)
    finished        = QtCore.pyqtSignal(int)

    THUMB_H = 68

    def __init__(self, path: str, count: int):
        super().__init__()
        self.path  = path
        self.count = count
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        if THUMB_DIR.exists():
            shutil.rmtree(THUMB_DIR, ignore_errors=True)
        THUMB_DIR.mkdir(parents=True, exist_ok=True)

        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", self.path],
            capture_output=True, text=True,
        )
        try:
            duration = float(r.stdout.strip())
        except Exception:
            self.finished.emit(0)
            return

        fps = min(self.count / duration, 2.0) if duration > 0 else 1.0
        cmd = [
            "ffmpeg", "-i", self.path,
            "-vf", f"fps={fps:.6f},scale=-1:{self.THUMB_H}",
            "-f", "image2", str(THUMB_DIR / "t_%04d.jpg"),
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)

        thumbs = sorted(THUMB_DIR.glob("t_*.jpg"))
        for i, tp in enumerate(thumbs):
            if self._cancelled:
                break
            pm = QtGui.QPixmap(str(tp))
            if not pm.isNull():
                self.thumbnail_ready.emit(i, pm)

        self.finished.emit(len(thumbs))


# ── Widgets ───────────────────────────────────────────────────────────────────

class ThumbnailTimeline(QtWidgets.QWidget):
    seek_requested = QtCore.pyqtSignal(float)

    THUMB_H = ThumbnailWorker.THUMB_H

    def __init__(self):
        super().__init__()
        self.setFixedHeight(self.THUMB_H + 6)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self._thumbs: list = []
        self._position = 0.0
        self._loading  = False
        self._worker: ThumbnailWorker | None = None

    def load_file(self, path: str, duration: float):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()
        self.clear()
        self.set_loading(True)
        count = min(MAX_THUMBS, max(20, int(self.width() / 12) or 40))
        self._worker = ThumbnailWorker(path, count)
        self._worker.thumbnail_ready.connect(self.add_thumbnail)
        self._worker.finished.connect(lambda _: self.set_loading(False))
        self._worker.start()

    def set_loading(self, v: bool):
        self._loading = v
        if v:
            self._thumbs = []
        self.update()

    def add_thumbnail(self, _idx: int, pm: QtGui.QPixmap):
        self._thumbs.append(pm.scaledToHeight(self.THUMB_H, QtCore.Qt.SmoothTransformation))
        self.update()

    def set_position(self, ratio: float):
        self._position = max(0.0, min(1.0, ratio))
        self.update()

    def clear(self):
        self._thumbs = []
        self._loading = False
        self.update()

    def paintEvent(self, _e):
        p = QtGui.QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QtGui.QColor(15, 15, 30))

        if self._loading:
            p.setPen(QtGui.QColor(129, 140, 248, 100))
            p.drawText(QtCore.QRect(0, 0, w, h), QtCore.Qt.AlignCenter, "Loading thumbnails…")
        elif not self._thumbs:
            p.setPen(QtGui.QColor(129, 140, 248, 50))
            p.drawText(QtCore.QRect(0, 0, w, h), QtCore.Qt.AlignCenter, "Open a file")
        else:
            n = len(self._thumbs)
            for i, pm in enumerate(self._thumbs):
                x  = int(i * w / n)
                tw = int((i + 1) * w / n) - x
                p.drawPixmap(x, 3, tw, h - 6, pm)

        px = int(self._position * w)
        p.setPen(QtGui.QPen(QtGui.QColor(244, 114, 182, 220), 2))
        p.drawLine(px, 0, px, h)

        p.setPen(QtGui.QPen(QtGui.QColor(45, 45, 94, 80), 1))
        p.drawRect(0, 0, w - 1, h - 1)

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self.seek_requested.emit(e.x() / self.width())

    def mouseMoveEvent(self, e):
        if e.buttons() & QtCore.Qt.LeftButton:
            self.seek_requested.emit(max(0.0, min(1.0, e.x() / self.width())))


class TimeSpinWidget(QtWidgets.QWidget):
    def __init__(self, label: str):
        super().__init__()
        self._step_ms = 100   # updated to 1-frame duration when a file is loaded

        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)
        lay.addWidget(QtWidgets.QLabel(label))

        self._minus = QtWidgets.QPushButton("−")
        self._minus.setObjectName("nudgeBtn")
        self._minus.setFixedSize(24, 30)
        self._minus.clicked.connect(self._nudge_minus)
        lay.addWidget(self._minus)

        self._edit = QtWidgets.QLineEdit("00:00:00.000")
        self._edit.setFixedWidth(130)
        self._edit.setPlaceholderText("HH:MM:SS.mmm")
        lay.addWidget(self._edit)

        self._plus = QtWidgets.QPushButton("+")
        self._plus.setObjectName("nudgeBtn")
        self._plus.setFixedSize(24, 30)
        self._plus.clicked.connect(self._nudge_plus)
        lay.addWidget(self._plus)

    def set_fps(self, fps: float):
        """Set nudge step to one frame duration for the given frame rate."""
        self._step_ms = round(1000 / fps) if fps > 0 else 100

    def text(self) -> str:      return self._edit.text()
    def setText(self, t: str):  self._edit.setText(t)

    @property
    def textChanged(self):      return self._edit.textChanged

    def _nudge(self, delta_ms: int):
        try:
            secs = max(0.0, _timestr_to_secs(self._edit.text()) + delta_ms / 1000)
            self._edit.setText(_secs_to_timestr(secs))
        except ValueError:
            pass

    def _nudge_minus(self): self._nudge(-self._step_ms)
    def _nudge_plus(self):  self._nudge(+self._step_ms)


class DragFileList(QtWidgets.QListWidget):
    """Drag-to-reorder list for the Merge tab."""
    def __init__(self):
        super().__init__()
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setMinimumHeight(120)

    def paths(self) -> list:
        return [self.item(i).data(QtCore.Qt.UserRole) for i in range(self.count())]

    def add_path(self, path: str):
        item = QtWidgets.QListWidgetItem(os.path.basename(path))
        item.setData(QtCore.Qt.UserRole, path)
        item.setToolTip(path)
        self.addItem(item)


# ── Page: Trim / Split ────────────────────────────────────────────────────────

class TrimSplitPage(QtWidgets.QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self._build_ui()

    def _build_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        # ── Trim ──
        trim_card, tlay = self._card("TRIM")

        time_row = QtWidgets.QHBoxLayout()
        self.trim_start = TimeSpinWidget("Start:")
        time_row.addWidget(self.trim_start)
        self.set_start_btn = QtWidgets.QPushButton("Set")
        self.set_start_btn.setObjectName("smallBtn")
        self.set_start_btn.setFixedWidth(38)
        self.set_start_btn.setToolTip("Set to playhead position")
        self.set_start_btn.clicked.connect(
            lambda: self._snap_to_pos(self.trim_start))
        time_row.addWidget(self.set_start_btn)
        time_row.addSpacing(12)
        self.trim_end = TimeSpinWidget("End:")
        time_row.addWidget(self.trim_end)
        self.set_end_btn = QtWidgets.QPushButton("Set")
        self.set_end_btn.setObjectName("smallBtn")
        self.set_end_btn.setFixedWidth(38)
        self.set_end_btn.setToolTip("Set to playhead position")
        self.set_end_btn.clicked.connect(
            lambda: self._snap_to_pos(self.trim_end))
        time_row.addWidget(self.set_end_btn)
        time_row.addStretch(1)
        tlay.addLayout(time_row)

        opt_row = QtWidgets.QHBoxLayout()
        self.stream_copy_cb = QtWidgets.QCheckBox("Stream copy (fast, no re-encode)")
        self.stream_copy_cb.setChecked(True)
        self.stream_copy_cb.toggled.connect(self._on_copy_toggled)
        opt_row.addWidget(self.stream_copy_cb)
        opt_row.addStretch(1)
        tlay.addLayout(opt_row)

        encode_row = QtWidgets.QHBoxLayout()
        encode_row.addWidget(QtWidgets.QLabel("Format:"))
        self.trim_fmt = QtWidgets.QComboBox()
        self.trim_fmt.addItems(VIDEO_FORMATS)
        encode_row.addWidget(self.trim_fmt)
        encode_row.addSpacing(8)
        encode_row.addWidget(QtWidgets.QLabel("Video:"))
        self.trim_vcodec = QtWidgets.QComboBox()
        self.trim_vcodec.addItems([c for c in VIDEO_CODECS if c != "none"])
        encode_row.addWidget(self.trim_vcodec)
        encode_row.addSpacing(8)
        encode_row.addWidget(QtWidgets.QLabel("CRF:"))
        self.trim_crf = QtWidgets.QSpinBox()
        self.trim_crf.setRange(0, 51)
        self.trim_crf.setValue(23)
        self.trim_crf.setFixedWidth(60)
        encode_row.addWidget(self.trim_crf)
        encode_row.addStretch(1)
        self.trim_encode_widget = QtWidgets.QWidget()
        self.trim_encode_widget.setLayout(encode_row)
        self.trim_encode_widget.setEnabled(False)
        tlay.addWidget(self.trim_encode_widget)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        self.trim_btn = QtWidgets.QPushButton("Save Trim")
        self.trim_btn.setObjectName("actionBtn")
        self.trim_btn.clicked.connect(self._do_trim)
        btn_row.addWidget(self.trim_btn)
        tlay.addLayout(btn_row)

        lay.addWidget(trim_card)

        # ── Separator ──
        sep = QtWidgets.QFrame()
        sep.setObjectName("separator")
        lay.addWidget(sep)

        # ── Split at position ──
        split_card, slay = self._card("SPLIT")

        row1 = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel("Split at current playhead position")
        lbl.setObjectName("fileInfoLabel")
        row1.addWidget(lbl)
        row1.addStretch(1)
        self.split_pos_btn = QtWidgets.QPushButton("Split Here")
        self.split_pos_btn.setObjectName("actionBtn")
        self.split_pos_btn.clicked.connect(self._do_split_at_pos)
        row1.addWidget(self.split_pos_btn)
        slay.addLayout(row1)

        sep2 = QtWidgets.QFrame(); sep2.setObjectName("separator")
        slay.addWidget(sep2)

        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(QtWidgets.QLabel("Split into"))
        self.split_n = QtWidgets.QSpinBox()
        self.split_n.setRange(2, 100)
        self.split_n.setValue(2)
        self.split_n.setFixedWidth(70)
        row2.addWidget(self.split_n)
        row2.addWidget(QtWidgets.QLabel("equal parts"))
        row2.addStretch(1)
        self.split_equal_btn = QtWidgets.QPushButton("Split Equal")
        self.split_equal_btn.setObjectName("actionBtn")
        self.split_equal_btn.clicked.connect(self._do_split_equal)
        row2.addWidget(self.split_equal_btn)
        slay.addLayout(row2)

        sep3 = QtWidgets.QFrame(); sep3.setObjectName("separator")
        slay.addWidget(sep3)

        row3 = QtWidgets.QHBoxLayout()
        row3.addWidget(QtWidgets.QLabel("Split every"))
        self.split_secs = QtWidgets.QDoubleSpinBox()
        self.split_secs.setRange(1.0, 3600.0)
        self.split_secs.setValue(60.0)
        self.split_secs.setSuffix(" s")
        self.split_secs.setFixedWidth(90)
        row3.addWidget(self.split_secs)
        row3.addWidget(QtWidgets.QLabel("(segment muxer, stream copy)"))
        row3.addStretch(1)
        self.split_seg_btn = QtWidgets.QPushButton("Split Segments")
        self.split_seg_btn.setObjectName("actionBtn")
        self.split_seg_btn.clicked.connect(self._do_split_segments)
        row3.addWidget(self.split_seg_btn)
        slay.addLayout(row3)

        lay.addWidget(split_card)
        lay.addStretch(1)
        self._refresh_controls()

    # ── helpers ──

    def _card(self, title=""):
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        lay = QtWidgets.QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(8)
        if title:
            lbl = QtWidgets.QLabel(title)
            lbl.setObjectName("sectionLabel")
            lay.addWidget(lbl)
        return card, lay

    def _snap_to_pos(self, target: TimeSpinWidget):
        target.setText(_secs_to_timestr(self.ctrl.player.position() / 1000))

    def _on_copy_toggled(self, checked: bool):
        self.trim_encode_widget.setEnabled(not checked)

    def on_file_loaded(self):
        pd = self.ctrl.probe_data
        fps = pd.get("fps", 25.0)
        self.trim_start.set_fps(fps)
        self.trim_end.set_fps(fps)
        self.trim_start.setText("00:00:00.000")
        self.trim_end.setText(_secs_to_timestr(pd.get("duration", 0)))
        self._refresh_controls()

    def _refresh_controls(self):
        has = self.ctrl.current_file is not None
        for w in (self.trim_btn, self.split_pos_btn,
                  self.split_equal_btn, self.split_seg_btn):
            w.setEnabled(has)

    def _pick_folder(self):
        src = Path(self.ctrl.current_file)
        d = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Output Folder", str(src.parent))
        return d or None

    # ── actions ──

    def _do_trim(self):
        if not self.ctrl.current_file:
            return
        try:
            start_s = _timestr_to_secs(self.trim_start.text())
            end_s   = _timestr_to_secs(self.trim_end.text())
        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Invalid Time", str(e))
            return
        if end_s <= start_s:
            QtWidgets.QMessageBox.warning(self, "Invalid Range",
                                          "End must be after start.")
            return

        src = Path(self.ctrl.current_file)
        fmt = self.trim_fmt.currentText() if not self.stream_copy_cb.isChecked() \
              else src.suffix.lstrip(".")
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Trimmed File",
            str(src.parent / f"{src.stem}_trim.{fmt}"),
            f"{fmt.upper()} (*.{fmt});;All Files (*)",
        )
        if not out:
            return

        dur = end_s - start_s
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-ss", f"{start_s:.6f}", "-i", self.ctrl.current_file,
               "-t", f"{dur:.6f}"]
        if self.stream_copy_cb.isChecked():
            cmd.extend(["-c", "copy", "-avoid_negative_ts", "make_zero"])
        else:
            vcodec = self.trim_vcodec.currentText()
            cmd.extend(["-c:v", vcodec, "-crf", str(self.trim_crf.value()),
                        "-c:a", "copy"])
        cmd.append(out)
        self.ctrl._run_ffmpeg(cmd, dur, f"Trimming…")

    def _do_split_at_pos(self):
        if not self.ctrl.current_file:
            return
        pos_s  = self.ctrl.player.position() / 1000
        if pos_s <= 0:
            QtWidgets.QMessageBox.warning(self, "No Position",
                                          "Seek to a position first.")
            return
        src = Path(self.ctrl.current_file)
        ext = src.suffix
        out_dir = self._pick_folder()
        if not out_dir:
            return

        part1 = str(Path(out_dir) / f"{src.stem}_part1{ext}")
        part2 = str(Path(out_dir) / f"{src.stem}_part2{ext}")
        cmds = [
            ["ffmpeg", "-y", "-i", self.ctrl.current_file,
             "-t", f"{pos_s:.6f}", "-c", "copy", part1],
            ["ffmpeg", "-y", "-ss", f"{pos_s:.6f}",
             "-i", self.ctrl.current_file, "-c", "copy", part2],
        ]
        self.ctrl._run_multi(cmds, "Splitting…")

    def _do_split_equal(self):
        if not self.ctrl.current_file:
            return
        dur = self.ctrl.probe_data.get("duration", 0)
        n   = self.split_n.value()
        if dur <= 0:
            return
        src     = Path(self.ctrl.current_file)
        out_dir = self._pick_folder()
        if not out_dir:
            return

        seg_dur = dur / n
        cmds = []
        for i in range(n):
            ss  = i * seg_dur
            out = str(Path(out_dir) / f"{src.stem}_part{i+1:02d}{src.suffix}")
            cmds.append([
                "ffmpeg", "-y", "-ss", f"{ss:.6f}",
                "-i", self.ctrl.current_file,
                "-t", f"{seg_dur:.6f}", "-c", "copy", out,
            ])
        self.ctrl._run_multi(cmds, f"Splitting into {n} parts…")

    def _do_split_segments(self):
        if not self.ctrl.current_file:
            return
        src     = Path(self.ctrl.current_file)
        out_dir = self._pick_folder()
        if not out_dir:
            return
        seg_t   = self.split_secs.value()
        out_pat = str(Path(out_dir) / f"{src.stem}_%03d{src.suffix}")
        cmd = [
            "ffmpeg", "-y", "-i", self.ctrl.current_file,
            "-c", "copy", "-map", "0",
            "-segment_time", f"{seg_t:.1f}",
            "-reset_timestamps", "1",
            "-f", "segment", out_pat,
        ]
        self.ctrl._run_ffmpeg(cmd, 0, f"Splitting every {seg_t:.0f}s…")


# ── Page: Convert ─────────────────────────────────────────────────────────────

class ConvertPage(QtWidgets.QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self._build_ui()

    def _build_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        card, clay = self._card("CONVERT")

        # Container
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Container:"))
        self.fmt_combo = QtWidgets.QComboBox()
        self.fmt_combo.addItems(VIDEO_FORMATS)
        row.addWidget(self.fmt_combo)
        row.addStretch(1)
        clay.addLayout(row)

        sep1 = QtWidgets.QFrame(); sep1.setObjectName("separator"); clay.addWidget(sep1)

        # Video codec
        vrow = QtWidgets.QHBoxLayout()
        vrow.addWidget(QtWidgets.QLabel("Video codec:"))
        self.vcodec = QtWidgets.QComboBox()
        self.vcodec.addItems(VIDEO_CODECS)
        self.vcodec.currentTextChanged.connect(self._on_vcodec_changed)
        vrow.addWidget(self.vcodec)
        vrow.addSpacing(10)
        self.crf_lbl = QtWidgets.QLabel("CRF:")
        vrow.addWidget(self.crf_lbl)
        self.crf_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.crf_slider.setRange(0, 63)
        self.crf_slider.setValue(23)
        self.crf_slider.setFixedWidth(120)
        vrow.addWidget(self.crf_slider)
        self.crf_val_lbl = QtWidgets.QLabel("23")
        self.crf_val_lbl.setFixedWidth(24)
        self.crf_slider.valueChanged.connect(
            lambda v: self.crf_val_lbl.setText(str(v)))
        vrow.addWidget(self.crf_val_lbl)
        vrow.addSpacing(10)
        vrow.addWidget(QtWidgets.QLabel("Preset:"))
        self.preset = QtWidgets.QComboBox()
        self.preset.addItems(PRESETS_264)
        self.preset.setCurrentText("medium")
        vrow.addWidget(self.preset)
        vrow.addStretch(1)
        clay.addLayout(vrow)

        # VAAPI + two-pass
        hw_row = QtWidgets.QHBoxLayout()
        self.vaapi_cb = QtWidgets.QCheckBox("VAAPI hardware encode")
        self.vaapi_cb.toggled.connect(self._on_vaapi_toggled)
        hw_row.addWidget(self.vaapi_cb)
        self.twopass_cb = QtWidgets.QCheckBox("Two-pass")
        hw_row.addWidget(self.twopass_cb)
        hw_row.addStretch(1)
        clay.addLayout(hw_row)

        sep2 = QtWidgets.QFrame(); sep2.setObjectName("separator"); clay.addWidget(sep2)

        # Audio codec
        arow = QtWidgets.QHBoxLayout()
        arow.addWidget(QtWidgets.QLabel("Audio codec:"))
        self.acodec = QtWidgets.QComboBox()
        self.acodec.addItems(AUDIO_CODECS)
        arow.addWidget(self.acodec)
        arow.addSpacing(10)
        arow.addWidget(QtWidgets.QLabel("Bitrate:"))
        self.abr = QtWidgets.QComboBox()
        self.abr.addItems(AUDIO_BR)
        arow.addWidget(self.abr)
        arow.addStretch(1)
        clay.addLayout(arow)

        sep3 = QtWidgets.QFrame(); sep3.setObjectName("separator"); clay.addWidget(sep3)

        # Resolution + frame rate
        res_row = QtWidgets.QHBoxLayout()
        res_row.addWidget(QtWidgets.QLabel("Resolution:"))
        self.res_combo = QtWidgets.QComboBox()
        self.res_combo.addItems(RESOLUTIONS)
        self.res_combo.currentTextChanged.connect(self._on_res_changed)
        res_row.addWidget(self.res_combo)
        self.custom_w = QtWidgets.QSpinBox()
        self.custom_w.setRange(16, 7680)
        self.custom_w.setValue(1920)
        self.custom_w.setFixedWidth(80)
        self.custom_h = QtWidgets.QSpinBox()
        self.custom_h.setRange(16, 4320)
        self.custom_h.setValue(1080)
        self.custom_h.setFixedWidth(80)
        self.custom_lbl = QtWidgets.QLabel("W:")
        self.custom_x   = QtWidgets.QLabel("×")
        self.custom_h_lbl = QtWidgets.QLabel("H:")
        self.aspect_lock = QtWidgets.QCheckBox("Lock aspect")
        self.aspect_lock.setChecked(True)
        for w in (self.custom_lbl, self.custom_w, self.custom_x,
                  self.custom_h_lbl, self.custom_h, self.aspect_lock):
            res_row.addWidget(w)
        self._custom_widgets = [self.custom_lbl, self.custom_w, self.custom_x,
                                self.custom_h_lbl, self.custom_h, self.aspect_lock]
        for w in self._custom_widgets:
            w.hide()
        res_row.addSpacing(12)
        res_row.addWidget(QtWidgets.QLabel("FPS:"))
        self.fps_combo = QtWidgets.QComboBox()
        self.fps_combo.addItems(FRAMERATES)
        res_row.addWidget(self.fps_combo)
        res_row.addStretch(1)
        clay.addLayout(res_row)

        sep4 = QtWidgets.QFrame(); sep4.setObjectName("separator"); clay.addWidget(sep4)

        # Extra args
        extra_row = QtWidgets.QHBoxLayout()
        extra_row.addWidget(QtWidgets.QLabel("Extra args:"))
        self.extra_args = QtWidgets.QLineEdit()
        self.extra_args.setPlaceholderText("-movflags +faststart  -pix_fmt yuv420p  …")
        extra_row.addWidget(self.extra_args)
        clay.addLayout(extra_row)

        # Convert buttons
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.ctrl._cancel_ffmpeg)
        self.cancel_btn.hide()
        btn_row.addWidget(self.cancel_btn)
        self.convert_btn = QtWidgets.QPushButton("Convert…")
        self.convert_btn.setObjectName("actionBtn")
        self.convert_btn.clicked.connect(self._do_convert)
        btn_row.addWidget(self.convert_btn)
        clay.addLayout(btn_row)

        lay.addWidget(card)
        lay.addStretch(1)
        self._refresh_controls()

    def _card(self, title=""):
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        lay = QtWidgets.QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(8)
        if title:
            lbl = QtWidgets.QLabel(title)
            lbl.setObjectName("sectionLabel")
            lay.addWidget(lbl)
        return card, lay

    def on_file_loaded(self):
        self._refresh_controls()

    def _refresh_controls(self):
        self.convert_btn.setEnabled(self.ctrl.current_file is not None)

    def set_busy(self, busy: bool):
        self.convert_btn.setVisible(not busy)
        self.cancel_btn.setVisible(busy)

    def _on_vcodec_changed(self, codec: str):
        disabled = codec in ("copy", "none")
        for w in (self.crf_slider, self.crf_lbl, self.crf_val_lbl,
                  self.preset, self.vaapi_cb, self.twopass_cb):
            w.setEnabled(not disabled)
        if codec == "libvpx-vp9":
            self.crf_slider.setRange(0, 63)
        elif codec == "libaom-av1":
            self.crf_slider.setRange(0, 63)
            self.crf_slider.setValue(35)
        else:
            self.crf_slider.setRange(0, 51)

    def _on_vaapi_toggled(self, checked: bool):
        self.twopass_cb.setEnabled(not checked)
        if checked:
            self.twopass_cb.setChecked(False)

    def _on_res_changed(self, text: str):
        custom = text == "Custom…"
        for w in self._custom_widgets:
            w.setVisible(custom)

    def _build_vf(self) -> str | None:
        res = self.res_combo.currentText()
        if res == "Original":
            return None
        if res == "Custom…":
            w = self.custom_w.value()
            h = self.custom_h.value()
            if self.aspect_lock.isChecked():
                return f"scale={w}:-2"
            return f"scale={w}:{h}"
        wh = _res_to_wh(res)
        if not wh:
            return None
        return f"scale={wh[0]}:{wh[1]}"

    def _do_convert(self):
        if not self.ctrl.current_file:
            return
        fmt = self.fmt_combo.currentText()
        src = Path(self.ctrl.current_file)
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Converted File",
            str(src.parent / f"{src.stem}_converted.{fmt}"),
            f"{fmt.upper()} (*.{fmt});;All Files (*)",
        )
        if not out:
            return

        dur   = self.ctrl.probe_data.get("duration", 0)
        vaapi = self.vaapi_cb.isChecked()
        vcodec = self.vcodec.currentText()

        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats"]

        if vaapi:
            cmd.extend(["-hwaccel", "vaapi",
                        "-hwaccel_device", VAAPI_DEVICE,
                        "-hwaccel_output_format", "vaapi"])

        cmd.extend(["-i", self.ctrl.current_file])

        # Video
        if vcodec == "none":
            cmd.append("-vn")
        elif vcodec == "copy":
            cmd.extend(["-c:v", "copy"])
        else:
            vf = self._build_vf()
            if vaapi:
                enc = "hevc_vaapi" if vcodec == "libx265" else "h264_vaapi"
                cmd.extend(["-c:v", enc, "-qp", str(self.crf_slider.value())])
                if vf:
                    vaapi_scale = vf.replace("scale=", "scale_vaapi=")
                    cmd.extend(["-vf", vaapi_scale])
            else:
                cmd.extend(["-c:v", vcodec, "-crf", str(self.crf_slider.value())])
                if vcodec in ("libx264", "libx265"):
                    cmd.extend(["-preset", self.preset.currentText()])
                if vcodec == "libvpx-vp9":
                    cmd.extend(["-b:v", "0"])
                if vf:
                    cmd.extend(["-vf", vf])

        fps = self.fps_combo.currentText()
        if fps != "Original":
            cmd.extend(["-r", fps])

        # Audio
        acodec = self.acodec.currentText()
        if acodec == "none":
            cmd.append("-an")
        elif acodec == "copy":
            cmd.extend(["-c:a", "copy"])
        else:
            cmd.extend(["-c:a", acodec])
            abr = self.abr.currentText()
            if abr != "best":
                cmd.extend(["-b:a", abr])

        # Extra args
        extra = self.extra_args.text().strip()
        if extra:
            cmd.extend(extra.split())

        cmd.append(out)

        if self.twopass_cb.isChecked() and vcodec not in ("copy", "none"):
            self._do_twopass(cmd, out, dur)
        else:
            self.ctrl._run_ffmpeg(cmd, dur, "Converting…")

    def _do_twopass(self, cmd_pass2: list, out: str, dur: float):
        # Build pass-1 command (same but -pass 1 -f null /dev/null)
        cmd1 = []
        skip_next = False
        for token in cmd_pass2:
            if skip_next:
                skip_next = False
                continue
            if token in ("-progress", "-nostats"):
                continue
            if token == "pipe:1":
                skip_next = False
                continue
            cmd1.append(token)
        # Remove output file, add pass flags
        cmd1 = cmd1[:-1]  # remove output
        cmd1.extend(["-pass", "1", "-f", "null", "/dev/null"])
        cmd_pass2 = cmd_pass2[:-1] + ["-pass", "2", out]
        self.ctrl._run_multi([cmd1, cmd_pass2], "Two-pass encode…")


# ── Page: Filters ─────────────────────────────────────────────────────────────

class FiltersPage(QtWidgets.QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self._build_ui()

    def _section(self, parent_lay, title):
        lbl = QtWidgets.QLabel(title)
        lbl.setObjectName("sectionLabel")
        parent_lay.addWidget(lbl)

    def _card(self, title=""):
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        lay = QtWidgets.QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(8)
        if title:
            lbl = QtWidgets.QLabel(title)
            lbl.setObjectName("sectionLabel")
            lay.addWidget(lbl)
        return card, lay

    def _build_ui(self):
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        inner = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(inner)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        # ── Resize ──
        rc, rlay = self._card("RESIZE")
        rrow = QtWidgets.QHBoxLayout()
        self.resize_res = QtWidgets.QComboBox()
        self.resize_res.addItems(RESOLUTIONS)
        self.resize_res.currentTextChanged.connect(self._on_resize_res_changed)
        rrow.addWidget(self.resize_res)
        self.rw_lbl = QtWidgets.QLabel("W:")
        self.rw = QtWidgets.QSpinBox(); self.rw.setRange(16, 7680); self.rw.setValue(1920)
        self.rw.setFixedWidth(75)
        self.rx_lbl = QtWidgets.QLabel("×")
        self.rh_lbl = QtWidgets.QLabel("H:")
        self.rh = QtWidgets.QSpinBox(); self.rh.setRange(16, 4320); self.rh.setValue(1080)
        self.rh.setFixedWidth(75)
        self.r_aspect = QtWidgets.QCheckBox("Lock aspect")
        self.r_aspect.setChecked(True)
        self._resize_custom = [self.rw_lbl, self.rw, self.rx_lbl,
                               self.rh_lbl, self.rh, self.r_aspect]
        for w in [self.rw_lbl, self.rw, self.rx_lbl,
                  self.rh_lbl, self.rh, self.r_aspect]:
            rrow.addWidget(w)
            w.hide()
        rrow.addStretch(1)
        rlay.addLayout(rrow)
        lay.addWidget(rc)

        # ── Crop ──
        cc, clay = self._card("CROP")
        crow = QtWidgets.QHBoxLayout()
        for label, attr, default in [
            ("W:", "crop_w", 1920), ("H:", "crop_h", 1080),
            ("X:", "crop_x", 0),   ("Y:", "crop_y", 0),
        ]:
            crow.addWidget(QtWidgets.QLabel(label))
            sb = QtWidgets.QSpinBox()
            sb.setRange(0, 9999)
            sb.setValue(default)
            sb.setFixedWidth(75)
            setattr(self, attr, sb)
            crow.addWidget(sb)
            crow.addSpacing(4)
        self.crop_enabled = QtWidgets.QCheckBox("Enable crop")
        crow.addWidget(self.crop_enabled)
        crow.addStretch(1)
        clay.addLayout(crow)
        lay.addWidget(cc)

        # ── Transform ──
        tc, tlay = self._card("ROTATE / FLIP")
        trow = QtWidgets.QHBoxLayout()
        self.rot_none   = QtWidgets.QRadioButton("None")
        self.rot_90cw   = QtWidgets.QRadioButton("90° CW")
        self.rot_90ccw  = QtWidgets.QRadioButton("90° CCW")
        self.rot_180    = QtWidgets.QRadioButton("180°")
        self.rot_none.setChecked(True)
        for rb in (self.rot_none, self.rot_90cw, self.rot_90ccw, self.rot_180):
            trow.addWidget(rb)
        trow.addSpacing(16)
        self.flip_h = QtWidgets.QCheckBox("Flip H")
        self.flip_v = QtWidgets.QCheckBox("Flip V")
        trow.addWidget(self.flip_h)
        trow.addWidget(self.flip_v)
        trow.addStretch(1)
        tlay.addLayout(trow)
        lay.addWidget(tc)

        # ── Speed ──
        sc, slay2 = self._card("SPEED")
        sprow = QtWidgets.QHBoxLayout()
        sprow.addWidget(QtWidgets.QLabel("Speed:"))
        self.speed_combo = QtWidgets.QComboBox()
        for v in SPEED_VALUES:
            self.speed_combo.addItem(f"{v}×", v)
        self.speed_combo.setCurrentIndex(SPEED_VALUES.index(1.0))
        sprow.addWidget(self.speed_combo)
        self.pitch_cb = QtWidgets.QCheckBox("Correct audio pitch")
        self.pitch_cb.setChecked(True)
        sprow.addWidget(self.pitch_cb)
        sprow.addStretch(1)
        slay2.addLayout(sprow)
        lay.addWidget(sc)

        # ── Effects ──
        ec, elay = self._card("EFFECTS")
        eff_row = QtWidgets.QHBoxLayout()
        self.deint_cb  = QtWidgets.QCheckBox("Deinterlace (yadif)")
        self.denoise_cb = QtWidgets.QCheckBox("Denoise")
        self.denoise_str = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.denoise_str.setRange(1, 10); self.denoise_str.setValue(3)
        self.denoise_str.setFixedWidth(80)
        self.sharpen_cb  = QtWidgets.QCheckBox("Sharpen")
        self.sharpen_str = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sharpen_str.setRange(1, 20); self.sharpen_str.setValue(5)
        self.sharpen_str.setFixedWidth(80)
        self.blur_cb  = QtWidgets.QCheckBox("Blur")
        self.blur_str = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.blur_str.setRange(1, 20); self.blur_str.setValue(3)
        self.blur_str.setFixedWidth(80)
        for w in (self.deint_cb, self.denoise_cb, self.denoise_str,
                  self.sharpen_cb, self.sharpen_str,
                  self.blur_cb, self.blur_str):
            eff_row.addWidget(w)
        eff_row.addStretch(1)
        elay.addLayout(eff_row)
        lay.addWidget(ec)

        # ── Colour ──
        clrc, clrlay = self._card("COLOUR")

        def _slider_row(label, attr_name, lo, hi, default, scale=100):
            row = QtWidgets.QHBoxLayout()
            row.addWidget(QtWidgets.QLabel(label))
            sl = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            sl.setRange(lo, hi)
            sl.setValue(default)
            sl.setFixedWidth(140)
            val_lbl = QtWidgets.QLabel(f"{default/scale:.2f}")
            val_lbl.setFixedWidth(36)
            val_lbl.setObjectName("dimLabel")
            sl.valueChanged.connect(lambda v, l=val_lbl, s=scale: l.setText(f"{v/s:.2f}"))
            reset = QtWidgets.QPushButton("↺")
            reset.setObjectName("nudgeBtn")
            reset.setFixedSize(22, 22)
            reset.clicked.connect(lambda _, s=sl, d=default: s.setValue(d))
            setattr(self, attr_name, sl)
            row.addWidget(sl)
            row.addWidget(val_lbl)
            row.addWidget(reset)
            row.addSpacing(16)
            return row

        br_row = _slider_row("Brightness:", "brightness", -100, 100, 0)
        ct_row = _slider_row("Contrast:",   "contrast",   10,  300, 100)
        st_row = _slider_row("Saturation:", "saturation", 0,   300, 100)
        gm_row = _slider_row("Gamma:",      "gamma",      10,  300, 100)

        combined = QtWidgets.QHBoxLayout()
        combined.addLayout(br_row)
        combined.addLayout(ct_row)
        clrlay.addLayout(combined)
        combined2 = QtWidgets.QHBoxLayout()
        combined2.addLayout(st_row)
        combined2.addLayout(gm_row)
        clrlay.addLayout(combined2)
        lay.addWidget(clrc)

        # ── Fade ──
        fdc, fdlay = self._card("FADE")
        frow = QtWidgets.QHBoxLayout()
        self.fade_in_cb = QtWidgets.QCheckBox("Fade in:")
        self.fade_in_dur = QtWidgets.QDoubleSpinBox()
        self.fade_in_dur.setRange(0.1, 30.0); self.fade_in_dur.setValue(1.0)
        self.fade_in_dur.setSuffix(" s"); self.fade_in_dur.setFixedWidth(80)
        self.fade_out_cb = QtWidgets.QCheckBox("Fade out:")
        self.fade_out_dur = QtWidgets.QDoubleSpinBox()
        self.fade_out_dur.setRange(0.1, 30.0); self.fade_out_dur.setValue(1.0)
        self.fade_out_dur.setSuffix(" s"); self.fade_out_dur.setFixedWidth(80)
        for w in (self.fade_in_cb, self.fade_in_dur,
                  self.fade_out_cb, self.fade_out_dur):
            frow.addWidget(w)
        frow.addStretch(1)
        fdlay.addLayout(frow)
        lay.addWidget(fdc)

        # ── Watermark ──
        wc, wlay = self._card("WATERMARK / OVERLAY")
        wrow = QtWidgets.QHBoxLayout()
        self.wm_path = QtWidgets.QLineEdit()
        self.wm_path.setPlaceholderText("Image path…")
        wrow.addWidget(self.wm_path, 1)
        wm_pick = QtWidgets.QPushButton("Browse…")
        wm_pick.setObjectName("openBtn")
        wm_pick.clicked.connect(self._pick_watermark)
        wrow.addWidget(wm_pick)
        wrow.addSpacing(8)
        wrow.addWidget(QtWidgets.QLabel("Position:"))
        self.wm_pos = QtWidgets.QComboBox()
        self.wm_pos.addItems(OVERLAY_POS)
        self.wm_pos.setCurrentText("Bottom-Right")
        wrow.addWidget(self.wm_pos)
        wrow.addSpacing(8)
        wrow.addWidget(QtWidgets.QLabel("Margin:"))
        self.wm_margin = QtWidgets.QSpinBox()
        self.wm_margin.setRange(0, 200); self.wm_margin.setValue(10)
        self.wm_margin.setFixedWidth(65)
        wrow.addWidget(self.wm_margin)
        wlay.addLayout(wrow)
        lay.addWidget(wc)

        # ── Pad ──
        pc, play_ = self._card("PAD / LETTERBOX")
        prow = QtWidgets.QHBoxLayout()
        prow.addWidget(QtWidgets.QLabel("Target W:"))
        self.pad_w = QtWidgets.QSpinBox()
        self.pad_w.setRange(0, 7680); self.pad_w.setValue(1920); self.pad_w.setFixedWidth(80)
        prow.addWidget(self.pad_w)
        prow.addWidget(QtWidgets.QLabel("H:"))
        self.pad_h = QtWidgets.QSpinBox()
        self.pad_h.setRange(0, 4320); self.pad_h.setValue(1080); self.pad_h.setFixedWidth(80)
        prow.addWidget(self.pad_h)
        prow.addWidget(QtWidgets.QLabel("Colour:"))
        self.pad_color = QtWidgets.QLineEdit("black")
        self.pad_color.setFixedWidth(70)
        prow.addWidget(self.pad_color)
        self.pad_enabled = QtWidgets.QCheckBox("Enable pad")
        prow.addWidget(self.pad_enabled)
        prow.addStretch(1)
        play_.addLayout(prow)
        lay.addWidget(pc)

        # ── Output options + Apply ──
        oc, olay = self._card("OUTPUT")
        out_row = QtWidgets.QHBoxLayout()
        out_row.addWidget(QtWidgets.QLabel("Format:"))
        self.out_fmt = QtWidgets.QComboBox()
        self.out_fmt.addItems(VIDEO_FORMATS)
        out_row.addWidget(self.out_fmt)
        out_row.addSpacing(8)
        out_row.addWidget(QtWidgets.QLabel("Video codec:"))
        self.out_vcodec = QtWidgets.QComboBox()
        self.out_vcodec.addItems([c for c in VIDEO_CODECS if c != "none"])
        out_row.addWidget(self.out_vcodec)
        out_row.addSpacing(8)
        out_row.addWidget(QtWidgets.QLabel("CRF:"))
        self.out_crf = QtWidgets.QSpinBox()
        self.out_crf.setRange(0, 51); self.out_crf.setValue(23); self.out_crf.setFixedWidth(60)
        out_row.addWidget(self.out_crf)
        out_row.addStretch(1)
        self.apply_btn = QtWidgets.QPushButton("Apply Filters…")
        self.apply_btn.setObjectName("actionBtn")
        self.apply_btn.clicked.connect(self._do_apply)
        out_row.addWidget(self.apply_btn)
        olay.addLayout(out_row)
        lay.addWidget(oc)

        lay.addStretch(1)
        scroll.setWidget(inner)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self._refresh_controls()

    def _pick_watermark(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Watermark Image", str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.svg *.webp);;All Files (*)",
        )
        if path:
            self.wm_path.setText(path)

    def _on_resize_res_changed(self, text: str):
        custom = text == "Custom…"
        for w in self._resize_custom:
            w.setVisible(custom)

    def on_file_loaded(self):
        pd = self.ctrl.probe_data
        w, h = pd.get("width", 1920), pd.get("height", 1080)
        self.crop_w.setValue(w); self.crop_h.setValue(h)
        self.pad_w.setValue(w);  self.pad_h.setValue(h)
        self._refresh_controls()

    def _refresh_controls(self):
        self.apply_btn.setEnabled(self.ctrl.current_file is not None)

    def _build_filter_chain(self):
        vf, af = [], []
        pd  = self.ctrl.probe_data
        dur = pd.get("duration", 0)
        fps = pd.get("fps", 25.0)

        # Deinterlace first
        if self.deint_cb.isChecked():
            vf.append("yadif")

        # Crop
        if self.crop_enabled.isChecked():
            vf.append(f"crop={self.crop_w.value()}:{self.crop_h.value()}"
                      f":{self.crop_x.value()}:{self.crop_y.value()}")

        # Resize
        res = self.resize_res.currentText()
        if res != "Original":
            if res == "Custom…":
                w = self.rw.value()
                if self.r_aspect.isChecked():
                    vf.append(f"scale={w}:-2")
                else:
                    vf.append(f"scale={w}:{self.rh.value()}")
            else:
                wh = _res_to_wh(res)
                if wh:
                    vf.append(f"scale={wh[0]}:{wh[1]}")

        # Rotate / flip
        if self.rot_90cw.isChecked():
            vf.append("transpose=1")
        elif self.rot_90ccw.isChecked():
            vf.append("transpose=2")
        elif self.rot_180.isChecked():
            vf.append("transpose=1,transpose=1")
        if self.flip_h.isChecked():
            vf.append("hflip")
        if self.flip_v.isChecked():
            vf.append("vflip")

        # Speed
        speed = self.speed_combo.currentData()
        if speed != 1.0:
            vf.append(f"setpts={1.0/speed:.6f}*PTS")
            if self.pitch_cb.isChecked():
                af.extend(_atempo_chain(speed))
            else:
                af.extend(_atempo_chain(speed) + ["aresample=async=1"])

        # Colour eq
        br = self.brightness.value() / 100.0
        ct = self.contrast.value()   / 100.0
        st = self.saturation.value() / 100.0
        gm = self.gamma.value()      / 100.0
        if any(abs(v - dv) > 0.001 for v, dv in
               [(br, 0), (ct, 1), (st, 1), (gm, 1)]):
            vf.append(f"eq=brightness={br:.3f}:contrast={ct:.3f}"
                      f":saturation={st:.3f}:gamma={gm:.3f}")

        # Effects
        if self.denoise_cb.isChecked():
            s = self.denoise_str.value()
            vf.append(f"hqdn3d={s}:{s*0.75:.1f}:{s*1.5:.1f}:{s*1.125:.2f}")
        if self.sharpen_cb.isChecked():
            s = self.sharpen_str.value() / 10.0
            vf.append(f"unsharp=5:5:{s}:5:5:0.0")
        if self.blur_cb.isChecked():
            vf.append(f"gblur=sigma={self.blur_str.value()}")

        # Fade in/out
        if self.fade_in_cb.isChecked():
            frames = int(self.fade_in_dur.value() * fps)
            vf.append(f"fade=in:0:{frames}")
        if self.fade_out_cb.isChecked():
            fade_dur = self.fade_out_dur.value()
            start_f  = max(0, int((dur - fade_dur) * fps))
            end_f    = int(fade_dur * fps)
            vf.append(f"fade=out:{start_f}:{end_f}")

        # Pad
        if self.pad_enabled.isChecked():
            pw  = self.pad_w.value()
            ph  = self.pad_h.value()
            col = self.pad_color.text().strip() or "black"
            vf.append(f"pad={pw}:{ph}:(ow-iw)/2:(oh-ih)/2:{col}")

        return vf, af

    def _do_apply(self):
        if not self.ctrl.current_file:
            return
        vf, af = self._build_filter_chain()
        wm = self.wm_path.text().strip()
        fmt    = self.out_fmt.currentText()
        src    = Path(self.ctrl.current_file)
        dur    = self.ctrl.probe_data.get("duration", 0)
        vcodec = self.out_vcodec.currentText()
        crf    = self.out_crf.value()

        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Filtered File",
            str(src.parent / f"{src.stem}_filtered.{fmt}"),
            f"{fmt.upper()} (*.{fmt});;All Files (*)",
        )
        if not out:
            return

        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file]

        if wm and Path(wm).exists():
            cmd.extend(["-i", wm])
            vf_str  = ",".join(vf) if vf else ""
            if vf_str:
                fc = f"[0:v]{vf_str}[tmp];[tmp][1:v]overlay={_overlay_expr(self.wm_pos.currentText(), self.wm_margin.value())}[vout]"
            else:
                fc = f"[0:v][1:v]overlay={_overlay_expr(self.wm_pos.currentText(), self.wm_margin.value())}[vout]"
            cmd.extend(["-filter_complex", fc, "-map", "[vout]", "-map", "0:a?"])
        else:
            if vf:
                cmd.extend(["-vf", ",".join(vf)])

        if af:
            cmd.extend(["-af", ",".join(af)])

        cmd.extend(["-c:v", vcodec, "-crf", str(crf), "-c:a", "aac"])
        cmd.append(out)
        self.ctrl._run_ffmpeg(cmd, dur, "Applying filters…")


# ── Page: Audio ───────────────────────────────────────────────────────────────

class AudioPage(QtWidgets.QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self._build_ui()

    def _card(self, title=""):
        card = QtWidgets.QFrame(); card.setObjectName("card")
        lay = QtWidgets.QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10); lay.setSpacing(8)
        if title:
            lbl = QtWidgets.QLabel(title); lbl.setObjectName("sectionLabel")
            lay.addWidget(lbl)
        return card, lay

    def _hrow(self): r = QtWidgets.QHBoxLayout(); return r

    def _build_ui(self):
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        inner = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(inner)
        lay.setContentsMargins(12, 10, 12, 10); lay.setSpacing(10)

        # Extract audio
        ec, elay = self._card("EXTRACT AUDIO")
        er = self._hrow()
        er.addWidget(QtWidgets.QLabel("Format:"))
        self.extract_fmt = QtWidgets.QComboBox(); self.extract_fmt.addItems(AUDIO_FORMATS)
        er.addWidget(self.extract_fmt)
        self.extract_norm = QtWidgets.QCheckBox("Normalize (loudnorm)")
        er.addWidget(self.extract_norm)
        er.addStretch(1)
        self.extract_btn = QtWidgets.QPushButton("Extract Audio…")
        self.extract_btn.setObjectName("actionBtn")
        self.extract_btn.clicked.connect(self._do_extract)
        er.addWidget(self.extract_btn)
        elay.addLayout(er)
        lay.addWidget(ec)

        # Remove audio
        rc, rlay = self._card("REMOVE AUDIO")
        rr = self._hrow()
        lbl = QtWidgets.QLabel("Strip all audio tracks from the video")
        lbl.setObjectName("fileInfoLabel"); rr.addWidget(lbl); rr.addStretch(1)
        self.mute_btn = QtWidgets.QPushButton("Mute Video…")
        self.mute_btn.setObjectName("actionBtn"); self.mute_btn.clicked.connect(self._do_mute)
        rr.addWidget(self.mute_btn); rlay.addLayout(rr); lay.addWidget(rc)

        # Normalize
        nc, nlay = self._card("NORMALIZE (EBU R128)")
        nrow = self._hrow()
        nrow.addWidget(QtWidgets.QLabel("Target I:"))
        self.norm_i = QtWidgets.QDoubleSpinBox(); self.norm_i.setRange(-70, -5)
        self.norm_i.setValue(-16); self.norm_i.setSuffix(" LUFS"); self.norm_i.setFixedWidth(110)
        nrow.addWidget(self.norm_i)
        nrow.addSpacing(8); nrow.addWidget(QtWidgets.QLabel("TP:"))
        self.norm_tp = QtWidgets.QDoubleSpinBox(); self.norm_tp.setRange(-9, 0)
        self.norm_tp.setValue(-1.5); self.norm_tp.setSuffix(" dBTP"); self.norm_tp.setFixedWidth(100)
        nrow.addWidget(self.norm_tp)
        nrow.addSpacing(8); nrow.addWidget(QtWidgets.QLabel("LRA:"))
        self.norm_lra = QtWidgets.QDoubleSpinBox(); self.norm_lra.setRange(1, 50)
        self.norm_lra.setValue(11); self.norm_lra.setSuffix(" LU"); self.norm_lra.setFixedWidth(90)
        nrow.addWidget(self.norm_lra)
        nrow.addStretch(1)
        self.norm_btn = QtWidgets.QPushButton("Normalize…")
        self.norm_btn.setObjectName("actionBtn"); self.norm_btn.clicked.connect(self._do_normalize)
        nrow.addWidget(self.norm_btn); nlay.addLayout(nrow); lay.addWidget(nc)

        # Volume
        vc, vlay = self._card("VOLUME ADJUST")
        vrow = self._hrow()
        vrow.addWidget(QtWidgets.QLabel("Volume:"))
        self.vol_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.vol_slider.setRange(-20, 20); self.vol_slider.setValue(0); self.vol_slider.setFixedWidth(160)
        vrow.addWidget(self.vol_slider)
        self.vol_lbl = QtWidgets.QLabel("0 dB"); self.vol_lbl.setFixedWidth(50)
        self.vol_lbl.setObjectName("dimLabel")
        self.vol_slider.valueChanged.connect(lambda v: self.vol_lbl.setText(f"{v:+d} dB"))
        vrow.addWidget(self.vol_lbl)
        vrow.addStretch(1)
        self.vol_btn = QtWidgets.QPushButton("Apply Volume…")
        self.vol_btn.setObjectName("actionBtn"); self.vol_btn.clicked.connect(self._do_volume)
        vrow.addWidget(self.vol_btn); vlay.addLayout(vrow); lay.addWidget(vc)

        # Delay
        dc, dlay = self._card("AUDIO DELAY")
        dr = self._hrow()
        dr.addWidget(QtWidgets.QLabel("Delay:"))
        self.delay_ms = QtWidgets.QDoubleSpinBox(); self.delay_ms.setRange(-10000, 10000)
        self.delay_ms.setValue(0); self.delay_ms.setSuffix(" ms"); self.delay_ms.setFixedWidth(110)
        dr.addWidget(self.delay_ms)
        lbl2 = QtWidgets.QLabel("(positive = audio later, negative = audio earlier)")
        lbl2.setObjectName("fileInfoLabel"); dr.addWidget(lbl2)
        dr.addStretch(1)
        self.delay_btn = QtWidgets.QPushButton("Apply Delay…")
        self.delay_btn.setObjectName("actionBtn"); self.delay_btn.clicked.connect(self._do_delay)
        dr.addWidget(self.delay_btn); dlay.addLayout(dr); lay.addWidget(dc)

        # Fade
        fdc, fdlay = self._card("AUDIO FADE")
        fr = self._hrow()
        self.afx_fade_in = QtWidgets.QCheckBox("Fade in:")
        self.afx_fade_in_dur = QtWidgets.QDoubleSpinBox()
        self.afx_fade_in_dur.setRange(0.1, 30); self.afx_fade_in_dur.setValue(1.0)
        self.afx_fade_in_dur.setSuffix(" s"); self.afx_fade_in_dur.setFixedWidth(80)
        self.afx_fade_out = QtWidgets.QCheckBox("Fade out:")
        self.afx_fade_out_dur = QtWidgets.QDoubleSpinBox()
        self.afx_fade_out_dur.setRange(0.1, 30); self.afx_fade_out_dur.setValue(1.0)
        self.afx_fade_out_dur.setSuffix(" s"); self.afx_fade_out_dur.setFixedWidth(80)
        for w in (self.afx_fade_in, self.afx_fade_in_dur,
                  self.afx_fade_out, self.afx_fade_out_dur):
            fr.addWidget(w)
        fr.addStretch(1)
        self.afade_btn = QtWidgets.QPushButton("Apply Fade…")
        self.afade_btn.setObjectName("actionBtn"); self.afade_btn.clicked.connect(self._do_afade)
        fr.addWidget(self.afade_btn); fdlay.addLayout(fr); lay.addWidget(fdc)

        # Replace audio
        repc, replay = self._card("REPLACE AUDIO")
        repr_ = self._hrow()
        self.rep_path = QtWidgets.QLineEdit(); self.rep_path.setPlaceholderText("Audio file…")
        repr_.addWidget(self.rep_path, 1)
        rep_pick = QtWidgets.QPushButton("Browse…"); rep_pick.setObjectName("openBtn")
        rep_pick.clicked.connect(self._pick_audio_file); repr_.addWidget(rep_pick)
        repr_.addSpacing(8); repr_.addWidget(QtWidgets.QLabel("Offset:"))
        self.rep_offset = QtWidgets.QDoubleSpinBox(); self.rep_offset.setRange(0, 3600)
        self.rep_offset.setSuffix(" s"); self.rep_offset.setFixedWidth(90)
        repr_.addWidget(self.rep_offset)
        repr_.addStretch(0)
        self.rep_btn = QtWidgets.QPushButton("Replace…")
        self.rep_btn.setObjectName("actionBtn"); self.rep_btn.clicked.connect(self._do_replace)
        repr_.addWidget(self.rep_btn); replay.addLayout(repr_); lay.addWidget(repc)

        lay.addStretch(1)
        scroll.setWidget(inner)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0); outer.addWidget(scroll)
        self._action_btns = [self.extract_btn, self.mute_btn, self.norm_btn,
                             self.vol_btn, self.delay_btn, self.afade_btn, self.rep_btn]
        self._refresh_controls()

    def on_file_loaded(self): self._refresh_controls()

    def _refresh_controls(self):
        has = self.ctrl.current_file is not None
        for b in self._action_btns: b.setEnabled(has)

    def _pick_audio_file(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Audio File", str(Path.home()),
            "Audio (*.mp3 *.flac *.wav *.ogg *.opus *.m4a *.aac);;All Files (*)")
        if p: self.rep_path.setText(p)

    def _save_as(self, suffix_hint: str) -> str | None:
        src = Path(self.ctrl.current_file)
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Output",
            str(src.parent / f"{src.stem}{suffix_hint}"),
            "All Files (*)")
        return out or None

    def _do_extract(self):
        if not self.ctrl.current_file: return
        fmt = self.extract_fmt.currentText()
        src = Path(self.ctrl.current_file)
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Audio",
            str(src.parent / f"{src.stem}.{fmt}"),
            f"{fmt.upper()} (*.{fmt})")
        if not out: return
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file, "-vn"]
        if self.extract_norm.isChecked():
            cmd.extend(["-af", "loudnorm"])
        cmd.append(out)
        self.ctrl._run_ffmpeg(cmd, self.ctrl.probe_data.get("duration", 0), "Extracting audio…")

    def _do_mute(self):
        if not self.ctrl.current_file: return
        out = self._save_as("_muted.mp4")
        if not out: return
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file, "-an", "-c:v", "copy", out]
        self.ctrl._run_ffmpeg(cmd, self.ctrl.probe_data.get("duration", 0), "Removing audio…")

    def _do_normalize(self):
        if not self.ctrl.current_file: return
        out = self._save_as("_norm.mp4")
        if not out: return
        af = (f"loudnorm=I={self.norm_i.value():.1f}"
              f":TP={self.norm_tp.value():.1f}"
              f":LRA={self.norm_lra.value():.1f}")
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file, "-af", af, "-c:v", "copy", out]
        self.ctrl._run_ffmpeg(cmd, self.ctrl.probe_data.get("duration", 0), "Normalizing…")

    def _do_volume(self):
        if not self.ctrl.current_file: return
        out = self._save_as("_vol.mp4")
        if not out: return
        db = self.vol_slider.value()
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file,
               "-af", f"volume={db}dB", "-c:v", "copy", out]
        self.ctrl._run_ffmpeg(cmd, self.ctrl.probe_data.get("duration", 0), "Adjusting volume…")

    def _do_delay(self):
        if not self.ctrl.current_file: return
        out = self._save_as("_delay.mp4")
        if not out: return
        ms = self.delay_ms.value()
        if ms >= 0:
            af = f"adelay={ms:.0f}:all=1"
        else:
            af = f"atrim=start={abs(ms)/1000:.3f},asetpts=PTS-STARTPTS"
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file,
               "-af", af, "-c:v", "copy", out]
        self.ctrl._run_ffmpeg(cmd, self.ctrl.probe_data.get("duration", 0), "Applying delay…")

    def _do_afade(self):
        if not self.ctrl.current_file: return
        out = self._save_as("_afade.mp4")
        if not out: return
        dur = self.ctrl.probe_data.get("duration", 0)
        parts = []
        if self.afx_fade_in.isChecked():
            parts.append(f"afade=t=in:st=0:d={self.afx_fade_in_dur.value():.2f}")
        if self.afx_fade_out.isChecked():
            st = max(0, dur - self.afx_fade_out_dur.value())
            parts.append(f"afade=t=out:st={st:.3f}:d={self.afx_fade_out_dur.value():.2f}")
        if not parts:
            QtWidgets.QMessageBox.information(self, "Nothing selected", "Enable fade in or fade out.")
            return
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file,
               "-af", ",".join(parts), "-c:v", "copy", out]
        self.ctrl._run_ffmpeg(cmd, dur, "Applying audio fade…")

    def _do_replace(self):
        if not self.ctrl.current_file: return
        audio_path = self.rep_path.text().strip()
        if not audio_path or not Path(audio_path).exists():
            QtWidgets.QMessageBox.warning(self, "No File", "Select an audio file first.")
            return
        out = self._save_as("_replaced.mp4")
        if not out: return
        offset = self.rep_offset.value()
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file]
        if offset > 0:
            cmd.extend(["-ss", f"{offset:.3f}"])
        cmd.extend(["-i", audio_path,
                    "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0",
                    "-shortest", out])
        self.ctrl._run_ffmpeg(cmd, self.ctrl.probe_data.get("duration", 0), "Replacing audio…")


# ── Page: Frames ──────────────────────────────────────────────────────────────

class FramesPage(QtWidgets.QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self._build_ui()

    def _card(self, title=""):
        card = QtWidgets.QFrame(); card.setObjectName("card")
        lay = QtWidgets.QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10); lay.setSpacing(8)
        if title:
            lbl = QtWidgets.QLabel(title); lbl.setObjectName("sectionLabel"); lay.addWidget(lbl)
        return card, lay

    def _build_ui(self):
        scroll = QtWidgets.QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        inner = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(inner)
        lay.setContentsMargins(12, 10, 12, 10); lay.setSpacing(10)

        # Capture frame
        cc, clay = self._card("CAPTURE FRAME")
        cr = QtWidgets.QHBoxLayout()
        cr.addWidget(QtWidgets.QLabel("Format:"))
        self.cap_fmt = QtWidgets.QComboBox(); self.cap_fmt.addItems(FRAME_FMTS)
        cr.addWidget(self.cap_fmt)
        cr.addSpacing(8); cr.addWidget(QtWidgets.QLabel("Quality:"))
        self.cap_q = QtWidgets.QSpinBox(); self.cap_q.setRange(1, 31); self.cap_q.setValue(2)
        self.cap_q.setFixedWidth(60); cr.addWidget(self.cap_q)
        cr.addStretch(1)
        self.cap_btn = QtWidgets.QPushButton("Capture Frame…")
        self.cap_btn.setObjectName("actionBtn"); self.cap_btn.clicked.connect(self._do_capture)
        cr.addWidget(self.cap_btn); clay.addLayout(cr); lay.addWidget(cc)

        # Extract frames
        xc, xlay = self._card("EXTRACT FRAMES")
        xr1 = QtWidgets.QHBoxLayout()
        self.ext_mode = QtWidgets.QComboBox()
        self.ext_mode.addItems(["Every N seconds", "Every Nth frame", "All frames"])
        xr1.addWidget(self.ext_mode)
        xr1.addSpacing(8); xr1.addWidget(QtWidgets.QLabel("N:"))
        self.ext_n = QtWidgets.QDoubleSpinBox(); self.ext_n.setRange(0.01, 3600)
        self.ext_n.setValue(1.0); self.ext_n.setFixedWidth(90)
        xr1.addWidget(self.ext_n)
        xr1.addSpacing(8); xr1.addWidget(QtWidgets.QLabel("Format:"))
        self.ext_fmt = QtWidgets.QComboBox(); self.ext_fmt.addItems(FRAME_FMTS)
        xr1.addWidget(self.ext_fmt); xr1.addStretch(1)
        self.ext_btn = QtWidgets.QPushButton("Extract Frames…")
        self.ext_btn.setObjectName("actionBtn"); self.ext_btn.clicked.connect(self._do_extract_frames)
        xr1.addWidget(self.ext_btn); xlay.addLayout(xr1); lay.addWidget(xc)

        # GIF
        gc, glay = self._card("CREATE GIF")
        gr1 = QtWidgets.QHBoxLayout()
        gr1.addWidget(QtWidgets.QLabel("Start:"))
        self.gif_start = TimeSpinWidget(""); gr1.addWidget(self.gif_start)
        gr1.addWidget(QtWidgets.QLabel("End:"))
        self.gif_end = TimeSpinWidget(""); gr1.addWidget(self.gif_end)
        gr1.addStretch(1); glay.addLayout(gr1)
        gr2 = QtWidgets.QHBoxLayout()
        gr2.addWidget(QtWidgets.QLabel("FPS:"))
        self.gif_fps = QtWidgets.QSpinBox(); self.gif_fps.setRange(1, 30); self.gif_fps.setValue(10)
        self.gif_fps.setFixedWidth(60); gr2.addWidget(self.gif_fps)
        gr2.addSpacing(8); gr2.addWidget(QtWidgets.QLabel("Width:"))
        self.gif_w = QtWidgets.QSpinBox(); self.gif_w.setRange(64, 1920); self.gif_w.setValue(480)
        self.gif_w.setFixedWidth(80); gr2.addWidget(self.gif_w)
        gr2.addSpacing(8); gr2.addWidget(QtWidgets.QLabel("Loops:"))
        self.gif_loops = QtWidgets.QSpinBox(); self.gif_loops.setRange(0, 100)
        self.gif_loops.setValue(0); self.gif_loops.setSpecialValueText("∞"); self.gif_loops.setFixedWidth(60)
        gr2.addWidget(self.gif_loops)
        gr2.addSpacing(8)
        self.gif_dither = QtWidgets.QComboBox()
        self.gif_dither.addItems(["bayer", "floyd_steinberg", "sierra2_4a", "none"])
        gr2.addWidget(self.gif_dither)
        gr2.addStretch(1)
        self.gif_btn = QtWidgets.QPushButton("Create GIF…")
        self.gif_btn.setObjectName("actionBtn"); self.gif_btn.clicked.connect(self._do_gif)
        gr2.addWidget(self.gif_btn); glay.addLayout(gr2); lay.addWidget(gc)

        # Thumbnail
        thc, thlay = self._card("THUMBNAIL / POSTER")
        thr = QtWidgets.QHBoxLayout()
        thr.addWidget(QtWidgets.QLabel("At:"))
        self.thumb_time = TimeSpinWidget(""); thr.addWidget(self.thumb_time)
        thr.addSpacing(8); thr.addWidget(QtWidgets.QLabel("Format:"))
        self.thumb_fmt = QtWidgets.QComboBox(); self.thumb_fmt.addItems(["jpg", "png", "webp"])
        thr.addWidget(self.thumb_fmt)
        thr.addStretch(1)
        self.thumb_btn = QtWidgets.QPushButton("Save Thumbnail…")
        self.thumb_btn.setObjectName("actionBtn"); self.thumb_btn.clicked.connect(self._do_thumbnail)
        thr.addWidget(self.thumb_btn); thlay.addLayout(thr); lay.addWidget(thc)

        # Image sequence → video
        isc, islay = self._card("IMAGE SEQUENCE → VIDEO")
        isr1 = QtWidgets.QHBoxLayout()
        self.imgseq_folder = QtWidgets.QLineEdit(); self.imgseq_folder.setPlaceholderText("Input folder…")
        isr1.addWidget(self.imgseq_folder, 1)
        imgseq_pick = QtWidgets.QPushButton("Browse…"); imgseq_pick.setObjectName("openBtn")
        imgseq_pick.clicked.connect(self._pick_imgseq_folder); isr1.addWidget(imgseq_pick)
        islay.addLayout(isr1)
        isr2 = QtWidgets.QHBoxLayout()
        isr2.addWidget(QtWidgets.QLabel("Pattern:"))
        self.imgseq_pat = QtWidgets.QLineEdit("*.jpg"); self.imgseq_pat.setFixedWidth(100)
        isr2.addWidget(self.imgseq_pat)
        isr2.addSpacing(8); isr2.addWidget(QtWidgets.QLabel("FPS:"))
        self.imgseq_fps = QtWidgets.QDoubleSpinBox(); self.imgseq_fps.setRange(0.1, 120)
        self.imgseq_fps.setValue(24.0); self.imgseq_fps.setFixedWidth(80)
        isr2.addWidget(self.imgseq_fps)
        isr2.addSpacing(8); isr2.addWidget(QtWidgets.QLabel("Codec:"))
        self.imgseq_codec = QtWidgets.QComboBox()
        self.imgseq_codec.addItems(["libx264", "libx265", "libvpx-vp9"])
        isr2.addWidget(self.imgseq_codec)
        isr2.addStretch(1)
        self.imgseq_btn = QtWidgets.QPushButton("Create Video…")
        self.imgseq_btn.setObjectName("actionBtn"); self.imgseq_btn.clicked.connect(self._do_imgseq)
        isr2.addWidget(self.imgseq_btn); islay.addLayout(isr2); lay.addWidget(isc)

        lay.addStretch(1)
        scroll.setWidget(inner)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0); outer.addWidget(scroll)
        self._action_btns = [self.cap_btn, self.ext_btn, self.gif_btn,
                             self.thumb_btn]
        self._refresh_controls()

    def on_file_loaded(self):
        pd = self.ctrl.probe_data
        dur = pd.get("duration", 0)
        self.gif_start.setText("00:00:00.000")
        self.gif_end.setText(_secs_to_timestr(min(dur, 5.0)))
        self.thumb_time.setText(_secs_to_timestr(dur * 0.1))
        self._refresh_controls()

    def _refresh_controls(self):
        has = self.ctrl.current_file is not None
        for b in self._action_btns: b.setEnabled(has)

    def _pick_imgseq_folder(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Image Folder", str(Path.home()))
        if d: self.imgseq_folder.setText(d)

    def _do_capture(self):
        if not self.ctrl.current_file: return
        pos_s = self.ctrl.player.position() / 1000
        fmt   = self.cap_fmt.currentText()
        src   = Path(self.ctrl.current_file)
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Frame",
            str(src.parent / f"{src.stem}_frame.{fmt}"),
            f"{fmt.upper()} (*.{fmt})")
        if not out: return
        cmd = ["ffmpeg", "-y", "-ss", f"{pos_s:.3f}",
               "-i", self.ctrl.current_file,
               "-frames:v", "1", "-q:v", str(self.cap_q.value()), out]
        self.ctrl._run_ffmpeg(cmd, 0, "Capturing frame…")

    def _do_extract_frames(self):
        if not self.ctrl.current_file: return
        out_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Output Folder", str(Path(self.ctrl.current_file).parent))
        if not out_dir: return
        fmt = self.ext_fmt.currentText()
        src = Path(self.ctrl.current_file)
        out_pat = str(Path(out_dir) / f"{src.stem}_%05d.{fmt}")
        mode = self.ext_mode.currentText()
        n    = self.ext_n.value()
        if mode == "Every N seconds":
            vf = f"fps=1/{n:.4f}"
        elif mode == "Every Nth frame":
            vf = f"select='not(mod(n,{int(n)}))',setpts=N*AVTB"
        else:
            vf = None
        cmd = ["ffmpeg", "-y", "-i", self.ctrl.current_file]
        if vf:
            cmd.extend(["-vf", vf])
        cmd.extend(["-vsync", "0", "-q:v", "2", out_pat])
        self.ctrl._run_ffmpeg(cmd, 0, "Extracting frames…")

    def _do_gif(self):
        if not self.ctrl.current_file: return
        try:
            start_s = _timestr_to_secs(self.gif_start.text())
            end_s   = _timestr_to_secs(self.gif_end.text())
        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Invalid Time", str(e)); return
        if end_s <= start_s:
            QtWidgets.QMessageBox.warning(self, "Invalid Range", "End must be after start."); return
        src = Path(self.ctrl.current_file)
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save GIF", str(src.parent / f"{src.stem}.gif"), "GIF (*.gif)")
        if not out: return
        dur   = end_s - start_s
        fps   = self.gif_fps.value()
        w     = self.gif_w.value()
        dith  = self.gif_dither.currentText()
        loops = self.gif_loops.value()
        pal   = str(Path(tempfile.gettempdir()) / "fuetem_palette.png")
        vf    = f"fps={fps},scale={w}:-1:flags=lanczos"
        cmd1 = ["ffmpeg", "-y",
                "-ss", f"{start_s:.3f}", "-t", f"{dur:.3f}",
                "-i", self.ctrl.current_file,
                "-vf", f"{vf},palettegen=stats_mode=diff", pal]
        cmd2 = ["ffmpeg", "-y",
                "-ss", f"{start_s:.3f}", "-t", f"{dur:.3f}",
                "-i", self.ctrl.current_file, "-i", pal,
                "-loop", str(loops),
                "-filter_complex",
                f"{vf}[x];[x][1:v]paletteuse=dither={dith}", out]
        self.ctrl._run_multi([cmd1, cmd2], "Creating GIF…")

    def _do_thumbnail(self):
        if not self.ctrl.current_file: return
        try:
            t = _timestr_to_secs(self.thumb_time.text())
        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Invalid Time", str(e)); return
        fmt = self.thumb_fmt.currentText()
        src = Path(self.ctrl.current_file)
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Thumbnail",
            str(src.parent / f"{src.stem}_thumb.{fmt}"),
            f"{fmt.upper()} (*.{fmt})")
        if not out: return
        cmd = ["ffmpeg", "-y", "-ss", f"{t:.3f}",
               "-i", self.ctrl.current_file,
               "-frames:v", "1", "-q:v", "2", out]
        self.ctrl._run_ffmpeg(cmd, 0, "Saving thumbnail…")

    def _do_imgseq(self):
        folder = self.imgseq_folder.text().strip()
        if not folder or not Path(folder).is_dir():
            QtWidgets.QMessageBox.warning(self, "No Folder", "Select an image folder first."); return
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Video", str(Path(folder) / "output.mp4"),
            "MP4 (*.mp4);;MKV (*.mkv)")
        if not out: return
        pat = self.imgseq_pat.text().strip() or "*.jpg"
        fps = self.imgseq_fps.value()
        codec = self.imgseq_codec.currentText()
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-framerate", f"{fps:.3f}",
               "-pattern_type", "glob",
               "-i", str(Path(folder) / pat),
               "-c:v", codec, "-pix_fmt", "yuv420p", out]
        self.ctrl._run_ffmpeg(cmd, 0, "Building video from images…")


# ── Page: Merge ───────────────────────────────────────────────────────────────

class MergePage(QtWidgets.QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self._build_ui()

    def _build_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10); lay.setSpacing(10)

        card = QtWidgets.QFrame(); card.setObjectName("card")
        clay = QtWidgets.QVBoxLayout(card)
        clay.setContentsMargins(14, 10, 14, 10); clay.setSpacing(8)
        lbl = QtWidgets.QLabel("MERGE / CONCATENATE"); lbl.setObjectName("sectionLabel")
        clay.addWidget(lbl)

        self.file_list = DragFileList()
        clay.addWidget(self.file_list)

        btn_row = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton("Add Files…"); add_btn.setObjectName("openBtn")
        add_btn.clicked.connect(self._add_files); btn_row.addWidget(add_btn)
        rem_btn = QtWidgets.QPushButton("Remove"); rem_btn.setObjectName("smallBtn")
        rem_btn.clicked.connect(self._remove_selected); btn_row.addWidget(rem_btn)
        up_btn  = QtWidgets.QPushButton("▲"); up_btn.setObjectName("smallBtn")
        up_btn.clicked.connect(self._move_up); btn_row.addWidget(up_btn)
        dn_btn  = QtWidgets.QPushButton("▼"); dn_btn.setObjectName("smallBtn")
        dn_btn.clicked.connect(self._move_down); btn_row.addWidget(dn_btn)
        btn_row.addStretch(1)
        clay.addLayout(btn_row)

        sep = QtWidgets.QFrame(); sep.setObjectName("separator"); clay.addWidget(sep)

        opt_row = QtWidgets.QHBoxLayout()
        self.concat_copy = QtWidgets.QCheckBox("Stream copy (all files must share codec/resolution)")
        self.concat_copy.setChecked(True); opt_row.addWidget(self.concat_copy)
        opt_row.addSpacing(16)
        opt_row.addWidget(QtWidgets.QLabel("Output format:"))
        self.concat_fmt = QtWidgets.QComboBox(); self.concat_fmt.addItems(VIDEO_FORMATS)
        opt_row.addWidget(self.concat_fmt)
        opt_row.addStretch(1); clay.addLayout(opt_row)

        merge_row = QtWidgets.QHBoxLayout()
        merge_row.addStretch(1)
        self.merge_btn = QtWidgets.QPushButton("Merge…"); self.merge_btn.setObjectName("actionBtn")
        self.merge_btn.clicked.connect(self._do_merge); merge_row.addWidget(self.merge_btn)
        clay.addLayout(merge_row)

        lay.addWidget(card)
        lay.addStretch(1)

    def on_file_loaded(self): pass

    def _add_files(self):
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Add Video Files", str(Path.home()),
            "Video Files (*.mp4 *.mkv *.mov *.avi *.webm *.flv *.ts *.m4v);;All Files (*)")
        for p in paths: self.file_list.add_path(p)

    def _remove_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def _move_up(self):
        row = self.file_list.currentRow()
        if row > 0:
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row - 1, item)
            self.file_list.setCurrentRow(row - 1)

    def _move_down(self):
        row = self.file_list.currentRow()
        if row < self.file_list.count() - 1:
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row + 1, item)
            self.file_list.setCurrentRow(row + 1)

    def _do_merge(self):
        paths = self.file_list.paths()
        if len(paths) < 2:
            QtWidgets.QMessageBox.warning(self, "Need files",
                                          "Add at least two files to merge."); return
        fmt = self.concat_fmt.currentText()
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Merged File",
            str(Path(paths[0]).parent / f"merged.{fmt}"),
            f"{fmt.upper()} (*.{fmt})")
        if not out: return

        if self.concat_copy.isChecked():
            lst = Path(tempfile.gettempdir()) / "fuetem_concat.txt"
            lst.write_text("\n".join(f"file '{p}'" for p in paths))
            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                   "-i", str(lst), "-c", "copy", out]
            self.ctrl._run_ffmpeg(cmd, 0, "Merging (stream copy)…")
        else:
            n      = len(paths)
            inputs = []
            for p in paths:
                inputs.extend(["-i", p])
            fc = "".join(f"[{i}:v:0][{i}:a:0]" for i in range(n))
            fc += f"concat=n={n}:v=1:a=1[vout][aout]"
            cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats"] + inputs + [
                "-filter_complex", fc,
                "-map", "[vout]", "-map", "[aout]",
                "-c:v", "libx264", "-crf", "23", "-c:a", "aac", out]
            self.ctrl._run_ffmpeg(cmd, 0, "Merging (re-encode)…")


# ── Page: Subtitles ───────────────────────────────────────────────────────────

class SubtitlesPage(QtWidgets.QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self._build_ui()

    def _card(self, title=""):
        card = QtWidgets.QFrame(); card.setObjectName("card")
        lay = QtWidgets.QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10); lay.setSpacing(8)
        if title:
            lbl = QtWidgets.QLabel(title); lbl.setObjectName("sectionLabel"); lay.addWidget(lbl)
        return card, lay

    def _build_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10); lay.setSpacing(10)

        # Burn
        bc, blay = self._card("BURN SUBTITLES (HARD SUBS)")
        br = QtWidgets.QHBoxLayout()
        self.burn_path = QtWidgets.QLineEdit(); self.burn_path.setPlaceholderText("SRT / ASS file…")
        br.addWidget(self.burn_path, 1)
        bp = QtWidgets.QPushButton("Browse…"); bp.setObjectName("openBtn")
        bp.clicked.connect(lambda: self._pick_sub(self.burn_path)); br.addWidget(bp)
        blay.addLayout(br)
        br2 = QtWidgets.QHBoxLayout()
        br2.addWidget(QtWidgets.QLabel("Font size:"))
        self.burn_size = QtWidgets.QSpinBox(); self.burn_size.setRange(8, 96)
        self.burn_size.setValue(24); self.burn_size.setFixedWidth(70); br2.addWidget(self.burn_size)
        br2.addSpacing(8); br2.addWidget(QtWidgets.QLabel("Encoding:"))
        self.burn_enc = QtWidgets.QLineEdit("UTF-8"); self.burn_enc.setFixedWidth(80)
        br2.addWidget(self.burn_enc)
        br2.addStretch(1)
        self.burn_btn = QtWidgets.QPushButton("Burn Subtitles…")
        self.burn_btn.setObjectName("actionBtn"); self.burn_btn.clicked.connect(self._do_burn)
        br2.addWidget(self.burn_btn); blay.addLayout(br2); lay.addWidget(bc)

        # Soft subs
        sc, slay = self._card("ADD SOFT SUBTITLE TRACK")
        sr = QtWidgets.QHBoxLayout()
        self.soft_path = QtWidgets.QLineEdit(); self.soft_path.setPlaceholderText("SRT / ASS file…")
        sr.addWidget(self.soft_path, 1)
        sp = QtWidgets.QPushButton("Browse…"); sp.setObjectName("openBtn")
        sp.clicked.connect(lambda: self._pick_sub(self.soft_path)); sr.addWidget(sp)
        slay.addLayout(sr)
        sr2 = QtWidgets.QHBoxLayout()
        sr2.addWidget(QtWidgets.QLabel("Language:"))
        self.soft_lang = QtWidgets.QLineEdit("eng"); self.soft_lang.setFixedWidth(60)
        sr2.addWidget(self.soft_lang)
        sr2.addStretch(1)
        self.soft_btn = QtWidgets.QPushButton("Add Subtitle…")
        self.soft_btn.setObjectName("actionBtn"); self.soft_btn.clicked.connect(self._do_soft)
        sr2.addWidget(self.soft_btn); slay.addLayout(sr2); lay.addWidget(sc)

        # Extract
        xc, xlay = self._card("EXTRACT SUBTITLE")
        xr = QtWidgets.QHBoxLayout()
        xr.addWidget(QtWidgets.QLabel("Stream index:"))
        self.ext_idx = QtWidgets.QSpinBox(); self.ext_idx.setRange(0, 20)
        self.ext_idx.setFixedWidth(60); xr.addWidget(self.ext_idx)
        xr.addSpacing(8); xr.addWidget(QtWidgets.QLabel("Format:"))
        self.ext_sfmt = QtWidgets.QComboBox(); self.ext_sfmt.addItems(SUB_FMTS); xr.addWidget(self.ext_sfmt)
        xr.addStretch(1)
        self.ext_btn = QtWidgets.QPushButton("Extract…")
        self.ext_btn.setObjectName("actionBtn"); self.ext_btn.clicked.connect(self._do_extract)
        xr.addWidget(self.ext_btn); xlay.addLayout(xr); lay.addWidget(xc)

        # Remove
        rc, rlay = self._card("REMOVE ALL SUBTITLES")
        rr = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel("Strip every subtitle track from the container")
        lbl.setObjectName("fileInfoLabel"); rr.addWidget(lbl); rr.addStretch(1)
        self.rem_btn = QtWidgets.QPushButton("Remove Subs…")
        self.rem_btn.setObjectName("dangerBtn"); self.rem_btn.clicked.connect(self._do_remove)
        rr.addWidget(self.rem_btn); rlay.addLayout(rr); lay.addWidget(rc)

        lay.addStretch(1)
        self._action_btns = [self.burn_btn, self.soft_btn, self.ext_btn, self.rem_btn]
        self._refresh_controls()

    def on_file_loaded(self):
        pd = self.ctrl.probe_data
        n  = len(pd.get("subtitle_streams", []))
        self.ext_idx.setRange(0, max(0, n - 1))
        self._refresh_controls()

    def _refresh_controls(self):
        has = self.ctrl.current_file is not None
        for b in self._action_btns: b.setEnabled(has)

    def _pick_sub(self, target):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Subtitle File", str(Path.home()),
            "Subtitle Files (*.srt *.ass *.ssa *.vtt);;All Files (*)")
        if p: target.setText(p)

    def _save_as(self, hint):
        src = Path(self.ctrl.current_file)
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Output",
            str(src.parent / f"{src.stem}{hint}"),
            "All Files (*)")
        return out or None

    def _do_burn(self):
        if not self.ctrl.current_file: return
        sub = self.burn_path.text().strip()
        if not sub or not Path(sub).exists():
            QtWidgets.QMessageBox.warning(self, "No File", "Select a subtitle file."); return
        out = self._save_as("_burned.mp4")
        if not out: return
        enc  = self.burn_enc.text().strip() or "UTF-8"
        size = self.burn_size.value()
        sub_escaped = sub.replace(":", "\\:")
        vf = f"subtitles='{sub_escaped}':charenc={enc}:force_style='FontSize={size}'"
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file,
               "-vf", vf, "-c:a", "copy", out]
        self.ctrl._run_ffmpeg(cmd, self.ctrl.probe_data.get("duration", 0), "Burning subtitles…")

    def _do_soft(self):
        if not self.ctrl.current_file: return
        sub = self.soft_path.text().strip()
        if not sub or not Path(sub).exists():
            QtWidgets.QMessageBox.warning(self, "No File", "Select a subtitle file."); return
        src = Path(self.ctrl.current_file)
        # mkv supports most sub formats natively; mp4 needs mov_text
        ext  = src.suffix.lower()
        out  = self._save_as("_subbed" + ext)
        if not out: return
        lang = self.soft_lang.text().strip() or "eng"
        scodec = "mov_text" if ext in (".mp4", ".m4v") else "copy"
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file, "-i", sub,
               "-c", "copy", "-c:s", scodec,
               "-metadata:s:s:0", f"language={lang}", out]
        self.ctrl._run_ffmpeg(cmd, self.ctrl.probe_data.get("duration", 0), "Adding subtitle…")

    def _do_extract(self):
        if not self.ctrl.current_file: return
        idx  = self.ext_idx.value()
        fmt  = self.ext_sfmt.currentText()
        src  = Path(self.ctrl.current_file)
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Subtitle",
            str(src.parent / f"{src.stem}_sub{idx}.{fmt}"),
            f"{fmt.upper()} (*.{fmt})")
        if not out: return
        cmd = ["ffmpeg", "-y", "-i", self.ctrl.current_file,
               "-map", f"0:s:{idx}", out]
        self.ctrl._run_ffmpeg(cmd, 0, "Extracting subtitle…")

    def _do_remove(self):
        if not self.ctrl.current_file: return
        out = self._save_as("_nosubs.mp4")
        if not out: return
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file,
               "-map", "0:v", "-map", "0:a?",
               "-c", "copy", out]
        self.ctrl._run_ffmpeg(cmd, self.ctrl.probe_data.get("duration", 0), "Removing subtitles…")


# ── Page: Metadata ────────────────────────────────────────────────────────────

class MetadataPage(QtWidgets.QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self._build_ui()

    def _build_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10); lay.setSpacing(10)

        card = QtWidgets.QFrame(); card.setObjectName("card")
        clay = QtWidgets.QVBoxLayout(card)
        clay.setContentsMargins(14, 10, 14, 10); clay.setSpacing(8)
        lbl = QtWidgets.QLabel("METADATA / TAGS"); lbl.setObjectName("sectionLabel")
        clay.addWidget(lbl)

        grid = QtWidgets.QGridLayout(); grid.setSpacing(8)
        self._fields = {}
        entries = [
            ("title",   "Title",   0, 0), ("artist",  "Artist",  0, 2),
            ("album",   "Album",   1, 0), ("date",    "Date",    1, 2),
            ("comment", "Comment", 2, 0), ("description", "Description", 2, 2),
            ("encoder", "Encoder", 3, 0), ("copyright",   "Copyright",   3, 2),
        ]
        for key, label, row, col in entries:
            grid.addWidget(QtWidgets.QLabel(f"{label}:"), row, col)
            le = QtWidgets.QLineEdit(); le.setPlaceholderText(label)
            grid.addWidget(le, row, col + 1)
            self._fields[key] = le
        for c in (1, 3): grid.setColumnStretch(c, 1)
        clay.addLayout(grid)

        btn_row = QtWidgets.QHBoxLayout()
        self.strip_btn = QtWidgets.QPushButton("Strip All Metadata…")
        self.strip_btn.setObjectName("dangerBtn"); self.strip_btn.clicked.connect(self._do_strip)
        btn_row.addWidget(self.strip_btn)
        btn_row.addStretch(1)
        self.save_btn = QtWidgets.QPushButton("Save Tags…")
        self.save_btn.setObjectName("actionBtn"); self.save_btn.clicked.connect(self._do_save)
        btn_row.addWidget(self.save_btn)
        clay.addLayout(btn_row)

        lay.addWidget(card)
        lay.addStretch(1)
        self._refresh_controls()

    def on_file_loaded(self):
        pd   = self.ctrl.probe_data
        tags = pd.get("tags", {})
        # case-insensitive tag lookup
        tag_map = {k.lower(): v for k, v in tags.items()}
        for key, le in self._fields.items():
            le.setText(tag_map.get(key, ""))
        self._refresh_controls()

    def _refresh_controls(self):
        has = self.ctrl.current_file is not None
        self.save_btn.setEnabled(has); self.strip_btn.setEnabled(has)

    def _do_save(self):
        if not self.ctrl.current_file: return
        src = Path(self.ctrl.current_file)
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save With Tags",
            str(src.parent / f"{src.stem}_tagged{src.suffix}"),
            "All Files (*)")
        if not out: return
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file]
        for key, le in self._fields.items():
            val = le.text().strip()
            cmd.extend(["-metadata", f"{key}={val}"])
        cmd.extend(["-c", "copy", out])
        self.ctrl._run_ffmpeg(cmd, self.ctrl.probe_data.get("duration", 0), "Saving tags…")

    def _do_strip(self):
        if not self.ctrl.current_file: return
        src = Path(self.ctrl.current_file)
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Without Metadata",
            str(src.parent / f"{src.stem}_stripped{src.suffix}"),
            "All Files (*)")
        if not out: return
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file,
               "-map_metadata", "-1", "-c", "copy", out]
        self.ctrl._run_ffmpeg(cmd, self.ctrl.probe_data.get("duration", 0), "Stripping metadata…")


# ── Page: Analyse ─────────────────────────────────────────────────────────────

class AnalysePage(QtWidgets.QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self._build_ui()

    def _build_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10); lay.setSpacing(10)

        # ── Device info card (hidden until a file with device metadata is loaded) ──
        self.device_card = QtWidgets.QFrame()
        self.device_card.setObjectName("card")
        self.device_card.setStyleSheet(
            "QFrame#card { border: 1px solid rgba(244,114,182,0.3); }")
        dc_lay = QtWidgets.QVBoxLayout(self.device_card)
        dc_lay.setContentsMargins(14, 10, 14, 10); dc_lay.setSpacing(8)
        dc_hdr = QtWidgets.QHBoxLayout()
        dc_title = QtWidgets.QLabel("DEVICE / CAMERA DATA")
        dc_title.setObjectName("sectionLabel")
        dc_hdr.addWidget(dc_title)
        dc_hdr.addStretch(1)
        self.strip_tracks_btn = QtWidgets.QPushButton("Strip Device Tracks…")
        self.strip_tracks_btn.setObjectName("smallBtn")
        self.strip_tracks_btn.setToolTip(
            "Remove device data tracks (mebx/tmcd/GPS) — keeps video and audio only")
        self.strip_tracks_btn.clicked.connect(self._do_strip_tracks)
        dc_hdr.addWidget(self.strip_tracks_btn)
        dc_lay.addLayout(dc_hdr)

        self.device_info_label = QtWidgets.QLabel()
        self.device_info_label.setWordWrap(True)
        self.device_info_label.setObjectName("fileInfoLabel")
        dc_lay.addWidget(self.device_info_label)

        self.gps_row = QtWidgets.QHBoxLayout()
        self.gps_label = QtWidgets.QLabel()
        self.gps_label.setObjectName("fileInfoLabel")
        self.gps_row.addWidget(self.gps_label)
        self.copy_gps_btn = QtWidgets.QPushButton("Copy coords")
        self.copy_gps_btn.setObjectName("smallBtn")
        self.copy_gps_btn.clicked.connect(self._copy_gps)
        self.gps_row.addWidget(self.copy_gps_btn)
        self.gps_row.addStretch(1)
        dc_lay.addLayout(self.gps_row)

        self.device_card.hide()
        lay.addWidget(self.device_card)

        # ── Probe JSON card ──
        card = QtWidgets.QFrame(); card.setObjectName("card")
        clay = QtWidgets.QVBoxLayout(card)
        clay.setContentsMargins(14, 10, 14, 10); clay.setSpacing(8)
        lbl = QtWidgets.QLabel("ANALYSE"); lbl.setObjectName("sectionLabel")
        clay.addWidget(lbl)

        self.probe_text = QtWidgets.QTextEdit()
        self.probe_text.setReadOnly(True)
        self.probe_text.setMinimumHeight(220)
        self.probe_text.setPlaceholderText("Open a file to see full probe output…")
        clay.addWidget(self.probe_text)

        btn_row = QtWidgets.QHBoxLayout()
        self.error_btn = QtWidgets.QPushButton("Check for Errors")
        self.error_btn.setObjectName("smallBtn")
        self.error_btn.clicked.connect(self._do_check_errors)
        btn_row.addWidget(self.error_btn)
        copy_btn = QtWidgets.QPushButton("Copy JSON")
        copy_btn.setObjectName("smallBtn")
        copy_btn.clicked.connect(
            lambda: QtWidgets.QApplication.clipboard().setText(self.probe_text.toPlainText()))
        btn_row.addWidget(copy_btn)
        btn_row.addStretch(1)
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.setObjectName("smallBtn")
        self.refresh_btn.clicked.connect(self._refresh)
        btn_row.addWidget(self.refresh_btn)
        clay.addLayout(btn_row)

        lay.addWidget(card)
        lay.addStretch(1)
        self._refresh_controls()
        self._gps_coords = None

    def on_file_loaded(self):
        self._refresh()
        self._refresh_controls()

    def _refresh_controls(self):
        has = self.ctrl.current_file is not None
        self.error_btn.setEnabled(has)
        self.refresh_btn.setEnabled(has)

    def _refresh(self):
        if not self.ctrl.current_file: return
        pd  = self.ctrl.probe_data
        raw = pd.get("raw", {})
        self.probe_text.setPlainText(json.dumps(raw, indent=2, ensure_ascii=False))
        self._populate_device_card(pd)

    def _populate_device_card(self, pd: dict):
        dev = pd.get("device_info", {})
        data_streams = pd.get("data_streams", [])
        if not dev and not data_streams:
            self.device_card.hide()
            return

        lines = []
        if dev.get("make") or dev.get("model"):
            lines.append(f"Device: {dev.get('make', '')} {dev.get('model', '')}".strip())
        if dev.get("software"):
            lines.append(f"Software: {dev.get('software', '')}")
        if dev.get("creation_date"):
            lines.append(f"Recorded: {dev.get('creation_date', '')}")
        if data_streams:
            tags = [s.get("codec_tag_string", "data") for s in data_streams]
            lines.append(f"Data tracks: {', '.join(t for t in tags if t)} "
                         f"({len(data_streams)} stream{'s' if len(data_streams) != 1 else ''})")
        self.device_info_label.setText("\n".join(lines))

        # GPS
        self._gps_coords = None
        loc = dev.get("location", "")
        if loc:
            coords = _parse_iso6709(loc)
            if coords:
                lat, lon = coords
                acc = dev.get("location_accuracy", "")
                acc_str = f"  ±{float(acc):.0f} m" if acc else ""
                self.gps_label.setText(
                    f"GPS: {lat:+.6f}, {lon:+.6f}{acc_str}")
                self._gps_coords = f"{lat:+.6f}, {lon:+.6f}"
                self.gps_label.show()
                self.copy_gps_btn.show()
            else:
                self.gps_label.hide()
                self.copy_gps_btn.hide()
        else:
            self.gps_label.hide()
            self.copy_gps_btn.hide()

        self.device_card.show()

    def _copy_gps(self):
        if self._gps_coords:
            QtWidgets.QApplication.clipboard().setText(self._gps_coords)
            self.ctrl._set_status("GPS coordinates copied.")

    def _do_strip_tracks(self):
        if not self.ctrl.current_file: return
        src = Path(self.ctrl.current_file)
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Clean Copy",
            str(src.parent / f"{src.stem}_clean{src.suffix}"),
            "All Files (*)")
        if not out: return
        # -map 0:v -map 0:a keeps only video and audio, dropping all data/timecode tracks
        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file,
               "-map", "0:v", "-map", "0:a?",
               "-c", "copy", out]
        self.ctrl._run_ffmpeg(
            cmd, self.ctrl.probe_data.get("duration", 0),
            "Stripping device tracks…")

    def _do_check_errors(self):
        if not self.ctrl.current_file: return
        self.ctrl._set_status("Checking for errors…")
        self.ctrl._set_busy(True)

        class _Runner(QtCore.QThread):
            done = QtCore.pyqtSignal(str)
            def __init__(self, path):
                super().__init__(); self.path = path
            def run(self):
                r = subprocess.run(
                    ["ffmpeg", "-v", "error", "-i", self.path, "-f", "null", "-"],
                    capture_output=True, text=True)
                errors = r.stderr.strip()
                self.done.emit(errors if errors else "No errors detected.")

        self._err_runner = _Runner(self.ctrl.current_file)
        self._err_runner.done.connect(self._on_check_done)
        self._err_runner.start()

    def _on_check_done(self, msg: str):
        self.ctrl._set_busy(False)
        self.ctrl._set_status("Error check complete.")
        QtWidgets.QMessageBox.information(self, "Error Check", msg)


# ── Page: Privacy ─────────────────────────────────────────────────────────────

_NEVER_REMOVE = frozenset({
    "rotate", "rotation", "stereo_mode",
})

_PRIVACY_KEYS = frozenset({
    # GPS / location
    "com.apple.quicktime.location.iso6709",
    "com.apple.quicktime.location.accuracy.horizontal",
    "location", "location-eng", "gps_coordinates", "gps",
    # device identity
    "com.apple.quicktime.make", "com.apple.quicktime.model",
    "com.apple.quicktime.software", "com.apple.quicktime.description",
    "com.android.manufacturer", "com.android.model", "com.android.version",
    "make", "model", "software",
    # timestamps
    "com.apple.quicktime.creationdate", "creation_time", "date",
    # encoder / tool info
    "encoder", "encoded_by", "encoding_tool",
    # ownership / legal
    "copyright", "com.apple.quicktime.copyright",
    "artist", "album_artist", "description",
})


class PrivacyPage(QtWidgets.QWidget):
    _COL_CHECK = 0
    _COL_SRC   = 1
    _COL_KEY   = 2
    _COL_VAL   = 3

    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self._rows: list = []   # list of dicts: {source, key, value, stream_in, stream_type}
        self._build_ui()

    def _build_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        # data tracks card (only visible when data streams present)
        self._data_card = QtWidgets.QFrame()
        self._data_card.setObjectName("privacyDataCard")
        self._data_card.setStyleSheet(
            "#privacyDataCard { background: #1a1040; border: 1px solid #f472b6; "
            "border-radius: 8px; }")
        dc_lay = QtWidgets.QVBoxLayout(self._data_card)
        dc_lay.setContentsMargins(14, 10, 14, 10)
        dc_lay.setSpacing(6)

        hdr = QtWidgets.QLabel("DEVICE DATA TRACKS")
        hdr.setObjectName("sectionLabel")
        hdr.setStyleSheet("color: #f472b6;")
        dc_lay.addWidget(hdr)

        self._data_tracks_cb = QtWidgets.QCheckBox("Remove device data tracks (mebx, tmcd, …)")
        self._data_tracks_cb.setStyleSheet("color: #e0e0ff;")
        dc_lay.addWidget(self._data_tracks_cb)

        self._data_tracks_desc = QtWidgets.QLabel()
        self._data_tracks_desc.setStyleSheet("color: #9494c0;")
        self._data_tracks_desc.setWordWrap(True)
        dc_lay.addWidget(self._data_tracks_desc)

        lay.addWidget(self._data_card)
        self._data_card.setVisible(False)

        # tags card
        tags_card = QtWidgets.QFrame()
        tags_card.setObjectName("card")
        tc_lay = QtWidgets.QVBoxLayout(tags_card)
        tc_lay.setContentsMargins(14, 10, 14, 10)
        tc_lay.setSpacing(8)

        hdr2 = QtWidgets.QLabel("METADATA FIELDS")
        hdr2.setObjectName("sectionLabel")
        tc_lay.addWidget(hdr2)

        sel_row = QtWidgets.QHBoxLayout()
        sel_row.setSpacing(8)
        for label, slot in [
            ("Select Privacy-Sensitive", self._select_privacy),
            ("Select All",              self._select_all),
            ("Deselect All",            self._deselect_all),
        ]:
            btn = QtWidgets.QPushButton(label)
            btn.setObjectName("actionBtn")
            btn.clicked.connect(slot)
            sel_row.addWidget(btn)
        sel_row.addStretch(1)
        tc_lay.addLayout(sel_row)

        self._table = QtWidgets.QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["", "Source", "Key", "Value"])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(
            "QTableWidget { background: #0f0f23; gridline-color: #2d2d5e; "
            "alternate-background-color: #16213e; color: #e0e0ff; border: none; }"
            "QHeaderView::section { background: #16213e; color: #818cf8; "
            "border: 1px solid #2d2d5e; padding: 4px; }")
        self._table.setMinimumHeight(300)
        tc_lay.addWidget(self._table)

        strip_row = QtWidgets.QHBoxLayout()
        strip_row.addStretch(1)
        self.strip_btn = QtWidgets.QPushButton("Strip Selected…")
        self.strip_btn.setObjectName("actionBtn")
        self.strip_btn.clicked.connect(self._do_strip)
        strip_row.addWidget(self.strip_btn)
        tc_lay.addLayout(strip_row)

        lay.addWidget(tags_card, 1)
        self._refresh_controls()

    def on_file_loaded(self):
        pd = self.ctrl.probe_data
        self._rows = []
        self._table.setRowCount(0)

        # format-level tags
        for k, v in pd.get("tags", {}).items():
            if k.lower() in _NEVER_REMOVE:
                continue
            self._add_row("Format", k, str(v), stream_in=None)

        # stream-level tags (video, audio, subtitle — not data)
        type_order = (
            [(s, "video")    for s in pd.get("video_streams", [])] +
            [(s, "audio")    for s in pd.get("audio_streams", [])] +
            [(s, "subtitle") for s in pd.get("subtitle_streams", [])]
        )
        for s, stype in type_order:
            idx = s.get("index", "?")
            label = f"Stream {idx} ({stype})"
            for k, v in s.get("tags", {}).items():
                if k.lower() in _NEVER_REMOVE:
                    continue
                self._add_row(label, k, str(v), stream_in=idx)

        # data tracks card
        data_streams = pd.get("data_streams", [])
        if data_streams:
            tags = [s.get("codec_tag_string", "data") for s in data_streams]
            self._data_tracks_desc.setText(
                f"{len(data_streams)} track(s): {', '.join(t for t in tags if t)}")
            self._data_tracks_cb.setChecked(True)
            self._data_card.setVisible(True)
        else:
            self._data_card.setVisible(False)

        self._refresh_controls()

    def _add_row(self, source: str, key: str, value: str, stream_in):
        row = self._table.rowCount()
        self._table.insertRow(row)

        is_priv = key.lower() in _PRIVACY_KEYS

        cb = QtWidgets.QTableWidgetItem()
        cb.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        cb.setCheckState(QtCore.Qt.Checked if is_priv else QtCore.Qt.Unchecked)
        self._table.setItem(row, self._COL_CHECK, cb)

        src_item = QtWidgets.QTableWidgetItem(source)
        src_item.setForeground(QtGui.QColor("#818cf8"))
        self._table.setItem(row, self._COL_SRC, src_item)

        key_item = QtWidgets.QTableWidgetItem(key)
        if is_priv:
            key_item.setForeground(QtGui.QColor("#f472b6"))
        self._table.setItem(row, self._COL_KEY, key_item)

        self._table.setItem(row, self._COL_VAL, QtWidgets.QTableWidgetItem(value))

        self._rows.append({
            "source":    source,
            "key":       key,
            "value":     value,
            "stream_in": stream_in,
        })

    def _select_privacy(self):
        for r in range(self._table.rowCount()):
            key = self._table.item(r, self._COL_KEY).text().lower()
            state = QtCore.Qt.Checked if key in _PRIVACY_KEYS else QtCore.Qt.Unchecked
            self._table.item(r, self._COL_CHECK).setCheckState(state)

    def _select_all(self):
        for r in range(self._table.rowCount()):
            self._table.item(r, self._COL_CHECK).setCheckState(QtCore.Qt.Checked)

    def _deselect_all(self):
        for r in range(self._table.rowCount()):
            self._table.item(r, self._COL_CHECK).setCheckState(QtCore.Qt.Unchecked)

    def _refresh_controls(self):
        self.strip_btn.setEnabled(self.ctrl.current_file is not None)

    def _do_strip(self):
        if not self.ctrl.current_file:
            return

        pd = self.ctrl.probe_data
        fmt_tags = pd.get("tags", {})
        remove_data = self._data_tracks_cb.isChecked() and self._data_card.isVisible()

        checked_rows = {r for r in range(self._table.rowCount())
                        if self._table.item(r, self._COL_CHECK).checkState()
                        == QtCore.Qt.Checked}

        if not checked_rows and not remove_data:
            QtWidgets.QMessageBox.information(
                self, "Nothing Selected", "No fields are checked.")
            return

        src = Path(self.ctrl.current_file)
        out, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Stripped File",
            str(src.parent / f"{src.stem}_private{src.suffix}"),
            "All Files (*)")
        if not out:
            return

        cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats",
               "-i", self.ctrl.current_file]

        # stream mapping
        if remove_data:
            for s in (pd.get("video_streams", []) +
                      pd.get("audio_streams", []) +
                      pd.get("subtitle_streams", [])):
                cmd += ["-map", f"0:{s['index']}"]
        else:
            cmd += ["-map", "0"]

        # format-level: clear all, re-add unchecked
        checked_fmt_keys = {self._rows[r]["key"]
                            for r in checked_rows
                            if self._rows[r]["stream_in"] is None}
        cmd += ["-map_metadata", "-1"]
        for k, v in fmt_tags.items():
            if k.lower() not in _NEVER_REMOVE and k not in checked_fmt_keys:
                cmd += ["-metadata", f"{k}={v}"]

        # per-stream: only touch streams that have checked tags
        kept_streams = (pd.get("video_streams", []) +
                        pd.get("audio_streams", []) +
                        pd.get("subtitle_streams", []))
        if not remove_data:
            kept_streams += pd.get("data_streams", [])

        for out_i, s in enumerate(kept_streams):
            in_idx = s.get("index")
            stream_tags = s.get("tags", {})
            if not stream_tags:
                continue
            checked_stream_keys = {self._rows[r]["key"]
                                   for r in checked_rows
                                   if self._rows[r]["stream_in"] == in_idx}
            if not checked_stream_keys:
                continue
            cmd += [f"-map_metadata:s:{out_i}", "-1"]
            for k, v in stream_tags.items():
                if k.lower() not in _NEVER_REMOVE and k not in checked_stream_keys:
                    cmd += [f"-metadata:s:{out_i}", f"{k}={v}"]

        cmd += ["-c", "copy", out]
        self.ctrl._run_ffmpeg(cmd, pd.get("duration", 0), "Stripping selected fields…")


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("Fuetem Video")
        self.setMinimumSize(1280, 760)
        self.resize(1400, 860)

        self.current_file: str | None = None
        self.probe_data: dict = {}
        self._ffmpeg_worker: FFmpegWorker | None = None
        self._multi_worker: MultiCmdWorker | None = None

        self._build_ui()
        self._apply_shortcuts()
        self._refresh_controls()
        self.setAcceptDrops(True)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── top splitter (left=player, right=tabs) ────────────────────────────
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("QSplitter::handle { background: #2d2d5e; }")
        root.addWidget(splitter, 1)

        # LEFT PANE
        left = QtWidgets.QWidget()
        left.setObjectName("MainWindow")
        left_lay = QtWidgets.QVBoxLayout(left)
        left_lay.setContentsMargins(8, 8, 4, 8)
        left_lay.setSpacing(6)

        # brand
        brand = QtWidgets.QLabel("▶ Fuetem Video")
        brand.setObjectName("brandLarge")
        brand.setStyleSheet("QLabel { color: #f472b6; font-size: 22px; font-weight: 700; "
                            "letter-spacing: 2px; padding: 6px 0; }")
        left_lay.addWidget(brand)

        # video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(240)
        self.video_widget.setStyleSheet("background: #000;")
        left_lay.addWidget(self.video_widget, 3)

        # thumbnail timeline
        self.timeline = ThumbnailTimeline()
        self.timeline.seek_requested.connect(self._on_timeline_seek)
        left_lay.addWidget(self.timeline)

        # time label
        self.time_label = QtWidgets.QLabel("00:00:00.000 / 00:00:00.000")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setAlignment(QtCore.Qt.AlignCenter)
        left_lay.addWidget(self.time_label)

        # transport row
        transport = QtWidgets.QHBoxLayout()
        transport.setSpacing(4)

        def _tbtn(symbol, tip, slot):
            b = QtWidgets.QToolButton()
            b.setText(symbol)
            b.setToolTip(tip)
            b.setFixedSize(34, 34)
            b.setStyleSheet(
                "QToolButton { background: #1e1e4e; border: 1px solid #2d2d5e; "
                "border-radius: 6px; color: #e0e0ff; font-size: 16px; }"
                "QToolButton:hover { border-color: #818cf8; }"
                "QToolButton:pressed { background: #2d2d5e; }")
            b.clicked.connect(slot)
            return b

        self.btn_jump_start = _tbtn("⏮", "Jump to start", self._jump_start)
        self.btn_step_back  = _tbtn("◀", "Step back 5 s", self._step_back)
        self.btn_play_pause = _tbtn("▶", "Play / Pause (Space)", self._play_pause)
        self.btn_stop       = _tbtn("■", "Stop", self._stop)
        self.btn_step_fwd   = _tbtn("▶▶", "Step fwd 5 s", self._step_fwd)
        self.btn_jump_end   = _tbtn("⏭", "Jump to end", self._jump_end)

        for b in (self.btn_jump_start, self.btn_step_back, self.btn_play_pause,
                  self.btn_stop, self.btn_step_fwd, self.btn_jump_end):
            transport.addWidget(b)

        transport.addSpacing(8)
        self.loop_btn = QtWidgets.QToolButton()
        self.loop_btn.setText("⟳")
        self.loop_btn.setToolTip("Loop playback")
        self.loop_btn.setCheckable(True)
        self.loop_btn.setFixedSize(34, 34)
        self.loop_btn.setStyleSheet(
            "QToolButton { background: #1e1e4e; border: 1px solid #2d2d5e; "
            "border-radius: 6px; color: #e0e0ff; font-size: 16px; }"
            "QToolButton:checked { background: #3730a3; border-color: #818cf8; }"
            "QToolButton:hover { border-color: #818cf8; }")
        transport.addWidget(self.loop_btn)

        transport.addSpacing(8)
        transport.addWidget(QtWidgets.QLabel("Vol"))
        self.vol_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80)
        self.vol_slider.setFixedWidth(80)
        self.vol_slider.setStyleSheet(
            "QSlider::groove:horizontal { height:4px; background:#2d2d5e; border-radius:2px; }"
            "QSlider::handle:horizontal { width:12px; height:12px; margin:-4px 0; "
            "background:#818cf8; border-radius:6px; }"
            "QSlider::sub-page:horizontal { background:#818cf8; border-radius:2px; }")
        self.vol_slider.valueChanged.connect(self._on_volume_changed)
        transport.addWidget(self.vol_slider)

        transport.addSpacing(8)
        transport.addWidget(QtWidgets.QLabel("Speed"))
        self.speed_combo = QtWidgets.QComboBox()
        self.speed_combo.addItems(["0.25×", "0.5×", "0.75×", "1×", "1.25×", "1.5×", "2×", "4×"])
        self.speed_combo.setCurrentIndex(3)
        self.speed_combo.setFixedWidth(70)
        self.speed_combo.currentIndexChanged.connect(self._on_speed_changed)
        transport.addWidget(self.speed_combo)

        transport.addStretch(1)
        left_lay.addLayout(transport)

        # seek slider
        self.seek_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.setStyleSheet(
            "QSlider::groove:horizontal { height:6px; background:#2d2d5e; border-radius:3px; }"
            "QSlider::handle:horizontal { width:14px; height:14px; margin:-4px 0; "
            "background:#f472b6; border-radius:7px; }"
            "QSlider::sub-page:horizontal { background:#f472b6; border-radius:3px; }")
        self.seek_slider.sliderMoved.connect(self._on_seek_moved)
        self.seek_slider.sliderPressed.connect(self._on_seek_pressed)
        self.seek_slider.sliderReleased.connect(self._on_seek_released)
        self._seeking = False
        left_lay.addWidget(self.seek_slider)

        splitter.addWidget(left)

        # RIGHT PANE
        right = QtWidgets.QWidget()
        right.setObjectName("MainWindow")
        right_lay = QtWidgets.QVBoxLayout(right)
        right_lay.setContentsMargins(4, 8, 8, 8)
        right_lay.setSpacing(8)

        # file card
        file_card = QtWidgets.QFrame()
        file_card.setFrameShape(QtWidgets.QFrame.StyledPanel)
        file_card.setStyleSheet(
            "QFrame { background: #16213e; border: 1px solid #2d2d5e; border-radius: 8px; "
            "padding: 8px; }")
        fc_lay = QtWidgets.QVBoxLayout(file_card)
        fc_lay.setSpacing(4)

        btn_row = QtWidgets.QHBoxLayout()
        open_btn = QtWidgets.QPushButton("Open…")
        open_btn.setObjectName("actionBtn")
        open_btn.clicked.connect(self._open_file)
        btn_row.addWidget(open_btn)

        recent_btn = QtWidgets.QPushButton("Recent ▾")
        recent_btn.clicked.connect(self._show_recent_menu)
        btn_row.addWidget(recent_btn)
        btn_row.addStretch(1)
        fc_lay.addLayout(btn_row)

        self.file_name_label = QtWidgets.QLabel("No file loaded")
        self.file_name_label.setObjectName("sectionLabel")
        self.file_name_label.setWordWrap(True)
        fc_lay.addWidget(self.file_name_label)

        self.file_info_label = QtWidgets.QLabel("")
        self.file_info_label.setObjectName("fileInfoLabel")
        self.file_info_label.setWordWrap(True)
        fc_lay.addWidget(self.file_info_label)

        right_lay.addWidget(file_card)

        # tab widget
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet(
            "QTabBar::tab { background: #16213e; color: #9494c0; border: 1px solid #2d2d5e; "
            "border-bottom: none; padding: 6px 14px; border-radius: 6px 6px 0 0; }"
            "QTabBar::tab:selected { background: #1e1e4e; color: #f472b6; "
            "border-color: #818cf8; }"
            "QTabBar::tab:hover:!selected { color: #e0e0ff; }"
            "QTabWidget::pane { border: 1px solid #2d2d5e; background: #1e1e4e; }")

        self._pages = {}
        for name, cls in [
            ("Trim / Split", TrimSplitPage),
            ("Convert",      ConvertPage),
            ("Filters",      FiltersPage),
            ("Audio",        AudioPage),
            ("Frames",       FramesPage),
            ("Merge",        MergePage),
            ("Subtitles",    SubtitlesPage),
            ("Metadata",     MetadataPage),
            ("Analyse",      AnalysePage),
            ("Privacy",      PrivacyPage),
        ]:
            page = cls(self)
            self._pages[name] = page
            scroll = QtWidgets.QScrollArea()
            scroll.setWidget(page)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
            scroll.setStyleSheet("QScrollArea { background: transparent; }")
            self.tabs.addTab(scroll, name)

        right_lay.addWidget(self.tabs, 1)
        splitter.addWidget(right)

        splitter.setSizes([620, 780])

        # ── status bar ────────────────────────────────────────────────────────
        status_bar = QtWidgets.QWidget()
        status_bar.setFixedHeight(42)
        status_bar.setStyleSheet(
            "QWidget { background: #0d0d24; border-top: 1px solid #2d2d5e; }")
        sb_lay = QtWidgets.QHBoxLayout(status_bar)
        sb_lay.setContentsMargins(12, 4, 12, 4)
        sb_lay.setSpacing(10)

        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        sb_lay.addWidget(self.status_label, 1)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background: #16213e; border: 1px solid #2d2d5e; "
            "border-radius: 4px; height: 12px; }"
            "QProgressBar::chunk { background: #818cf8; border-radius: 4px; }")
        self.progress_bar.setVisible(False)
        sb_lay.addWidget(self.progress_bar)

        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_ffmpeg)
        sb_lay.addWidget(self.cancel_btn)

        root.addWidget(status_bar)

        # ── media player ──────────────────────────────────────────────────────
        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.player.setVideoOutput(self.video_widget)
        self.player.setVolume(80)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.stateChanged.connect(self._on_state_changed)
        self.player.error.connect(self._on_player_error)

    # ── Keyboard shortcuts ────────────────────────────────────────────────────

    def _apply_shortcuts(self):
        QtWidgets.QShortcut(QtGui.QKeySequence("Space"),      self, self._play_pause)
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Left),  self, self._step_back)
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Right), self, self._step_fwd)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"),     self, self._open_file)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"),     self, self._close_file)

    # ── Transport controls ────────────────────────────────────────────────────

    def _play_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _stop(self):
        self.player.stop()

    def _jump_start(self):
        self.player.setPosition(0)

    def _jump_end(self):
        dur = self.player.duration()
        if dur > 0:
            self.player.setPosition(dur - 1)

    def _step_back(self):
        pos = max(0, self.player.position() - 5000)
        self.player.setPosition(pos)

    def _step_fwd(self):
        dur = self.player.duration()
        pos = min(dur - 1 if dur > 0 else 0, self.player.position() + 5000)
        self.player.setPosition(pos)

    def _on_volume_changed(self, val: int):
        self.player.setVolume(val)

    def _on_speed_changed(self, idx: int):
        rate = SPEED_VALUES[idx] if idx < len(SPEED_VALUES) else 1.0
        self.player.setPlaybackRate(rate)

    def _on_seek_pressed(self):
        self._seeking = True

    def _on_seek_moved(self, val: int):
        dur = self.player.duration()
        if dur > 0:
            self.player.setPosition(int(val / 1000 * dur))

    def _on_seek_released(self):
        self._seeking = False

    def _on_timeline_seek(self, frac: float):
        dur = self.player.duration()
        if dur > 0:
            self.player.setPosition(int(frac * dur))

    # ── Player signal handlers ────────────────────────────────────────────────

    def _on_position_changed(self, pos_ms: int):
        dur = self.player.duration()
        pos_s  = pos_ms  / 1000.0
        dur_s  = dur     / 1000.0
        self.time_label.setText(
            f"{_ms_to_hms(pos_ms)} / {_ms_to_hms(dur)}")
        if not self._seeking and dur > 0:
            self.seek_slider.setValue(int(pos_ms / dur * 1000))
        if dur > 0:
            self.timeline.set_position(pos_ms / dur)
        if (self.loop_btn.isChecked()
                and self.player.state() != QMediaPlayer.StoppedState
                and dur > 0 and pos_ms >= dur - 100):
            self.player.setPosition(0)

    def _on_duration_changed(self, dur_ms: int):
        self.time_label.setText(f"{_ms_to_hms(0)} / {_ms_to_hms(dur_ms)}")

    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.btn_play_pause.setText("⏸")
        else:
            self.btn_play_pause.setText("▶")

    def _on_player_error(self, error):
        if error == QMediaPlayer.NoError:
            return
        msg = self.player.errorString()
        if "unknown" in msg.lower() and self.probe_data.get("data_streams"):
            tags = [s.get("codec_tag_string", "data")
                    for s in self.probe_data["data_streams"]]
            self._set_status(
                f"Device data tracks present ({', '.join(t for t in tags if t)}) "
                f"— see Analyse tab to strip them")
        else:
            self._set_status(f"Player error: {msg}")

    # ── File loading ──────────────────────────────────────────────────────────

    def _open_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Video File", "",
            "Video files (" + " ".join(f"*{e}" for e in sorted(VIDEO_EXTS)) + ");;All files (*)")
        if path:
            self._load_file(path)

    def _show_recent_menu(self):
        recent = _load_recent()
        if not recent:
            QtWidgets.QMessageBox.information(self, "Recent Files", "No recent files.")
            return
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet(
            "QMenu { background:#16213e; color:#e0e0ff; border:1px solid #2d2d5e; }"
            "QMenu::item:selected { background:#3730a3; }")
        for p in recent:
            act = menu.addAction(Path(p).name)
            act.setData(p)
            act.setToolTip(p)
        action = menu.exec_(QtGui.QCursor.pos())
        if action:
            self._load_file(action.data())

    def _close_file(self):
        self.player.stop()
        self.current_file = None
        self.probe_data = {}
        self.file_name_label.setText("No file loaded")
        self.file_info_label.setText("")
        self.time_label.setText("00:00:00.000 / 00:00:00.000")
        self.seek_slider.setValue(0)
        self.timeline.clear()
        self._refresh_controls()

    def _load_file(self, path: str):
        if not Path(path).exists():
            QtWidgets.QMessageBox.warning(self, "File not found", f"Not found:\n{path}")
            return
        self.current_file = path
        self.probe_data = _probe(path)
        _add_to_recent(path)

        self.file_name_label.setText(Path(path).name)
        pd = self.probe_data
        parts = []
        if pd.get("width") and pd.get("height"):
            parts.append(f"{pd['width']}×{pd['height']}")
        if pd.get("vcodec"):
            parts.append(pd["vcodec"])
        if pd.get("fps"):
            parts.append(f"{pd['fps']} fps")
        dur = pd.get("duration", 0)
        if dur:
            parts.append(_secs_to_timestr(dur))
        sz = pd.get("size", 0)
        if sz:
            parts.append(f"{sz/1_048_576:.1f} MB")
        self.file_info_label.setText("  ·  ".join(parts))

        url = QtCore.QUrl.fromLocalFile(path)
        self.player.setMedia(QMediaContent(url))
        self.player.pause()

        self.timeline.load_file(path, self.probe_data.get("duration", 0))
        self._refresh_controls()
        self._set_status(f"Loaded: {Path(path).name}")

    # ── Control enable/disable ────────────────────────────────────────────────

    def _refresh_controls(self):
        for page in self._pages.values():
            if hasattr(page, "on_file_loaded") and self.current_file:
                page.on_file_loaded()
            elif hasattr(page, "_refresh_controls"):
                page._refresh_controls()

    # ── FFmpeg runner interface (called by pages) ─────────────────────────────

    def _run_ffmpeg(self, cmd: list, dur: float = 0.0, status: str = "Processing…"):
        self._set_status(status)
        self._set_busy(True)
        self._ffmpeg_worker = FFmpegWorker(cmd, dur)
        self._ffmpeg_worker.progress.connect(self.progress_bar.setValue)
        self._ffmpeg_worker.finished.connect(self._on_ffmpeg_done)
        self._ffmpeg_worker.start()

    def _run_multi(self, cmds: list, status: str = "Processing…"):
        self._set_status(status)
        self._set_busy(True)
        self._multi_worker = MultiCmdWorker(cmds)
        self._multi_worker.step_done.connect(
            lambda cur, tot: (
                self._set_status(f"{status} ({cur}/{tot})"),
                self.progress_bar.setValue(int(cur / tot * 100))))
        self._multi_worker.finished.connect(self._on_ffmpeg_done)
        self._multi_worker.start()

    def _on_ffmpeg_done(self, ok: bool, msg: str):
        self._set_busy(False)
        if ok:
            self._set_status(f"Done. {msg}")
        else:
            self._set_status(f"Error: {msg}")
            QtWidgets.QMessageBox.warning(self, "FFmpeg Error", msg)

    def _cancel_ffmpeg(self):
        if self._ffmpeg_worker and self._ffmpeg_worker.isRunning():
            self._ffmpeg_worker.cancel()
        if self._multi_worker and self._multi_worker.isRunning():
            self._multi_worker.cancel()
        self._set_busy(False)
        self._set_status("Cancelled.")

    def _set_status(self, msg: str):
        self.status_label.setText(msg)

    def _set_busy(self, busy: bool):
        self.progress_bar.setVisible(busy)
        self.cancel_btn.setVisible(busy)
        if not busy:
            self.progress_bar.setValue(0)

    # ── Drag and drop ─────────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(Path(u.toLocalFile()).suffix.lower() in VIDEO_EXTS for u in urls):
                event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if Path(path).suffix.lower() in VIDEO_EXTS:
                self._load_file(path)
                break


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Fuetem Video")
    font = app.font()
    font.setPixelSize(15)
    app.setFont(font)
    app.setStyleSheet(NEON_STYLESHEET)
    win = MainWindow()
    win.setStyleSheet(NEON_STYLESHEET)
    win.show()
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if Path(path).exists() and Path(path).suffix.lower() in VIDEO_EXTS:
            win._load_file(path)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
