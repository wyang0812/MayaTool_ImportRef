# -*- coding: utf-8 -*-
"""
模組用途：
提供 Maya 端的常用工具函式（FPS 讀取、相機列舉/shape 查找、連線解除、
安全的 parentConstraint、建立 imagePlane、打鍵與 postInfinity 設定、
解析 rig 名稱 index、依圖檔自動調整 imagePlane 尺寸）。
"""
import maya.cmds as cmds
import os
from maya import mel as mm

def get_scene_fps():
    """
    用途：回傳目前場景 FPS（以 Maya time unit 對照取得）。
    回傳：float（例如 24.0 / 30.0 等），無法判定時預設 24.0。
    備註：支援 'film'/'ntsc' 等常見單位，或 '<數值>fps' 形式。
    """
    unit = cmds.currentUnit(q=True, time=True)
    mapping = {
        'game': 15.0, 'film': 24.0, 'pal': 25.0, 'ntsc': 30.0,
        'show': 48.0, 'palf': 50.0, 'ntscf': 60.0
    }
    if unit in mapping:
        return mapping[unit]
    if unit.endswith('fps'):
        try:
            return float(unit[:-3])
        except:
            pass
    return 24.0

def list_cameras(include_defaults=True):
    """
    用途：列出場景中的相機 transform 名稱清單。
    參數：include_defaults=True 時會包含 'persp/top/front/side'。
    回傳：list[str] 相機 transform 名稱。
    """
    cams = []
    for shp in cmds.ls(type='camera') or []:
        try:
            parents = cmds.listRelatives(shp, p=True, type='transform') or []
            if not parents:
                continue
            cams.append(parents[0])
        except Exception:
            continue

    # 去重保持順序
    seen = set()
    dedup = []
    for c in cams:
        if c not in seen:
            seen.add(c)
            dedup.append(c)
    cams = dedup

    if not include_defaults:
        cams = [c for c in cams if c not in ('persp', 'top', 'front', 'side')]
    return cams

def camera_shape(cam_transform):
    """
    用途：由相機 transform 取得第一個 camera shape。
    回傳：str 或 None。
    """
    shapes = cmds.listRelatives(cam_transform, s=True, type='camera', f=False) or []
    return shapes[0] if shapes else None

def disconnect_all(attr):
    """
    用途：斷開指定屬性（plug）的所有輸入連線。
    參數：attr 例如 'node.attr'。
    備註：逐一嘗試斷線；失敗不拋例外以避免中斷流程。
    """
    cons = cmds.listConnections(attr, s=True, d=False, plugs=True) or []
    for src in cons:
        try:
            cmds.disconnectAttr(src, attr)
        except:
            pass

def safe_parent_constraint(src, dst, maintain_offset=False):
    """
    用途：對 dst 施做 parentConstraint（可控是否維持位移）。
    參數：maintain_offset=False → 無位移貼合（常用於讓 rig 貼相機）。
    回傳：cmds.parentConstraint 的回傳物件。
    """
    return cmds.parentConstraint(src, dst, mo=maintain_offset)

def create_free_image_plane(file_path=None):
    """
    用途：建立「自由 imagePlane」（不綁特定相機），可選擇直接指定檔案。
    行為：
    - showInAllViews=False、maintainRatio=True
    - 若給定 file_path：建立時即帶入，Maya 會依圖檔自動計算比例
    - 啟用 useFrameExtension=1；關閉 displayOnlyIfCurrent（避免只在當前幀顯示）
    回傳：(ip_transform, ip_shape)
    """
    import maya.cmds as cmds

    kwargs = dict(
        showInAllViews=False,
        maintainRatio=True,
    )
    
    if file_path:
        file_path = os.path.normpath(file_path).replace("\\", "/")
        kwargs["fileName"] = file_path

    ip_transform, ip_shape = cmds.imagePlane(**kwargs)

    # 基本顯示選項（逐幀顯示、不要只在當前幀）
    if cmds.attributeQuery('useFrameExtension', n=ip_shape, exists=True):
        cmds.setAttr(ip_shape + '.useFrameExtension', 1)
    if cmds.attributeQuery('displayOnlyIfCurrent', n=ip_shape, exists=True):
        try: cmds.setAttr(ip_shape + '.displayOnlyIfCurrent', 0)
        except: pass

    return ip_transform, ip_shape

def set_anim_keys_spline_and_post_linear(node, attr, keys):
    """
    用途：在 node.attr 依序設key，並將切線設為 spline、postInfinity 設為 linear。
    參數：
    - node/attr：目標 plug，如 ('ctrl', 'frame')
    - keys：[(time, value), ...]，至少兩點（例如 (s-1,0)、(s,1)）
    行為：
    1) 逐點 setKeyframe
    2) keyTangent 設定為 spline（避免 step）
    3) 找到相連的 animCurveT*（TL/TA/TT/TU），直接對曲線節點設 postInfinity=1（linear）
    """
    import maya.cmds as cmds

    plug = "{}.{}".format(node, attr)

    # 1) 設key（確保至少有兩個 key）
    for t, v in keys:
        cmds.setKeyframe(node, at=attr, t=t, v=v)

    # 2) 讓整條曲線切線為 spline（避免 step）
    try:
        cmds.keyTangent(node, at=attr, e=True, itt='spline', ott='spline')
    except Exception:
        pass

    # 3) 找到連到 plug 的所有 animCurveT*（TL/TA/TT/TU）
    anim_types = ['animCurveTL','animCurveTA','animCurveTT','animCurveTU']
    anim_curves = []
    for t in anim_types:
        anim_curves += cmds.listConnections(plug, s=True, d=False, type=t) or []
    anim_curves = list(set(anim_curves))

    # 4) 直接對曲線節點設 postInfinity=1（linear）
    for ac in anim_curves:
        try:
            cmds.setAttr(ac + ".postInfinity", 1)
        except Exception:
            pass

def extract_rig_index_from_grp_name(grp_name, default_index=1):
    """
    用途：從 '<camera>_videoRef_GRP_XX' 名稱中解析尾碼 index。
    例：'persp1_videoRef_GRP_07' → 回傳 7；若無匹配則回傳 default_index。
    """
    import re
    m = re.search(r'_videoRef_GRP_(\d+)$', grp_name)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    return default_index