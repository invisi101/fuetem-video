# Fuetem Video

A kitchen-sink single-file video tool built with PyQt5 and ffmpeg. Open a video, do what you need, export. No project files, no timeline overhead.

Supports MP4, MKV, MOV, AVI, WebM, FLV, TS, M4V, MTS, M2TS, MPEG, OGV, 3GP, GIF, VOB, and more.

---

## Installation

### Requirements

- Python 3.10 or newer
- ffmpeg
- PyQt5 with Qt5 Multimedia and Multimedia Widgets
- GStreamer with libav backend (for video playback)

### One-command install

Clone the repo and run the install script:

```bash
git clone https://github.com/invisi101/fuetem-video.git
cd fuetem-video
bash install.sh
```

The script checks for all dependencies, installs any that are missing using your system package manager, copies the app to `~/.local/bin/fuetem-video`, installs the icon, and creates a `.desktop` entry so the app appears in your application launcher.

### Dependency handling

The installer detects your package manager and maps dependencies to the correct package names automatically:

| Dependency | Arch | Debian / Ubuntu | Fedora | openSUSE |
|---|---|---|---|---|
| PyQt5 | `python-pyqt5` | `python3-pyqt5` | `python3-PyQt5` | `python3-qt5` |
| Qt5 Multimedia | `qt5-multimedia` | `python3-pyqt5.qtmultimedia` | `qt5-qtmultimedia` | `libqt5-qtmultimedia` |
| GStreamer good | `gst-plugins-good` | `gstreamer1.0-plugins-good` | `gstreamer1-plugins-good` | `gstreamer-plugins-good` |
| GStreamer libav | `gst-libav` | `gstreamer1.0-libav` | `gstreamer1-libav` | `gstreamer-plugins-libav` |
| ffmpeg | `ffmpeg` | `ffmpeg` | `ffmpeg` | `ffmpeg` |

**Fedora note:** ffmpeg and gstreamer1-libav are not in Fedora's default repositories. The installer will automatically enable RPM Fusion Free before installing these packages. RPM Fusion is the standard Fedora community repo for multimedia codecs.

### Launching

After install:

```bash
fuetem-video
fuetem-video /path/to/video.mp4   # open a specific file
```

Or find it in your application launcher as **Fuetem Video**.

### Running from the dev folder (without installing)

```bash
./fuetem_video.py
./fuetem_video.py /path/to/video.mp4
```

---

## Interface overview

The window is split into two panels:

**Left panel — player**
- Video playback area with GStreamer backend
- Thumbnail timeline showing frames scraped from the loaded file
- Transport controls: skip to start, back 5 s, play/pause, forward 5 s, skip to end
- Time display (current position / total duration)
- Open button and recent files dropdown
- File info card showing codec, resolution, fps, bitrate, file size

**Right panel — tools**
Ten tabs covering every common video operation. All tabs share the currently loaded file. The left panel is always visible while you work through the tabs.

---

## Player controls

| Control | Action |
|---|---|
| Click timeline | Seek to that position |
| Drag timeline | Scrub through the video |
| ⏮ | Jump to start |
| ⏪ | Back 5 seconds |
| ▶ / ⏸ | Play / Pause |
| ⏩ | Forward 5 seconds |
| ⏭ | Jump to end |

The thumbnail timeline loads frame previews in the background after a file is opened. Thumbnails appear progressively — you can use the timeline immediately while they load.

Drag a video file directly onto the player area to open it.

---

## Tab 1 — Trim / Split

Cut a section out of a video, or split a video into multiple parts.

### Trim

Set a start and end time, then export just that segment.

**Start / End fields** — Enter times in `HH:MM:SS.mmm` format (millisecond precision). The `−` and `+` buttons beside each field nudge by exactly one frame based on the loaded file's frame rate (e.g. ~42 ms at 23.98 fps, ~33 ms at 30 fps, ~17 ms at 60 fps).

**Set buttons** — Snap the start or end time to the current playhead position. Play to the exact frame you want, pause, then hit Set.

**Stream copy (fast, no re-encode)** — When checked, ffmpeg copies the video and audio streams without decoding or re-encoding. This is near-instant and lossless. The trade-off is that cuts snap to the nearest keyframe, which may be a second or two off your chosen time. For frame-accurate cuts, uncheck this and re-encode.

**Re-encode options** (visible when stream copy is off) — Choose the output container format, video codec (H.264, H.265, VP9, AV1), and CRF quality value (lower = better quality, larger file; 23 is a sensible default for H.264).

**Save Trim** — Opens a save dialog. The suggested filename is `original_trim.ext`.

### Split

Three ways to split:

**Split Here** — Splits the video at the current playhead position into two files. You choose the output folder; the two parts are saved as `filename_part1.ext` and `filename_part2.ext`. Uses stream copy.

**Split into N equal parts** — Divides the video into N segments of equal duration. Enter the number of parts (2–100), choose an output folder. Uses stream copy.

**Split every N seconds** — Uses ffmpeg's segment muxer to cut the video into chunks of a fixed length. Enter the segment duration in seconds (default 60 s). Uses stream copy. Output files are named `filename_seg000.ext`, `filename_seg001.ext`, etc.

---

## Tab 2 — Convert

Re-encode or remux the video to a different format, codec, resolution, or frame rate.

### Container

Choose the output file format: MP4, MKV, WebM, MOV, AVI, FLV, or TS.

### Video codec

- **libx264** — H.264. Widest compatibility. Good choice for most uses.
- **libx265** — H.265 / HEVC. Roughly half the file size of H.264 at the same quality. Slower to encode. Some older devices don't support it.
- **libvpx-vp9** — VP9. Open format, good for WebM/web delivery.
- **libaom-av1** — AV1. Best compression but very slow. Use veryslow or slow preset only if you have time.
- **copy** — Copy video stream without re-encoding (remux only).
- **none** — Drop the video stream (audio-only output).

**CRF** — Constant Rate Factor. Controls quality vs file size. Lower = better quality, bigger file. Typical values: 18 (high quality), 23 (good), 28 (acceptable, smaller file). Range 0–51 for H.264/H.265; the slider adjusts live.

**Preset** — Encoding speed vs compression efficiency. `ultrafast` encodes quickly but produces larger files. `veryslow` takes much longer but squeezes out better compression. `medium` is a sensible default for most work.

**VAAPI hardware encode** — Uses your GPU's hardware video encoder via VAAPI (requires a compatible Intel/AMD GPU and `/dev/dri/renderD128`). Much faster than CPU encoding, though quality and file size may differ slightly. CRF and preset are ignored in VAAPI mode.

**Two-pass** — Runs ffmpeg twice: first pass analyses the video, second pass encodes with better bit distribution. Produces better quality at a given file size but takes roughly twice as long. Not available with VAAPI.

### Audio codec

- **aac** — Good quality, wide compatibility. Best choice for MP4.
- **libmp3lame** — MP3. Universal compatibility.
- **libopus** — Opus. Excellent quality at low bitrates. Best for WebM.
- **flac** — Lossless audio. Large files.
- **ac3** — Dolby Digital. Common in broadcast/DVD.
- **copy** — Copy audio without re-encoding.
- **none** — Drop the audio stream (video-only output).

**Bitrate** — Audio bitrate. `best` lets the codec choose. 192k is a good default for AAC; 128k is acceptable.

### Resolution

Choose a target resolution or select Custom to enter width and height manually. **Lock aspect** keeps the aspect ratio when you change one dimension. Select Original to keep the source resolution.

### FPS

Change the output frame rate. Useful for converting 60 fps captures down to 30 fps for smaller files, or conforming to broadcast standards (25, 29.97). Select Original to keep the source frame rate.

### Extra args

A freeform text field for any additional ffmpeg arguments, passed directly to the command. Useful for flags like `-movflags +faststart` (web-optimised MP4), `-pix_fmt yuv420p` (force 8-bit colour for maximum compatibility), or any other ffmpeg option not covered by the UI.

**Convert** — Opens a save dialog and starts the encode. A progress bar appears at the bottom of the window. Click Cancel to abort mid-encode.

---

## Tab 3 — Filters

Apply visual and motion effects to the video. Multiple filters can be combined in a single pass — everything checked in this tab is applied together in one ffmpeg run.

### Resize

Scale the output to a preset resolution or enter a custom width and height. **Lock aspect** adjusts the other dimension proportionally when you change one. Uses the `scale` filter with bicubic resampling.

### Crop

Remove pixels from the edges. Set the output width (W) and height (H), then X and Y offsets for the crop window position (top-left origin). Tick **Enable crop** to include this in the output. Useful for removing black bars or reframing a shot.

### Rotate / Flip

- **90° CW** / **90° CCW** / **180°** — Rotate the video. Uses the `transpose` filter.
- **Flip H** — Mirror left-to-right (horizontal flip).
- **Flip V** — Mirror top-to-bottom (vertical flip).

Rotation and flip can be combined.

### Speed

Change playback speed. Options: 0.25×, 0.5×, 0.75×, 1×, 1.25×, 1.5×, 2×, 4×.

**Correct audio pitch** — When enabled, pitch-corrects the audio so speech doesn't sound chipmunk-ey at fast speeds or unnaturally low at slow speeds. Uses the `atempo` filter. Uncheck if you want the raw speed-shifted audio.

### Effects

- **Deinterlace (yadif)** — Removes interlacing artefacts from broadcast/capture footage. Uses the yadif (yet another deinterlacing filter) algorithm.
- **Denoise** — Reduces noise/grain using the `hqdn3d` filter. The slider controls strength (1–10).
- **Sharpen** — Applies an unsharp mask. Slider controls intensity (1–20).
- **Blur** — Applies a Gaussian blur. Slider controls radius (1–20).

### Colour

Four sliders with reset buttons (↺):

- **Brightness** — Range −1.00 to +1.00. Default 0.
- **Contrast** — Range 0.10 to 3.00. Default 1.00.
- **Saturation** — Range 0.00 to 3.00. Default 1.00. Set to 0 for black and white.
- **Gamma** — Range 0.10 to 3.00. Default 1.00.

Uses the `eq` filter. All four are applied together.

### Fade

- **Fade in** — Video fades up from black at the start. Set duration in seconds.
- **Fade out** — Video fades to black at the end. Set duration in seconds.

Both can be enabled simultaneously.

### Watermark / Overlay

Overlay a PNG, JPG, or other image onto the video. Browse for the image file, choose a position (Top-Left, Top-Right, Centre, Bottom-Left, Bottom-Right, or Custom), and set the margin in pixels from the edge. Uses the `overlay` filter.

### Pad / Letterbox

Add black (or coloured) bars around the video to reach a target canvas size without cropping or distorting. Set the target width and height, enter a colour name (e.g. `black`, `white`, `0x1a1a2e`), and tick **Enable pad**. Useful for adding letterbox bars, creating a 16:9 canvas from a 9:16 vertical clip, or padding to a broadcast standard.

### Output

Set the output container format, video codec, and CRF quality for the filtered output. Then click **Apply Filters** to choose a save location and start the encode.

---

## Tab 4 — Audio

Operations that affect only the audio track, or the relationship between audio and video.

### Extract Audio

Export the audio track as a standalone file. Choose a format (MP3, FLAC, Opus, WAV, AAC, M4A, OGG). Tick **Normalize (loudnorm)** to apply EBU R128 loudness normalisation during extraction.

### Remove Audio

Strip all audio tracks and export a silent video. Stream copies the video; fast and lossless.

### Normalize (EBU R128)

Loudness-normalise the audio to broadcast/streaming standards using ffmpeg's two-pass `loudnorm` filter.

- **Target I** — Integrated loudness target in LUFS. Default −16 LUFS (suitable for YouTube, podcasts). Broadcast is typically −23 LUFS (EBU R128) or −24 LUFS (ATSC A/85).
- **TP** — True peak ceiling in dBTP. Default −1.5 dBTP. Prevents inter-sample peaks from clipping after encoding.
- **LRA** — Loudness range in LU. Controls how much dynamic range is preserved. Default 11 LU.

### Volume Adjust

Boost or attenuate the audio level by −20 dB to +20 dB. The slider shows the dB value in real time. Applies the `volume` filter; re-encodes audio.

### Audio Delay

Shift the audio track forward or backward relative to the video.

- **Positive value** — Audio plays later (useful when audio is ahead of video).
- **Negative value** — Audio plays earlier (useful when audio lags behind video).

Range: −10,000 ms to +10,000 ms. Useful for fixing sync issues in recordings.

### Audio Fade

- **Fade in** — Audio fades up from silence at the start. Set duration in seconds.
- **Fade out** — Audio fades to silence at the end. Set duration in seconds.

### Replace Audio

Swap the video's audio track with audio from an external file. Browse for any audio file (MP3, FLAC, WAV, OGG, Opus, M4A, AAC).

**Offset** — Start reading from the audio file at this position (seconds). Useful if you want to use a section of a longer audio file rather than its start.

The output is trimmed to the shorter of the video or audio length (`-shortest`). Video stream is copied without re-encoding.

---

## Tab 5 — Frames

Extract individual frames, create GIFs, generate thumbnails, or build a video from a folder of images.

### Capture Frame

Save a single frame from the current playhead position as an image. Choose format (PNG, JPG, BMP, TIFF, WebP) and quality (1–31; lower is better quality for JPEG). Seek to the exact frame you want in the player, then click **Capture Frame**.

### Extract Frames

Dump multiple frames from the video as image files. Three modes:

- **Every N seconds** — Extract one frame every N seconds. Set N in the spin box.
- **Every Nth frame** — Extract every Nth frame (e.g. every 5th frame).
- **All frames** — Extract every single frame. Warning: can produce thousands of files for longer videos.

Choose an output format (PNG, JPG, etc.) and an output folder. Files are named `filename_frame_0001.ext`, `filename_frame_0002.ext`, etc.

### Create GIF

Convert a section of the video to an animated GIF.

- **Start / End** — Time range to convert. Uses the same `HH:MM:SS.mmm` format as the Trim tab.
- **FPS** — Frame rate of the GIF (1–30). Lower = smaller file. 10–15 fps is typical for GIFs.
- **Width** — Output width in pixels. Height is scaled proportionally.
- **Loops** — Number of times the GIF loops. 0 (∞) loops forever.
- **Dither** — Dithering algorithm for the 256-colour palette:
  - `bayer` — Fast, produces a regular cross-hatch pattern, small files.
  - `floyd_steinberg` — Error diffusion, smoother gradients.
  - `sierra2_4a` — Good balance of quality and file size.
  - `none` — No dithering, fastest, can look blocky on gradients.

Uses ffmpeg's two-step GIF pipeline (palette generation + encoding) for best quality.

### Thumbnail / Poster

Extract a single frame as a poster image. Enter a timestamp, choose a format (JPG, PNG, WebP), and save. Similar to Capture Frame but not tied to the playhead position.

### Image Sequence → Video

Build a video from a folder of numbered image files (a render output, a time-lapse, stop-motion frames, etc.).

- **Input folder** — Browse to the folder containing your images.
- **Pattern** — Glob pattern to match files, e.g. `*.jpg`, `*.png`, `frame_*.png`.
- **FPS** — How many images per second to display.
- **Codec** — Output video codec: H.264, H.265, or VP9.

Does not require a loaded file — this section is independent of the player.

---

## Tab 6 — Merge

Concatenate multiple video files into one.

Add files with **Add Files**, then arrange them into the desired order. You can drag rows to reorder, or use the ▲ / ▼ buttons. **Remove** deletes the selected entry.

**Stream copy** — When checked, all input files are concatenated using ffmpeg's concat demuxer without re-encoding. This is fast and lossless, but requires all files to share the same codec, resolution, and frame rate. If your files differ (e.g. different iPhones, different exports), uncheck this to re-encode through a filter graph.

**Output format** — Choose the container for the merged output.

Click **Merge** to choose a save location. The output is saved in the same folder as the first file in the list by default.

---

## Tab 7 — Subtitles

Add, burn, extract, or remove subtitle tracks.

### Burn Subtitles (Hard Subs)

Permanently render subtitles into the video frames so they are always visible and cannot be turned off. Browse for an SRT or ASS subtitle file.

- **Font size** — Size of the rendered subtitle text (8–96 px). Default 24.
- **Encoding** — Character encoding of the subtitle file. Default UTF-8. Change to match your file if you see garbled characters (e.g. use `cp1252` for Windows Western European files).

Requires re-encoding the video stream.

### Add Soft Subtitle Track

Embed a subtitle file as a selectable track inside the container without burning it into the picture. The viewer can turn subtitles on or off in their player.

- **Language** — ISO 639-2 language code for the track (e.g. `eng`, `jpn`, `fra`).

Note: MP4/M4V containers use `mov_text` codec for soft subs; MKV supports most formats natively. The output container is preserved from the source.

### Extract Subtitle

Pull a subtitle track out of a container and save it as a standalone file.

- **Stream index** — Which subtitle track to extract (0 = first). The range automatically adjusts to the number of subtitle tracks detected in the loaded file.
- **Format** — Output format: SRT, ASS, or VTT.

### Remove All Subtitles

Strip every subtitle track from the container while preserving video and audio. Stream copy; fast and lossless.

---

## Tab 8 — Metadata

Read and write the video's tags (title, artist, date, etc.), or strip all metadata at once.

The fields shown are the most common metadata tags. Load a file and any existing tags will populate the fields automatically. Edit the fields and click **Save Tags** to write them to a new file (the original is not modified).

**Fields:** Title, Artist, Album, Date, Comment, Description, Encoder, Copyright.

**Save Tags** — Writes a new file with the updated tags applied. Stream copies all streams; fast.

**Strip All Metadata** — Removes every metadata tag from every stream and the container using `-map_metadata -1`. Does not touch the video or audio data. For selective metadata removal, use the Privacy tab.

---

## Tab 9 — Analyse

Detailed technical information about the loaded file.

### File information

Displays:

- Container format
- File size
- Duration
- Overall bitrate
- Video stream: codec, resolution (W × H), pixel format, frame rate, video bitrate
- Audio stream: codec, sample rate, channels, audio bitrate

### Device / Camera Data

If the video was recorded on an iPhone or other Apple device, this card appears (highlighted in pink) showing:

- Device make and model (e.g. Apple / iPhone 15 Pro)
- Software / OS version
- Creation date (from `com.apple.quicktime.creationdate`)
- GPS location in decimal degrees with a **Copy coords** link
- Location accuracy

GPS coordinates are parsed from the Apple ISO 6709 format (`+35.7070+139.7366/`).

**Strip Device Tracks** — Removes the mebx and tmcd data streams that carry Apple's binary sensor metadata (IMU, GPS, camera parameters). These streams cause GStreamer to log "Cannot play stream type: unknown" errors; stripping them fixes that. This is the same operation as the Privacy tab's data track removal.

### Error Check

Runs `ffmpeg -v error` on the file and reports any stream errors, decode errors, or container problems. Useful for diagnosing files that behave unexpectedly.

---

## Tab 10 — Privacy

Selectively remove metadata fields from a video — GPS location, device identity, timestamps, and any other tag — while keeping the fields you want to preserve.

### Device Data Tracks

If the file contains device data streams (Apple mebx sensor tracks, tmcd timecodes, etc.), a pink card appears at the top showing how many tracks are present and their type. The **Remove device data tracks** checkbox is pre-ticked. These tracks carry Apple proprietary binary sensor data (IMU, GPS, accelerometer) and serve no purpose in a distributed video.

### Metadata Fields table

A full table of every tag in the file — both format-level (container) tags and per-stream tags — with a checkbox for each row.

**Columns:**
- Checkbox — tick to remove this field
- Source — where the tag lives: `Format` for container-level tags, `Stream N (video/audio/subtitle)` for stream-level tags
- Key — the tag name; privacy-sensitive keys are highlighted in pink
- Value — the current tag value

**Privacy-sensitive fields** (pre-checked, shown in pink):
- `com.apple.quicktime.location.iso6709` — GPS coordinates
- `com.apple.quicktime.location.accuracy.horizontal` — GPS accuracy
- `com.apple.quicktime.creationdate` — recording date/time
- `com.apple.quicktime.make` / `model` / `software` — device identity
- `creation_time` — creation timestamp (format and stream level)
- `encoder` — encoder software/device
- `date`, `copyright`, `description`, `artist`, and other identifying fields

Fields that would break playback or display (`rotate`, `rotation`, `stereo_mode`) are silently excluded from the table and are never removed.

**Selection buttons:**
- **Select Privacy-Sensitive** — tick all fields that are in the privacy-sensitive list, untick the rest
- **Select All** — tick every field
- **Deselect All** — untick every field

**Strip Selected** — Builds and runs an ffmpeg command that:
1. Uses `-map 0:v -map 0:a` (explicit stream mapping) if data tracks are being removed, dropping them from the output
2. Uses `-map_metadata -1` to clear all format-level tags, then re-adds every unchecked format tag
3. Uses `-map_metadata:s:N -1` for each stream that has at least one checked tag, then re-adds the unchecked tags for that stream
4. Copies all streams without re-encoding

The output filename is suggested as `original_private.ext`. The original file is never modified.

---

## Supported input formats

`.mp4` `.mkv` `.mov` `.avi` `.webm` `.flv` `.wmv` `.m4v` `.ts` `.mts` `.m2ts` `.mpeg` `.mpg` `.ogv` `.3gp` `.gif` `.vob` `.f4v` `.divx` `.rmvb`

## Supported frame rates

Original, 120, 60, 59.94, 50, 30, 29.97, 25, 24, 23.976

## Notes on stream copy vs re-encode

Most operations in this app offer a stream copy option. Understanding the difference:

**Stream copy** (`-c copy`) — ffmpeg passes the encoded video/audio data through unchanged. No quality loss, no generation loss, very fast. The limitation is that cuts must align with keyframes (I-frames), which are typically placed every 2–10 seconds depending on the encoder settings. A cut at an arbitrary frame will silently snap to the nearest keyframe.

**Re-encode** — ffmpeg decodes and re-encodes the video. You lose one generation of quality (very small with high CRF settings like 18), and encoding takes longer. The benefit is that cuts are frame-accurate and filters can be applied.

For trimming: if the keyframe snap is acceptable, use stream copy. If you need exact frame cuts, uncheck stream copy and re-encode.

---

## Configuration

The app stores recent files and window state in `~/.config/fuetem-video/`.

---

## Dependencies summary

| Package | Purpose |
|---|---|
| Python 3.10+ | Runtime |
| PyQt5 | GUI framework |
| Qt5 Multimedia | Video playback backend |
| Qt5 Multimedia Widgets | Video display widget |
| GStreamer + gst-libav | Media decoding (used by Qt5 Multimedia) |
| ffmpeg | All encode/decode/filter operations |
