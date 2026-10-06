import os, sys, threading, subprocess, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import yt_dlp

APP_NAME = "Video Downloader"
APP_VERSION = "2.1.0"

def resource_path(name):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return str(base / name)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("900x620")
        self.minsize(760, 520)
        self.url_var = tk.StringVar()
        self.folder_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.quality_var = tk.StringVar(value="Best")
        self.format_var = tk.StringVar(value="MP4")
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)
        self.speed_var = tk.StringVar(value="")
        self.eta_var = tk.StringVar(value="")
        self._build()
    def _build(self):
        pad = {"padx": 14, "pady": 8}
        title = ttk.Label(self, text="▶ Video Downloader", font=("Segoe UI", 20, "bold"))
        title.pack(anchor="w", **pad)
        ttk.Label(self, text="Download videos supported by yt-dlp.").pack(anchor="w", padx=14)
        box = ttk.LabelFrame(self, text="Video URL")
        box.pack(fill="x", **pad)
        row = ttk.Frame(box); row.pack(fill="x", padx=10, pady=10)
        ttk.Entry(row, textvariable=self.url_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Paste", command=self.paste).pack(side="left", padx=6)
        ttk.Button(row, text="Get info", command=self.info).pack(side="left")
        opts = ttk.LabelFrame(self, text="Options")
        opts.pack(fill="x", **pad)
        grid = ttk.Frame(opts); grid.pack(fill="x", padx=10, pady=10)
        ttk.Label(grid, text="Quality").grid(row=0,column=0,sticky="w")
        ttk.Combobox(grid,textvariable=self.quality_var,state="readonly",
                     values=["Best","2160p","1440p","1080p","720p","480p","360p","Audio only"],width=14).grid(row=0,column=1,padx=8)
        ttk.Label(grid, text="Format").grid(row=0,column=2,sticky="w")
        ttk.Combobox(grid,textvariable=self.format_var,state="readonly",
                     values=["MP4","MKV","WEBM"],width=10).grid(row=0,column=3,padx=8)
        ttk.Label(grid, text="Folder").grid(row=1,column=0,sticky="w",pady=(10,0))
        ttk.Entry(grid,textvariable=self.folder_var).grid(row=1,column=1,columnspan=2,sticky="ew",pady=(10,0))
        ttk.Button(grid,text="Browse…",command=self.browse).grid(row=1,column=3,padx=8,pady=(10,0))
        grid.columnconfigure(1,weight=1); grid.columnconfigure(2,weight=1)
        info = ttk.LabelFrame(self, text="Information")
        info.pack(fill="x", **pad)
        self.info_text = tk.Text(info,height=5,wrap="word",state="disabled")
        self.info_text.pack(fill="x",padx=10,pady=10)
        actions = ttk.Frame(self); actions.pack(fill="x", **pad)
        ttk.Button(actions,text="Download",command=self.download).pack(side="left")
        ttk.Button(actions,text="Open folder",command=self.open_folder).pack(side="left",padx=8)
        ttk.Label(actions,textvariable=self.status_var).pack(side="right")
        ttk.Progressbar(self,variable=self.progress_var,maximum=100).pack(fill="x",padx=14,pady=8)
        ttk.Label(self,textvariable=self.speed_var).pack(anchor="w",padx=14)
        ttk.Label(self,textvariable=self.eta_var).pack(anchor="w",padx=14)
    def paste(self):
        try: self.url_var.set(self.clipboard_get())
        except tk.TclError: pass
    def browse(self):
        p=filedialog.askdirectory(initialdir=self.folder_var.get())
        if p: self.folder_var.set(p)
    def show_info(self, text):
        self.info_text.config(state="normal"); self.info_text.delete("1.0","end"); self.info_text.insert("1.0",text); self.info_text.config(state="disabled")
    def info(self):
        url=self.url_var.get().strip()
        if not url: return messagebox.showwarning(APP_NAME,"Paste a video URL first.")
        self.status_var.set("Reading information…")
        threading.Thread(target=self._info,args=(url,),daemon=True).start()
    def _info(self,url):
        try:
            with yt_dlp.YoutubeDL({"quiet":True,"no_warnings":True,"skip_download":True}) as ydl:
                d=ydl.extract_info(url,download=False)
            dur=d.get("duration"); dur=f"{int(dur)//60}:{int(dur)%60:02d}" if dur else "—"
            text=f"Title: {d.get('title','—')}\nUploader: {d.get('uploader','—')}\nDuration: {dur}\nViews: {d.get('view_count','—')}"
            self.after(0,lambda:(self.show_info(text),self.status_var.set("Ready")))
        except Exception as e:
            self.after(0,lambda: self.status_var.set("Could not read video"))
            self.after(0,lambda: messagebox.showerror(APP_NAME,str(e)))
    def progress(self,d):
        if d["status"]=="downloading":
            total=d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done=d.get("downloaded_bytes",0)
            pct=(done/total*100) if total else 0
            self.after(0,self.progress_var.set,pct)
            self.after(0,self.speed_var.set,f"Speed: {d.get('_speed_str','')}")
            self.after(0,self.eta_var.set,f"ETA: {d.get('_eta_str','')}")
        elif d["status"]=="finished":
            self.after(0,self.progress_var.set,100)
    def download(self):
        url=self.url_var.get().strip()
        if not url: return messagebox.showwarning(APP_NAME,"Paste a video URL first.")
        Path(self.folder_var.get()).mkdir(parents=True,exist_ok=True)
        self.status_var.set("Downloading…"); self.progress_var.set(0)
        threading.Thread(target=self._download,args=(url,),daemon=True).start()
    def _download(self,url):
        q=self.quality_var.get(); fmt=self.format_var.get().lower()
        if q=="Audio only":
            f="bestaudio/best"
            post=[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
            merge_format=None
        else:
            heights={"2160p":2160,"1440p":1440,"1080p":1080,"720p":720,"480p":480,"360p":360}
            f="bestvideo+bestaudio/best" if q=="Best" else f"bestvideo[height<={heights[q]}]+bestaudio/best[height<={heights[q]}]"
            post=[]
            merge_format=fmt
        opts={"format":f,"outtmpl":str(Path(self.folder_var.get())/"%(title)s.%(ext)s"),
              "progress_hooks":[self.progress],"noplaylist":False}
        if merge_format:
            opts["merge_output_format"]=merge_format
        if post:
            opts["postprocessors"]=post
        ff=resource_path("ffmpeg.exe")
        if os.path.exists(ff): opts["ffmpeg_location"]=str(Path(ff).parent)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([url])
            self.after(0,lambda:self.status_var.set("Completed"))
            self.after(0,lambda:messagebox.showinfo(APP_NAME,"Download completed."))
        except Exception as e:
            self.after(0,lambda:self.status_var.set("Error"))
            self.after(0,lambda:messagebox.showerror(APP_NAME,str(e)))
    def open_folder(self):
        p=str(Path(self.folder_var.get()).resolve())
        if sys.platform.startswith("win"): os.startfile(p)
        elif sys.platform=="darwin": subprocess.Popen(["open",p])
        else: subprocess.Popen(["xdg-open",p])

if __name__=="__main__":
    App().mainloop()
