import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from urllib.request import Request, urlopen
import json
import re
import customtkinter as ctk
import yt_dlp

APP_NAME = "Video Downloader"
APP_VERSION = "2.2.3"
GITHUB_REPO = "tereshchenkopavlo-gif/VideoDownloader"

def resource_path(name):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return str(base / name)

def version_tuple(value):
    nums = re.findall(r"\d+", str(value))
    return tuple(int(x) for x in nums[:3]) if nums else (0, 0, 0)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("980x720")
        self.minsize(850, 650)
        self.url_var = tk.StringVar()
        self.folder_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.quality_var = tk.StringVar(value="Best")
        self.format_var = tk.StringVar(value="MP4")
        self.speed_var = tk.StringVar(value="1.0×")
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)
        self.speed_status_var = tk.StringVar(value="")
        self.eta_var = tk.StringVar(value="")
        self.cancel_event = threading.Event()
        self.download_active = False
        self.config_file = Path(os.environ.get("APPDATA", str(Path.home()))) / APP_NAME / "settings.json"
        self._load_settings()
        self._build()
        self.after(1500, lambda: threading.Thread(target=self.check_updates, args=(True,), daemon=True).start())

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        header = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 10))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Video Downloader", font=ctk.CTkFont(size=30, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text=f"Version {APP_VERSION}  •  yt-dlp + FFmpeg", text_color=("gray45", "gray65")).grid(row=1, column=0, sticky="w", pady=(2, 0))
        ctk.CTkButton(header, text="Check for updates", width=145, command=lambda: threading.Thread(target=self.check_updates, args=(False,), daemon=True).start()).grid(row=0, column=1, rowspan=2, padx=(20, 0))

        url_card = ctk.CTkFrame(self, corner_radius=14)
        url_card.grid(row=1, column=0, sticky="ew", padx=28, pady=10)
        url_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(url_card, text="Video URL", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=18, pady=(15, 8))
        self.url_entry = ctk.CTkEntry(url_card, textvariable=self.url_var, height=40, placeholder_text="Paste a video URL here…")
        self.url_entry.grid(row=1, column=0, sticky="ew", padx=(18, 8), pady=(0, 16))
        ctk.CTkButton(url_card, text="Paste", width=90, height=40, command=self.paste).grid(row=1, column=1, padx=4, pady=(0, 16))
        ctk.CTkButton(url_card, text="Get info", width=100, height=40, command=self.info).grid(row=1, column=2, padx=(4, 18), pady=(0, 16))

        options = ctk.CTkFrame(self, corner_radius=14)
        options.grid(row=2, column=0, sticky="ew", padx=28, pady=10)
        options.grid_columnconfigure(1, weight=1)
        options.grid_columnconfigure(3, weight=1)
        ctk.CTkLabel(options, text="Download options", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=18, pady=(15, 12))
        ctk.CTkLabel(options, text="Quality").grid(row=1, column=0, sticky="w", padx=(18, 8), pady=7)
        ctk.CTkOptionMenu(options, variable=self.quality_var, values=["Best", "2160p", "1440p", "1080p", "720p", "480p", "360p", "Audio only"], width=150).grid(row=1, column=1, sticky="ew", padx=8, pady=7)
        ctk.CTkLabel(options, text="Format").grid(row=1, column=2, sticky="w", padx=(18, 8), pady=7)
        ctk.CTkOptionMenu(options, variable=self.format_var, values=["MP4", "MKV", "WEBM"], width=130).grid(row=1, column=3, sticky="ew", padx=(8, 18), pady=7)
        ctk.CTkLabel(options, text="Playback speed").grid(row=2, column=0, sticky="w", padx=(18, 8), pady=7)
        speed_values = [f"{x / 10:.1f}×" for x in range(5, 21)]
        ctk.CTkOptionMenu(options, variable=self.speed_var, values=speed_values, width=150).grid(row=2, column=1, sticky="ew", padx=8, pady=7)
        ctk.CTkLabel(options, text="0.5× = slower  •  2.0× = faster", text_color=("gray45", "gray65")).grid(row=2, column=2, columnspan=2, sticky="w", padx=(18, 18), pady=7)
        ctk.CTkLabel(options, text="Save to").grid(row=3, column=0, sticky="w", padx=(18, 8), pady=(7, 15))
        ctk.CTkEntry(options, textvariable=self.folder_var, height=36).grid(row=3, column=1, columnspan=2, sticky="ew", padx=8, pady=(7, 15))
        ctk.CTkButton(options, text="Browse…", width=110, height=36, command=self.browse).grid(row=3, column=3, padx=(8, 18), pady=(7, 15))

        content = ctk.CTkFrame(self, corner_radius=14)
        content.grid(row=3, column=0, sticky="nsew", padx=28, pady=10)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(content, text="Information", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, sticky="w", padx=18, pady=(15, 8))
        self.info_text = ctk.CTkTextbox(content, height=150, corner_radius=10)
        self.info_text.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 15))
        self.info_text.configure(state="disabled")

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=4, column=0, sticky="ew", padx=28, pady=(5, 20))
        bottom.grid_columnconfigure(3, weight=1)
        self.download_button = ctk.CTkButton(bottom, text="Download", width=150, height=44, font=ctk.CTkFont(size=14, weight="bold"), command=self.download)
        self.download_button.grid(row=0, column=0, padx=(0, 8))
        self.cancel_button = ctk.CTkButton(bottom, text="Cancel", width=100, height=44, fg_color=("gray80", "gray25"), hover_color=("gray70", "gray35"), command=self.cancel_download, state="disabled")
        self.cancel_button.grid(row=0, column=1, padx=8)
        ctk.CTkButton(bottom, text="Open folder", width=120, height=44, fg_color=("gray90", "gray20"), hover_color=("gray80", "gray30"), text_color=("gray15", "white"), border_width=1, command=self.open_folder).grid(row=0, column=2, padx=8)
        ctk.CTkLabel(bottom, textvariable=self.status_var).grid(row=0, column=3, sticky="e", padx=(10, 0))
        self.progress = ctk.CTkProgressBar(bottom, variable=self.progress_var, height=10)
        self.progress.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(16, 6))
        ctk.CTkLabel(bottom, textvariable=self.speed_status_var, text_color=("gray45", "gray65")).grid(row=2, column=0, sticky="w")
        ctk.CTkLabel(bottom, textvariable=self.eta_var, text_color=("gray45", "gray65")).grid(row=2, column=3, sticky="e")

    def _load_settings(self):
        try:
            if self.config_file.exists():
                data = json.loads(self.config_file.read_text(encoding="utf-8"))
                folder = data.get("download_folder")
                if folder and Path(folder).exists():
                    self.folder_var.set(folder)
        except Exception:
            pass

    def _save_settings(self):
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            self.config_file.write_text(json.dumps({"download_folder": self.folder_var.get()}, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def paste(self):
        try: self.url_var.set(self.clipboard_get())
        except tk.TclError: pass

    def browse(self):
        p = filedialog.askdirectory(initialdir=self.folder_var.get())
        if p:
            self.folder_var.set(p)
            self._save_settings()

    def show_info(self, text):
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", text)
        self.info_text.configure(state="disabled")

    def info(self):
        url = self.url_var.get().strip()
        if not url: return messagebox.showwarning(APP_NAME, "Paste a video URL first.")
        self.status_var.set("Reading information…")
        threading.Thread(target=self._info, args=(url,), daemon=True).start()

    def _info(self, url):
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True}) as ydl:
                d = ydl.extract_info(url, download=False)
            dur = d.get("duration")
            if dur:
                seconds = int(dur)
                dur = f"{seconds // 3600}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}" if seconds >= 3600 else f"{seconds // 60}:{seconds % 60:02d}"
            else:
                dur = "—"
            width = d.get("width")
            height = d.get("height")
            resolution = f"{width}×{height}" if width and height else "—"
            filesize = d.get("filesize") or d.get("filesize_approx")
            size_text = f"{filesize / (1024 * 1024):.1f} MB" if filesize else "—"
            views = d.get("view_count")
            views_text = f"{views:,}" if isinstance(views, int) else "—"
            upload_date = d.get("upload_date")
            upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}" if upload_date and len(upload_date) == 8 else "—"
            text = (
                f"Title: {d.get('title', '—')}\n"
                f"Uploader: {d.get('uploader', '—')}\n"
                f"Duration: {dur}\n"
                f"Resolution: {resolution}\n"
                f"Estimated size: {size_text}\n"
                f"Views: {views_text}\n"
                f"Upload date: {upload_date}\n"
                f"Website: {d.get('webpage_url', url)}"
            )
            self.after(0, lambda: (self.show_info(text), self.status_var.set("Ready")))
        except Exception as e:
            self.after(0, lambda: self.status_var.set("Could not read video"))
            self.after(0, lambda: messagebox.showerror(APP_NAME, str(e)))

    def progress_hook(self, d):
        if self.cancel_event.is_set():
            raise yt_dlp.utils.DownloadError("Download cancelled by user.")
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes", 0)
            pct = (done / total) if total else 0
            self.after(0, self.progress_var.set, min(1, pct))
            self.after(0, self.speed_status_var.set, f"Speed: {d.get('_speed_str', '')}")
            self.after(0, self.eta_var.set, f"ETA: {d.get('_eta_str', '')}")
        elif d["status"] == "finished":
            self.after(0, self.progress_var.set, 1)

    def download(self):
        if self.download_active:
            return
        url = self.url_var.get().strip()
        if not url: return messagebox.showwarning(APP_NAME, "Paste a video URL first.")
        Path(self.folder_var.get()).mkdir(parents=True, exist_ok=True)
        self._save_settings()
        self.cancel_event.clear()
        self.download_active = True
        self.download_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.status_var.set("Downloading…")
        self.progress_var.set(0)
        self.speed_status_var.set("")
        self.eta_var.set("")
        threading.Thread(target=self._download, args=(url,), daemon=True).start()

    def cancel_download(self):
        if self.download_active:
            self.cancel_event.set()
            self.status_var.set("Cancelling…")
            self.cancel_button.configure(state="disabled")

    def _download(self, url):
        q = self.quality_var.get()
        fmt = self.format_var.get().lower()
        speed = float(self.speed_var.get().replace("×", ""))
        audio_only = q == "Audio only"
        if audio_only:
            f = "bestaudio/best"
            post = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
            merge_format = None
        else:
            heights = {"2160p": 2160, "1440p": 1440, "1080p": 1080, "720p": 720, "480p": 480, "360p": 360}
            f = "bestvideo+bestaudio/best" if q == "Best" else f"bestvideo[height<={heights[q]}]+bestaudio/best[height<={heights[q]}]"
            post = []
            merge_format = fmt
        folder = Path(self.folder_var.get())
        speed_suffix = "" if speed == 1.0 else f" [{speed:.1f}x]"
        outtmpl = str(folder / f"%(title)s{speed_suffix}.%(ext)s")
        opts = {"format": f, "outtmpl": outtmpl, "progress_hooks": [self.progress_hook], "postprocessor_hooks": [self._postprocessor_hook], "noplaylist": False}
        if merge_format: opts["merge_output_format"] = merge_format
        if post: opts["postprocessors"] = post
        ff = resource_path("ffmpeg.exe")
        if os.path.exists(ff): opts["ffmpeg_location"] = str(Path(ff).parent)
        expected_paths = []
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                expected_paths = self._expected_files(info, audio_only, fmt, outtmpl)
                ydl.download([url])
            if self.cancel_event.is_set():
                raise yt_dlp.utils.DownloadError("Download cancelled by user.")
            if speed != 1.0:
                for path in expected_paths:
                    if self.cancel_event.is_set():
                        raise yt_dlp.utils.DownloadError("Download cancelled by user.")
                    if path.exists(): self._change_speed(path, speed)
            self.after(0, lambda: self.status_var.set("Completed"))
            self.after(0, lambda: messagebox.showinfo(APP_NAME, "Download completed."))
        except yt_dlp.utils.DownloadError as e:
            if self.cancel_event.is_set() or "cancelled by user" in str(e).lower():
                self._cleanup_partial_files(expected_paths)
                self.after(0, lambda: self.status_var.set("Cancelled"))
            else:
                self.after(0, lambda: self.status_var.set("Error"))
                self.after(0, lambda: messagebox.showerror(APP_NAME, str(e)))
        except Exception as e:
            self.after(0, lambda: self.status_var.set("Error"))
            self.after(0, lambda: messagebox.showerror(APP_NAME, str(e)))
        finally:
            self.download_active = False
            self.cancel_event.clear()
            self.after(0, lambda: self.download_button.configure(state="normal"))
            self.after(0, lambda: self.cancel_button.configure(state="disabled"))

    def _cleanup_partial_files(self, paths):
        for path in paths:
            for candidate in (path, Path(str(path) + ".part"), Path(str(path) + ".ytdl")):
                try:
                    if candidate.exists():
                        candidate.unlink()
                except OSError:
                    pass

    def _expected_files(self, info, audio_only, fmt, outtmpl):
        entries = info.get("entries") if isinstance(info, dict) else None
        if entries:
            result = []
            for entry in entries:
                if entry: result.extend(self._expected_files(entry, audio_only, fmt, outtmpl))
            return result
        with yt_dlp.YoutubeDL({"outtmpl": outtmpl}) as ydl:
            filename = Path(ydl.prepare_filename(info))
        return [filename.with_suffix(".mp3" if audio_only else f".{fmt}")]

    def _postprocessor_hook(self, d):
        if self.cancel_event.is_set():
            raise yt_dlp.utils.DownloadError("Download cancelled by user.")

    def _probe_duration(self, source):
        ffprobe = resource_path("ffprobe.exe")
        if not os.path.exists(ffprobe):
            return 0.0
        try:
            result = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(source)],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
                check=True,
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    def _change_speed(self, source, speed):
        ffmpeg = resource_path("ffmpeg.exe")
        if not os.path.exists(ffmpeg):
            raise RuntimeError("FFmpeg is required to change playback speed.")

        temp = source.with_name(source.stem + ".speedtmp" + source.suffix)
        ext = source.suffix.lower()
        duration = self._probe_duration(source)

        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(source)]
        if ext == ".mp3":
            cmd += ["-filter:a", f"atempo={speed}", "-c:a", "libmp3lame", "-b:a", "192k"]
        else:
            if ext == ".webm":
                vcodec, acodec = "libvpx-vp9", "libopus"
                extra = ["-crf", "32", "-b:v", "0", "-b:a", "128k"]
            else:
                vcodec, acodec = "libx264", "aac"
                extra = ["-crf", "20", "-preset", "medium", "-b:a", "192k"]
            cmd += ["-filter:v", f"setpts=PTS/{speed}", "-filter:a", f"atempo={speed}", "-c:v", vcodec, "-c:a", acodec] + extra
        cmd += ["-progress", "pipe:1", "-nostats", str(temp)]

        self.after(0, self.status_var.set, f"Applying {speed:.1f}× speed…")
        self.after(0, self.progress_var.set, 0)
        self.after(0, self.speed_status_var.set, "Processing with FFmpeg…")
        self.after(0, self.eta_var.set, "")

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            bufsize=1, creationflags=creationflags,
        )

        try:
            while True:
                if self.cancel_event.is_set():
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    raise yt_dlp.utils.DownloadError("Download cancelled by user.")

                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    if line.startswith("out_time_ms=") and duration:
                        try:
                            current = int(line.split("=", 1)[1]) / 1_000_000
                            pct = max(0.0, min(1.0, current / duration))
                            self.after(0, self.progress_var.set, pct)
                            self.after(0, self.speed_status_var.set, f"Applying {speed:.1f}× speed… {pct * 100:.0f}%")
                        except ValueError:
                            pass
                    continue
                if process.poll() is not None:
                    break

            stderr = process.stderr.read()
            return_code = process.wait()
            if return_code != 0:
                raise RuntimeError(stderr.strip() or "FFmpeg failed while changing playback speed.")
            if self.cancel_event.is_set():
                raise yt_dlp.utils.DownloadError("Download cancelled by user.")
            os.replace(temp, source)
            self.after(0, self.progress_var.set, 1)
            self.after(0, self.speed_status_var.set, "")
        except Exception:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            try:
                if temp.exists():
                    temp.unlink()
            except OSError:
                pass
            raise

    def open_folder(self):
        p = str(Path(self.folder_var.get()).resolve())
        if sys.platform.startswith("win"): os.startfile(p)
        elif sys.platform == "darwin": subprocess.Popen(["open", p])
        else: subprocess.Popen(["xdg-open", p])

    def check_updates(self, silent):
        try:
            req = Request(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest", headers={"Accept": "application/vnd.github+json", "User-Agent": APP_NAME})
            with urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
            latest = data.get("tag_name", "")
            if version_tuple(latest) <= version_tuple(APP_VERSION):
                if not silent:
                    self.after(0, lambda: messagebox.showinfo(APP_NAME, f"You are using the latest version ({APP_VERSION})."))
                return
            asset = next((a for a in data.get("assets", []) if a.get("name", "").lower().endswith(".exe")), None)
            if not asset: return
            answer = [False]
            def ask(): answer[0] = messagebox.askyesno(APP_NAME, f"A new version {latest} is available.\n\nUpdate now?")
            self.after(0, ask)
            while not answer[0] and self.winfo_exists():
                self.update()
                threading.Event().wait(0.05)
            if answer[0]: self._install_update(asset["browser_download_url"], asset.get("name", "VideoDownloader-Setup.exe"))
        except Exception as e:
            if not silent:
                self.after(0, lambda: messagebox.showerror(APP_NAME, f"Could not check for updates.\n\n{e}"))

    def _install_update(self, url, filename):
        temp = Path(os.environ.get("TEMP", str(Path.home() / "AppData/Local/Temp"))) / filename
        self.after(0, lambda: self.status_var.set("Downloading update…"))
        req = Request(url, headers={"User-Agent": APP_NAME})
        with urlopen(req, timeout=30) as response, open(temp, "wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk: break
                out.write(chunk)
        subprocess.Popen([str(temp)])
        self.after(0, self.destroy)

if __name__ == "__main__":
    App().mainloop()
