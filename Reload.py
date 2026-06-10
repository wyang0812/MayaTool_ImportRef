# -*- coding: utf-8 -*-
"""
Safe reset for 'Reference_easy_import' (modules, UI, caches) without restarting Maya.
All messages and comments are in English to avoid encoding issues on non-UTF-8 setups.
"""

import sys
import os
import shutil
import tempfile
import importlib

import maya.cmds as cmds
import maya.utils

TARGET_TAG = "Reference_easy_import"  # ASCII-only tag used in names and temp paths


def _close_windows():
    """Close any Maya windows/docks/workspaceControls that match our tag in name or title."""
    # Regular windows
    for w in (cmds.lsUI(type="window") or []):
        try:
            title = ""
            try:
                title = cmds.window(w, q=True, title=True) or ""
            except:
                pass
            if TARGET_TAG in w or TARGET_TAG in title:
                cmds.deleteUI(w, window=True)
        except:
            pass

    # Legacy dockControl
    for d in (cmds.lsUI(type="dockControl") or []):
        try:
            if TARGET_TAG in d:
                cmds.deleteUI(d, control=True)
        except:
            pass

    # WorkspaceControl (Maya 2017+ / Qt docks)
    for wc in (cmds.lsUI(type="workspaceControl") or []):
        try:
            if TARGET_TAG in wc:
                try:
                    cmds.workspaceControl(wc, e=True, close=True)
                except:
                    pass
                try:
                    cmds.deleteUI(wc)
                except:
                    pass
        except:
            pass


# 1) Close UI elements created by the tool
_close_windows()

# 2) Purge loaded Python modules for a clean re-import
mods = [m for m in list(sys.modules)
        if m == TARGET_TAG or m.startswith(TARGET_TAG + ".")]
for m in mods:
    try:
        del sys.modules[m]
    except:
        pass

# 3) Invalidate Python import caches so fresh files are picked up
try:
    if hasattr(importlib, "invalidate_caches"):
        importlib.invalidate_caches()
except Exception:
    pass

# 4) Remove any sys.path entries that point to temp copies of this tool
for p in list(sys.path):
    try:
        if p and TARGET_TAG in p:
            sys.path.remove(p)
    except:
        pass

# 5) Remove temp files/folders that include the tag
tmp = tempfile.gettempdir()
try:
    for name in os.listdir(tmp):
        if TARGET_TAG in name:
            path = os.path.join(tmp, name)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)
            except:
                pass
except:
    pass

# 6) Notify in the viewport (ASCII-only message to avoid encoding pitfalls)
maya.utils.executeDeferred(lambda: cmds.inViewMessage(
    amg='<hl>:D {} reset</hl> :D modules, UI, and caches cleared. Next import loads fresh.'
        .format(TARGET_TAG),
    pos='midCenter', fade=True))

print("[{}] Reset complete. Next import will load fresh from disk.".format(TARGET_TAG))
