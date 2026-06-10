# -*- coding: utf-8 -*-
"""
模組用途：
提供外部呼叫入口與必要模組載入設定。
可直接使用：
    import Reference_easy_import
    Reference_easy_import.run()
"""

import importlib
import sys
import os

# 加入 vendor 目錄（Qt.py 等第三方套件所在）
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_vendor_dir = os.path.join(_pkg_dir, "vendor")
if _vendor_dir not in sys.path:
    sys.path.insert(0, _vendor_dir)

# 對外主要入口：開啟 UI
from .app import run

# 掛載常用子模組，方便外部直接呼叫
for _name in ("maya_utils", "media", "core", "ui_qt"):
    _mod = importlib.import_module("%s.%s" % (__name__, _name))
    globals()[_name] = _mod

# 清理暫時變數，保持命名空間乾淨
del _name, _mod, _pkg_dir, _vendor_dir, importlib, sys, os
