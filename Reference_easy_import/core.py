# -*- coding: utf-8 -*-
"""
模組用途：
建立「影片／影像參考 rig」的核心流程。
主要任務：
- 解析 UI 傳入參數（相機、來源型別、檔案路徑、FPS、是否鎖定 GRP）
- 建立整套層級（GRP / CTRL / imagePlane），並與相機對齊
- 視來源型別決定是否轉序列（ffmpeg）或直接載入
- 建立 CTRL 自訂屬性（offset / frame）並連到 imagePlane
- 設定自動播放（打兩個關鍵，postInfinity=linear）
錯誤處理：
- 關鍵條件不成立時以 cmds.error 中止；非關鍵問題使用 cmds.warning 提示
"""
import os
import maya.cmds as cmds
from . import config
from . import maya_utils as MU

def create_video_ref(
    cam_transform,
    source_type,          # "video" or "image"
    file_path,            # 選到的影片 或 圖片/序列中任一張
    target_fps,           # 只在 video 時用
    lock_grp=False
):
    # 檢查輸入與場景狀態
    if not cmds.objExists(cam_transform):
        cmds.error(u'找不到相機：%s' % cam_transform)
    cam_shape = MU.camera_shape(cam_transform)   
    if not cam_shape:
        cmds.error(u'選到的不是有效相機：%s' % cam_transform)
    if not file_path:
        cmds.error(u'請選擇影片或圖片檔案。')
    if not os.path.exists(file_path):
        cmds.error(u'找不到檔案：%s' % file_path)

    # 取得場景 FPS 與時間軸起始格
    scene_fps = MU.get_scene_fps()
    s = float(cmds.playbackOptions(q=True, min=True))

    # 建立最外層 GRP（先嘗試 _01；若重名 Maya 會自動進位）
    # rig 的根節點，後續 CTRL/IP 都掛在底下；命名規則統一由 config 決定
    req_grp_name = config.GRP_FMT.format(camera=cam_transform, index=1)
    top_grp = cmds.group(em=True, name=req_grp_name)

    # GRP 立刻貼到相機（parentConstraint，無偏移）
    MU.safe_parent_constraint(cam_transform, top_grp, maintain_offset=False)

    # 以「實際建立出來的 GRP 名稱」解析 index
    idx = MU.extract_rig_index_from_grp_name(top_grp, default_index=1)
    idx_str = "{:02d}".format(idx)

    # 用同一個 index 生成 CTRL/IP 名稱
    ctrl_name = config.CTRL_FMT.format(camera=cam_transform, index=idx)
    ip_name   = config.IP_FMT.format(camera=cam_transform, index=idx)
    ip_shape_name = ip_name + "Shape"

    # 建立 CTRL
    ctrl = cmds.circle(name=ctrl_name, nr=(0,0,1), ch=False, r=2.0)[0]
    cmds.parent(ctrl, top_grp)

    # 平移：X=0, Y=0, Z=依照 config（例如 -5）
    cmds.setAttr(ctrl + ".translateX", 0.0)
    cmds.setAttr(ctrl + ".translateY", 0.0)
    cmds.setAttr(ctrl + ".translateZ", config.CTRL_INIT.get("tz", -5.0))

    # 旋轉：全部歸零（RX/RY/RZ）
    for ax in ('X','Y','Z'):
        cmds.setAttr("{}.rotate{}".format(ctrl, ax), 0.0)

    # 縮放：依照 config
    for ax, key in (("X","sx"),("Y","sy"),("Z","sz")):
        cmds.setAttr("{}.scale{}".format(ctrl, ax), float(config.CTRL_INIT.get(key, 1.0)))


    # （可選）鎖最外層 GRP 的 TRS
    if lock_grp:
        for a in ('tx','ty','tz','rx','ry','rz','sx','sy','sz'):
            try:
                cmds.setAttr("{}.{}".format(top_grp, a), lock=True, keyable=False, channelBox=False)
            except:
                pass

    # 決定影像來源（video→轉序列；image→直接套用）
    final_first_file = file_path
    if source_type == "video":
        from .media import transcode_video_to_sequence
        seq_dir, first_file = transcode_video_to_sequence(
            video_path=file_path,
            target_fps=target_fps or scene_fps,
            ext=config.DEFAULT_IMAGE_EXT,
            jpg_quality=config.JPG_QUALITY
        )
        final_first_file = first_file

    # ----------------------------
    # 建立 imagePlane（建立時就帶 fileName）
    # Maya 會依檔案自動設定寬高比例；之後再微調顯示屬性
    # ----------------------------
    ip_transform, ip_shape = MU.create_free_image_plane(file_path=final_first_file)

    # 將 imagePlane 掛到 CTRL 底下並初始化姿態（旋轉歸零、平移/縮放依照 config）
    cmds.parent(ip_transform, ctrl)
    for ax in ("X","Y","Z"):
        cmds.setAttr("{}.rotate{}".format(ip_transform, ax), 0.0)
    for ax, key in (("X","sx"),("Y","sy"),("Z","sz")):
        cmds.setAttr("{}.scale{}".format(ip_transform, ax), float(config.IP_INIT.get(key, 1.0)))
    cmds.setAttr("{}.translateX".format(ip_transform), float(config.IP_INIT.get("tx", 0.0)))
    cmds.setAttr("{}.translateY".format(ip_transform), float(config.IP_INIT.get("ty", 0.0)))
    cmds.setAttr("{}.translateZ".format(ip_transform), float(config.IP_INIT.get("tz", 0.0)))

    # 重新命名 transform 與 shape（兩者使用同一個 index）
    try:
        ip_transform = cmds.rename(ip_transform, ip_name)
    except Exception:
        pass

    shapes = cmds.listRelatives(ip_transform, s=True, f=False) or []
    img_shapes = [shp for shp in shapes if cmds.nodeType(shp) == 'imagePlane']
    if not img_shapes:
        cmds.error(u"找不到 imagePlane 的 shape，建立失敗。")
    ip_shape = img_shapes[0]

    try:
        ip_shape = cmds.rename(ip_shape, ip_shape_name)
    except Exception:
        pass

    # 設定顯示屬性（useFrameExtension / displayOnlyIfCurrent）
    if cmds.attributeQuery('useFrameExtension', n=ip_shape, exists=True):
        cmds.setAttr(ip_shape + '.useFrameExtension', 1)
    if cmds.attributeQuery('displayOnlyIfCurrent', n=ip_shape, exists=True):
        try:
            cmds.setAttr(ip_shape + '.displayOnlyIfCurrent', 0)
        except:
            pass

    # 在 CTRL 新增自訂屬性 offset / frame
    # offset：整數值（長整型 attribute，預設 0）
    if not cmds.attributeQuery('offset', n=ctrl, exists=True):
        cmds.addAttr(ctrl, ln='offset', at='long', k=True, dv=0)
    else:
        cmds.setAttr(ctrl + '.offset', e=True, k=True, dv=0)

    # frame：整數值（長整型 attribute）
    if not cmds.attributeQuery('frame', n=ctrl, exists=True):
        cmds.addAttr(ctrl, ln='frame', at='long', k=True, dv=0)
    else:
        cmds.setAttr(ctrl + '.frame', e=True, k=True, dv=0)


    # 連線 offset/frame → imagePlane（frameOffset/frameExtension）
    if cmds.attributeQuery('frameOffset', n=ip_shape, exists=True):
        MU.disconnect_all(ip_shape + '.frameOffset')
        try:
            cmds.connectAttr(ctrl + '.offset', ip_shape + '.frameOffset', f=True)
        except:
            pass
    else:
        cmds.warning(u"此版本 imagePlane 沒有 frameOffset 屬性（將略過）。")

    if cmds.attributeQuery('frameExtension', n=ip_shape, exists=True):
        MU.disconnect_all(ip_shape + '.frameExtension')
        try:
            cmds.connectAttr(ctrl + '.frame', ip_shape + '.frameExtension', f=True)
        except:
            pass
    else:
        cmds.warning(u"此版本 imagePlane 沒有 frameExtension 屬性（將略過）。")

    # 建立自動播放
    # 為 frame 設兩個 key：t=s-1→0；t=s→1；tangent=spline；postInfinity=linear
    s = float(s)
    MU.set_anim_keys_spline_and_post_linear(
        node=ctrl,
        attr='frame',
        keys=[(s-1.0, 0.0), (s, 1.0)]
    )

    cmds.select(ctrl)
    cmds.inViewMessage(
        amg=u'建立完成 ✔（Free Image Plane + CTRL offset/frame）',
        pos='midCenter', fade=True
    )

    return {
        'group': top_grp,
        'ctrl': ctrl,
        'ip_transform': ip_transform,
        'ip_shape': ip_shape,
        'scene_fps': scene_fps,
        'start': s,
        'first_file': final_first_file
    }
