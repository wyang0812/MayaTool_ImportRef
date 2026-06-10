# -*- coding: utf-8 -*-
"""
模組用途：
提供與影片轉序列、路徑命名與 ffmpeg 呼叫相關的工具。
重點：
- 依 config 的命名規則輸出到：Seq_<影片名>/Seq_<影片名>_####.jpg
- 轉檔完成後回傳：輸出資料夾與「第一張影格」的檔案路徑
"""
import os, subprocess, stat, re
from . import config
from . import maya_utils as MU
import maya.cmds as cmds

def _package_root():
    # 取得目前套件的根目錄（用來定位 tools/ffmpeg）
    import os
    return os.path.dirname(os.path.abspath(__file__))

def _ffmpeg_path():
    # 組合 ffmpeg 的完整路徑（根據平台偵測子資料夾與執行檔名稱）
    sub = config.detect_ffmpeg_subpath()
    p = os.path.join(_package_root(), config.FFMPEG_DIR, sub)
    return os.path.normpath(p)

def _ensure_executable(path):
    # 確保 ffmpeg 具有可執行權限（Unix 類系統需要）
    if os.path.exists(path) and not os.access(path, os.X_OK):
        try:
            os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        except Exception:
            pass

def _video_basename_no_ext(video_path):
    # 回傳不含副檔名的影片檔名（供命名規則使用）
    base = os.path.basename(video_path)
    name, _ = os.path.splitext(base)
    return name

def _safe_name(s):
    # 將不利於路徑/指令解析的字元轉為底線（避免 ffmpeg/OS 解析問題）
    return re.sub(r"[^\w\-.]+", "_", s)

def seq_output_dir_for(video_path):
    """
    依 config 設定，產生輸出資料夾路徑：
    <video-dir>/Seq_<影片名稱>
    """
    safe_base = _safe_name(_video_basename_no_ext(video_path))
    return os.path.join(os.path.dirname(video_path), config.SEQ_DIR_FMT.format(video_name=safe_base))

def seq_file_fmt(video_path, ext):
    """
    依 config 設定，產生 ffmpeg 用的檔名 pattern：
    Seq_<影片名稱>_%04d.<ext>
    （內部先以 0001 取代 frame，再換成 %04d 供 ffmpeg 使用）
    """
    safe_base = _safe_name(_video_basename_no_ext(video_path))
    # 回傳 ffmpeg 可用的 pattern（%04d）
    return config.SEQ_FILE_FMT.format(video_name=safe_base, frame=1, ext=ext).replace("0001", "%04d")

def transcode_video_to_sequence(video_path, target_fps, ext=None, jpg_quality=None):
    """
    影片 → 影格序列（固定 jpg）
    回傳： (out_dir, first_file)
      - out_dir   ：<video-dir>/Seq_<影片名稱>
      - first_file：Seq_<影片名稱>_0001.jpg（或容錯 0000.jpg）

    邏輯：
    1) 決定 ffmpeg 路徑與執行權限
    2) 依 config 決定輸出目錄與 pattern
    3) 以 target_fps 重新取樣（確保與場景 FPS 對齊）
    4) 以 -qscale:v 控制 JPG 品質（由 config.JPG_QUALITY 映射）
    5) 轉檔完成後，回傳第一張影格路徑
    """
    # 固定輸出 jpg（ext 參數保留介面，但實際以 config 為準）
    ext = config.DEFAULT_IMAGE_EXT
    jpg_quality = jpg_quality or config.JPG_QUALITY

    # 1) ffmpeg 路徑與權限
    ffmpeg = _ffmpeg_path()
    if not os.path.exists(ffmpeg):
        raise RuntimeError("找不到內建 ffmpeg，可到 tools/ffmpeg 放置對應平台版本。")

    _ensure_executable(ffmpeg)

    safe_base = _safe_name(_video_basename_no_ext(video_path))

    # 2) 準備輸出資料夾與 pattern
    out_dir = os.path.join(
        os.path.dirname(video_path),
        config.SEQ_DIR_FMT.format(video_name=safe_base)
    )
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # 以 0001 為示例再替換為 %04d，讓 ffmpeg 產生連號檔
    out_pattern = os.path.join(
        out_dir,
        config.SEQ_FILE_FMT.format(video_name=safe_base, frame=1, ext=ext).replace("0001", "%04d")
    )

    # 3) ffmpeg 參數（-r 以目標 FPS 重新取樣）
    cmd = [ffmpeg, "-y", "-i", video_path, "-r", str(float(target_fps))]

    # 4) JPG 品質對應（數字越小品質越好）；簡單映射：100→2, ≥95→3, 其他→4
    qscale = 4
    try:
        q = int(getattr(config, "JPG_QUALITY", 92))
        if q >= 100:
            qscale = 2
        elif q >= 95:
            qscale = 3
        else:
            qscale = 4
    except Exception:
        pass

    cmd += ["-qscale:v", str(qscale), out_pattern]

    # 執行轉檔
    try:
        subprocess.check_call(cmd, shell=False)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("ffmpeg 轉檔失敗：{0}".format(e))

    # 5) 回傳第一張影格：優先 0001，找不到再容錯 0000
    safe_base = _safe_name(_video_basename_no_ext(video_path))
    first_file = os.path.join(
        out_dir,
        config.SEQ_FILE_FMT.format(video_name=safe_base, frame=1, ext=ext)
    )
    if not os.path.exists(first_file):
        alt = os.path.join(
            out_dir,
            config.SEQ_FILE_FMT.format(video_name=safe_base, frame=0, ext=ext)
        )
        if os.path.exists(alt):
            first_file = alt

    return out_dir, first_file
