# X & Xiaohongshu Photo Saver

[![CI](https://github.com/FlyTOmeLight/x-photo-saver/actions/workflows/ci.yml/badge.svg)](https://github.com/FlyTOmeLight/x-photo-saver/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![macOS](https://img.shields.io/badge/macOS-Photos.app-blue)](https://support.apple.com/photos)

Right-click an image on **X (Twitter)** or **Xiaohongshu (Rednote / 小红书)** in Chrome and save it directly into the macOS **Photos** app — original quality, no watermark. Once it's in Photos, iCloud Photos syncs it to your iPhone automatically.

> macOS only. Chrome, Chrome Canary, Brave, and Arc are supported.

## Demo

![Demo](docs/demo.gif)

> Drop a `demo.gif` into `docs/` to populate the screenshot above. Suggested:
> 30s recording showing right-click → "Save image to Photos" → notification →
> the image appearing in Photos.app.

| Right-click on X | Right-click on Xiaohongshu | Photos.app result |
|---|---|---|
| ![X menu](docs/screenshot-x.png) | ![XHS menu](docs/screenshot-xhs.png) | ![Photos](docs/screenshot-photos.png) |

---

## Why

- **Original quality.** X serves compressed thumbnails by default; this extension upgrades the URL to `name=orig` and prefers PNG bytes when available.
- **No watermark.** Xiaohongshu's CDN appends `!nd_dft_wlteh_webp_3` (or similar) to URLs to inject a watermark + format conversion. Stripping the suffix returns the original upload.
- **iPhone sync for free.** Saving to Photos.app means iCloud Photos pushes the image to every Apple device you own.
- **Source URL preserved.** The originating tweet / note URL is written into the EXIF `UserComment`, `XPComment`, and `ImageDescription` fields, so you can always trace where a saved image came from.

## How it works

```
Chrome right-click
        │
        ▼
contextMenus API ──► background.js ──► Native Messaging (stdio)
                                                 │
                                                 ▼
                                              host.py
                                                 │
                                  ┌──────────────┼──────────────┐
                                  ▼              ▼              ▼
                              download       exiftool        osascript
                            (PNG-first       (write          (import to
                             with refer-      source URL      Photos.app)
                             er fix)          to EXIF)
```

## Install

### Prerequisites

```bash
brew install exiftool         # required for EXIF metadata
# Python 3 ships with macOS; no extra deps.
```

### 1. Clone

```bash
git clone https://github.com/<your-user>/x-photo-saver.git
cd x-photo-saver
```

### 2. Install the native messaging host

```bash
./install.sh           # default: stable Chrome
./install.sh canary    # Chrome Canary
./install.sh brave     # Brave
./install.sh arc       # Arc
```

The script writes `~/Library/Application Support/<browser>/NativeMessagingHosts/com.x.photosaver.json` pointing at this directory's `host.py`.

### 3. Load the extension

1. Open `chrome://extensions/`
2. Toggle **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `extension/` folder of this repo
5. Confirm the extension ID matches `cnimapbahdbbaifdpnaknbhmekjbgien`

The ID is deterministic because the public key is committed in `extension/manifest.json`.

### 4. Grant Photos automation

First save will prompt for permission:

> "Chrome wants permission to control Photos."

Approve once. To inspect or revoke later:
**System Settings → Privacy & Security → Automation → Chrome → Photos**.

## Usage

- **X / Twitter**: open any post, right-click an image → **Save image to Photos**.
- **Xiaohongshu**: open any note (`xiaohongshu.com/explore/...`), right-click an image → **Save image to Photos**.

The notification will read `Saved (jpg 1.45MB)` or `Saved (png 3.21MB)`. Use **Save (debug info)** to see the exact upgraded URL that was downloaded.

## Quality details

### X (Twitter)

X stores each upload in two formats: JPEG and (sometimes) PNG. The host tries `format=png&name=orig` first; if the bytes returned aren't a real PNG (X silently returns JPEG for JPEG-only uploads), it falls back to `format=jpg&name=orig`. The actual format is detected via magic-byte sniffing, not URL hints — Photos always sees the correct file extension.

### Xiaohongshu

The XHS CDN adds watermark and format conversion via a `!<transform-tag>` suffix on the path (e.g. `!nd_dft_wlteh_webp_3`). Stripping the tag returns the original upload. The host also tries the alternate clean hosts (`ci.xiaohongshu.com`, `sns-img-bd.xhscdn.com`, `sns-img-hw.xhscdn.com`) in case the primary one is throttled or modified.

The CDN enforces a Referer check — the host sets `Referer: https://www.xiaohongshu.com/` for any `xhscdn.com` request to bypass hotlink protection.

A content script (`content_xhs.js`) is injected on Xiaohongshu pages to:

1. Suppress the page's `contextmenu` / `selectstart` / `copy` blockers.
2. Synthesize a transparent `<img>` overlay on `background-image` divs so Chrome's image-context right-click menu fires.

## Security notes

- The native host **only** accepts messages from this exact extension ID. The `allowed_origins` field in `com.x.photosaver.json` pins it to a single `chrome-extension://...` origin.
- The host downloads images directly via Python's `urllib`. No external services or telemetry.
- `key.pem` (the private key used to derive the extension ID) is gitignored. The public key is committed inside `extension/manifest.json` to keep the ID stable for everyone who installs from this repo.
- If you fork and want a different extension ID, regenerate:

  ```bash
  openssl genrsa -out key.pem 2048
  openssl rsa -in key.pem -pubout -outform DER 2>/dev/null \
    | openssl base64 -A
  # Replace the "key" field in extension/manifest.json with this string.
  openssl rsa -in key.pem -pubout -outform DER 2>/dev/null \
    | openssl dgst -sha256 -binary | xxd -p -c 32 \
    | cut -c1-32 | tr '0-9a-f' 'a-p'
  # Update install.sh's EXT_ID with this hash.
  ```

## File map

```
x-photo-saver/
├── host.py                  # Native messaging host (Python 3, stdlib only)
├── install.sh               # Browser-specific host manifest installer
├── com.x.photosaver.json    # Reference host manifest (templated by install.sh)
├── extension/
│   ├── manifest.json        # MV3 manifest with embedded public key
│   ├── background.js        # Service worker — context menus + native msg dispatch
│   ├── content_xhs.js       # Right-click unblocker for Xiaohongshu
│   └── icon.png
└── README.md
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Specified native messaging host not found` | Run `./install.sh <browser>` matching your browser. Restart the browser. |
| `Failed: HTTP Error 403` on Xiaohongshu | Make sure you're hitting the upgraded URL — `Save (debug info)` shows the actual URL tried. CDN blocks raw curl-style requests; the host sets a Referer for `xhscdn.com`. |
| Right-click menu doesn't appear on Xiaohongshu | Refresh the page after installing the extension — the content script attaches at `document_start`. |
| Photos.app prompt loop | Check **System Settings → Privacy & Security → Automation** and allow Chrome → Photos. |
| File saved as `.jpg` despite PNG preference | The image was originally uploaded as JPEG. X / XHS only have JPEG bytes; PNG is impossible to recover. |

## License

MIT — see [LICENSE](./LICENSE).

## Contributing

PRs welcome. Out-of-scope (so far): Instagram, Weibo, Bilibili, Pixiv, video downloads (XHS / X both store videos on a separate pipeline that this extension does not touch). Patches that add similar single-host watermark-stripping logic for other sites are happily reviewed.
