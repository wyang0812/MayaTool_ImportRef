# -*- coding: utf-8 -*-
"""
模組用途：
提供外部執行入口，負責啟動 Reference Easy Import 的主介面。
主要功能：
- 確保 vendor（第三方依賴）可被載入
- 啟動 UI 建立流程
"""
import os
import sys

def _package_root():
    # 取得套件根目錄，用於定位 vendor 路徑
    return os.path.dirname(os.path.abspath(__file__))

def _ensure_vendor_on_path():
    # 將 vendor 目錄加入 sys.path（確保 Qt.py 等可匯入）
    vendor_dir = os.path.join(_package_root(), "vendor")
    if vendor_dir not in sys.path:
        sys.path.insert(0, vendor_dir)

def run():
    """
    對外呼叫入口：
    執行 Reference Easy Import 工具。
    例：
        import Reference_easy_import
        Reference_easy_import.run()
    """
    _ensure_vendor_on_path()  # 確保依賴可用
    from .ui_qt import build_and_show_ui  # 載入 UI 組建函式
    build_and_show_ui()  # 顯示主介面