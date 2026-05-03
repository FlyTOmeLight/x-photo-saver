# Demo assets

Place screenshots and demo recordings here. Filenames the README expects:

| File | Recommended size | Suggested content |
|---|---|---|
| `demo.gif` | ≤ 5 MB, ≤ 1280×720, 15 fps | 20–30 s loop: right-click on X / XHS → "Save image to Photos" → notification → Photos.app shows the imported image |
| `screenshot-x.png` | 1024 px wide | Chrome window showing right-click context menu on a tweet image with the "Save image to Photos" entry highlighted |
| `screenshot-xhs.png` | 1024 px wide | Same but on a `xiaohongshu.com/explore/...` page |
| `screenshot-photos.png` | 1024 px wide | Photos.app with a freshly-imported image, ideally with EXIF panel visible showing the source URL in the comment field |

## Recording tips

- Built-in: <kbd>⌘</kbd>+<kbd>⇧</kbd>+<kbd>5</kbd> on macOS for screen capture; convert MOV to GIF with `ffmpeg`:

  ```bash
  ffmpeg -i input.mov -vf "fps=15,scale=1280:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" -loop 0 docs/demo.gif
  ```

- Crop tightly. Hide bookmarks bar and personal notifications first.
- Test the GIF renders well on both light and dark GitHub themes.
