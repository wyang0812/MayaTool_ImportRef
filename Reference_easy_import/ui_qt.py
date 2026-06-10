# -*- coding: utf-8 -*-
"""
模組用途：
建立並顯示工具 UI（Camera 選擇、來源型別、檔案挑選、FPS、建立與訊息提示）。
重點：
- 相機清單優先顯示「非預設相機」，預設四視角置於清單後方
- Video：使用 ffmpeg 轉成序列再建立
- Image：直接讀取圖片/序列
"""
from Qt import QtWidgets, QtCore, QtCompat
from maya import cmds
import os
from . import maya_utils as MU
from . import config
from .core import create_video_ref


# 取得 Maya 主視窗
def _get_maya_main_window():
    try:
        from maya import OpenMayaUI as omui
    except Exception:
        return None
    ptr = omui.MQtUtil.mainWindow()
    if ptr is None:
        return None
    return QtCompat.wrapInstance(int(ptr), QtWidgets.QWidget)

_WINDOW_OBJECT_NAME = "ReferenceEasyImportWin"
_WIN = None

# 關閉既有同名視窗
def _close_existing():
    global _WIN
    if _WIN is not None:
        try:
            _WIN.close(); _WIN.deleteLater()
        except: pass
        _WIN = None
    for w in QtWidgets.QApplication.topLevelWidgets():
        try:
            if w.objectName() == _WINDOW_OBJECT_NAME:
                w.close(); w.deleteLater()
        except: pass

class MainUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MainUI, self).__init__(parent)
        self.setObjectName(_WINDOW_OBJECT_NAME)
        self.setWindowTitle("Reference Easy Import")
        self.setMinimumWidth(560)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self._build()

    def _build(self):
        lay = QtWidgets.QVBoxLayout(self)

        # Camera
        row_cam = QtWidgets.QHBoxLayout()
        row_cam.addWidget(QtWidgets.QLabel("Camera"))

        self.cam_cb = QtWidgets.QComboBox()

        # 取出所有相機（含預設四視角）
        # 完整列出可用相機，再做排序優先顯示自訂相機
        cams = MU.list_cameras(include_defaults=True)

        # 分組：非預設相機在前，預設四視角在後
        defaults = ('persp', 'top', 'front', 'side')
        custom  = [c for c in cams if c not in defaults]
        system  = [c for c in cams if c in defaults]

        # 各組內排序：自訂相機按字母、系統相機照固定順序
        custom.sort(key=lambda s: s.lower())
        system.sort(key=lambda s: defaults.index(s))

        # 依序加入：自訂相機 → 系統相機
        for c in (custom + system):
            self.cam_cb.addItem(c)

        row_cam.addWidget(self.cam_cb, 1)

        lay.addLayout(row_cam)

        # Source Type
        row_type = QtWidgets.QHBoxLayout()
        row_type.addWidget(QtWidgets.QLabel("Source Type"))
        self.rb_video = QtWidgets.QRadioButton("Video")
        self.rb_image = QtWidgets.QRadioButton("Image")
        self.rb_video.setChecked(True)
        row_type.addWidget(self.rb_video)
        row_type.addWidget(self.rb_image)
        row_type.addStretch(1)
        lay.addLayout(row_type)

        # File picker
        row_file = QtWidgets.QHBoxLayout()
        self.file_le = QtWidgets.QLineEdit()
        btn = QtWidgets.QPushButton("Browse")
        btn.clicked.connect(self._browse)
        row_file.addWidget(QtWidgets.QLabel("File"))
        row_file.addWidget(self.file_le, 1)
        row_file.addWidget(btn)
        lay.addLayout(row_file)

        # Target FPS（只在 Video 時用；預設 = 場景 FPS）
        row_fps = QtWidgets.QHBoxLayout()
        row_fps.addWidget(QtWidgets.QLabel("Target FPS"))
        self.fps_sb = QtWidgets.QDoubleSpinBox()
        self.fps_sb.setDecimals(3)
        self.fps_sb.setRange(1.0, 480.0)
        self.fps_sb.setValue(MU.get_scene_fps())
        row_fps.addWidget(self.fps_sb)
        row_fps.addStretch(1)
        lay.addLayout(row_fps)

        # Lock GRP
        self.lock_ck = QtWidgets.QCheckBox("鎖定最外層 GRP（避免誤動）")
        self.lock_ck.setChecked(bool(getattr(config, "LOCK_GRP_BY_DEFAULT", True)))
        lay.addWidget(self.lock_ck)

        lay.addSpacing(6)
        self.create_btn = QtWidgets.QPushButton("Create Video Ref")
        self.create_btn.clicked.connect(self._do_create)
        lay.addWidget(self.create_btn)

    # 檔案瀏覽器（依來源型別切換濾器）
    def _browse(self):
        if self.rb_video.isChecked():
            filt = "Video Files (*.mp4 *.mov *.avi *.mkv);;All Files (*.*)"
        else:
            filt = "Image/Sequence Files (*.jpg *.jpeg *.png *.tif *.tiff *.exr);;All Files (*.*)"
        dlg = QtWidgets.QFileDialog(self, "Select File")
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dlg.setNameFilter(filt)
        if dlg.exec_():
            self.file_le.setText(dlg.selectedFiles()[0])

    # 收集輸入並建立參考 rig
    # 將 UI 值轉交核心函式 create_video_ref，並顯示結果訊息
    def _do_create(self):
        cam = self.cam_cb.currentText()
        path = self.file_le.text().strip()
        if not path:
            cmds.warning(u"請先選擇檔案")
            return
        src_type = "video" if self.rb_video.isChecked() else "image"
        fps = float(self.fps_sb.value())
        try:
            out = create_video_ref(
                cam_transform=cam,
                source_type=src_type,
                file_path=path,
                target_fps=fps,
                lock_grp=self.lock_ck.isChecked()
            )
            cmds.inViewMessage(
                amg=u"建立完成 ✔ 相機: %s，檔案: %s" % (cam, os.path.basename(out['first_file'])),
                pos='midCenter', fade=True
            )
        except Exception as e:
            cmds.warning(u"[ReferenceEasyImport] 建立失敗：%s" % e)

# 建立並顯示 UI
# 確保舊視窗被清除，並掛載到 Maya 主視窗
def build_and_show_ui():
    global _WIN
    _close_existing()
    parent = _get_maya_main_window()
    _WIN = MainUI(parent=parent)
    _WIN.show()
    try:
        _WIN.raise_(); _WIN.activateWindow()
    except Exception:
        pass
