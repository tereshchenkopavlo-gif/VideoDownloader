# Video Downloader

A modern Windows desktop video downloader based on yt-dlp and FFmpeg.

## Features

- YouTube and other sites supported by yt-dlp
- Quality selection from 360p to 2160p
- MP4, MKV and WEBM
- Audio-only MP3
- Playback speed from 0.5× to 2.0×
- Modern Windows interface
- Built-in update checker and installer download
- GitHub Actions builds the Windows installer automatically

## Release workflow

- Push to `main` → build artifact
- Push a tag like `v2.2.0` → build and publish a GitHub Release

The app does not bypass DRM, paywalls, or access controls. Use it only for content you are authorized to download.
