# -*- coding: utf-8 -*-
"""
模組用途：
集中管理「命名、初始姿態、輸出與 UI 預設」等設定，供其他模組讀取。
調整策略：
- 只在這裡改數值；core / media / ui 皆讀此設定，避免分散硬寫。
"""
import os, sys, platform

# =========================================================
# 命名規則（同一個 rig 的 GRP/CTRL/IP 使用同一個 index）
# 例：<camera>_videoRef_GRP_01 / CTRL_01 / IP_01
# =========================================================
GRP_FMT  = "{camera}_videoRef_GRP_{index:02d}"
CTRL_FMT = "{camera}_videoRef_CTRL_{index:02d}"
IP_FMT   = "{camera}_videoRef_IP_{index:02d}"

# =========================================================
# 初始姿態（建立時預設 Transform 值）
# - CTRL_INIT：控制器（預設往相機後方一點，縮小避免擋視線）
# - IP_INIT  ：imagePlane（預設放在 CTRL 右下方，放大方便辨識）
# 想要「零姿態」可直接把以下數值改為 0 / 1
# =========================================================
CTRL_INIT = { "tz": -5.0, "sx": 0.06, "sy": 0.06, "sz": 0.06 }
IP_INIT   = { "tx": 9.0, "ty": -8.0, "tz": 0.0, "sx": 3.0, "sy": 3.0, "sz": 3.0 }

# =========================================================
# 影片→序列輸出（固定輸出 jpg）
# - 目錄：與原影片同一路徑，建立 Seq_<影片名稱>
# - 檔名：Seq_<影片名稱>_####.jpg
# - 品質：JPG_QUALITY 會在 media.py 映射為 ffmpeg 的 -qscale:v
# =========================================================
DEFAULT_IMAGE_EXT = "jpg" 
JPG_QUALITY       = 92
SEQ_DIR_FMT  = "Seq_{video_name}"
SEQ_FILE_FMT = "Seq_{video_name}_{frame:04d}.{ext}"

# =========================================================
# UI 預設
# - INCLUDE_DEFAULT_CAMERAS：是否在相機下拉顯示 persp/top/front/side
# - LOCK_GRP_BY_DEFAULT    ：建立後預設鎖定最外層 GRP（避免誤動）
# =========================================================
INCLUDE_DEFAULT_CAMERAS = True   # 仍可能需要選到預設視角時可保留 True
LOCK_GRP_BY_DEFAULT     = True    # True: 預設勾選鎖定最外層 GRP

# =========================================================
# ffmpeg 執行檔位置（相對於套件根目錄的 tools/ffmpeg）
# detect_ffmpeg_subpath() 依平台回傳子路徑，供 media.py 組合完整路徑
# =========================================================
FFMPEG_DIR = os.path.join("tools", "ffmpeg")

def detect_ffmpeg_subpath():
    sysname = platform.system().lower()
    if "windows" in sysname or sys.platform.startswith("win"):
        return os.path.join("win64", "ffmpeg.exe")
    elif "darwin" in sysname or sysname == "macos" or sysname == "mac":
    # macOS：優先 arm64，必要時可自行改為 x64
        return os.path.join("mac-arm64", "ffmpeg")
    elif "linux" in sysname:
        return os.path.join("linux-x64", "ffmpeg")
    # 預設回傳 Windows 版本，避免空字串
    return os.path.join("win64", "ffmpeg.exe")
