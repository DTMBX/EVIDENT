# Evident Technologies — Ubuntu 24.04 System Dependencies

System-level packages required before installing the Python forensic stack.
Install on the deployment target (Ubuntu 24.04 LTS) or CI runner.

## Install All

```bash
sudo apt-get update && sudo apt-get install -y \
  tesseract-ocr \
  poppler-utils \
  libgl1 \
  ffmpeg \
  mediainfo \
  exiftool \
  libssl-dev \
  libffi-dev \
  libsodium-dev
```

## Package Reference

| Package | Required By | Purpose |
|---------|-------------|---------|
| `tesseract-ocr` | `pytesseract` (extraction) | OCR engine for scanned documents |
| `poppler-utils` | `pdf2image` (extraction) | PDF rendering (`pdftoppm`, `pdfinfo`) |
| `libgl1` | `opencv-python-headless` (extraction) | OpenGL backend for headless CV |
| `ffmpeg` | `moviepy`, `pydub`, `openai-whisper` (media) | Audio/video transcoding |
| `mediainfo` | forensic metadata pipeline (media) | Media container metadata extraction |
| `exiftool` | forensic metadata pipeline (media) | EXIF / XMP metadata extraction |
| `libssl-dev` | `cryptography` (crypto) | OpenSSL development headers |
| `libffi-dev` | `cryptography` (crypto) | Foreign function interface |
| `libsodium-dev` | `PyNaCl` (crypto) | NaCl / libsodium cryptography |

## Notes

- **Windows development**: Most packages have Python wheel binaries or are
  bundled. FFmpeg must be installed separately
  ([gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or `winget install ffmpeg`).
- **macOS**: Use `brew install tesseract poppler ffmpeg libsodium exiftool mediainfo`.
- **Docker**: Include the `apt-get install` block in your `Dockerfile`.
