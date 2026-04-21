#!/usr/bin/env python3
"""Dual-hand slider GUI for Linker Hand L6.

Controls left hand on can0 AND right hand on can1 at the same time.
Each hand has 6 joint sliders (0-255) plus preset gesture buttons.
A "Sync both" checkbox mirrors any movement to the other hand.
"""
import os, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "LinkerHand"))

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSlider, QLabel, QPushButton, QGroupBox, QCheckBox, QMessageBox,
)

from linker_hand_api import LinkerHandApi

JOINT_NAMES = [
    "Thumb flex",
    "Thumb abduct",
    "Index",
    "Middle",
    "Ring",
    "Pinky",
]

# L6 presets from example/gui_control/config/constants.py, per-side tuned values
PRESETS_LEFT = {
    "Open":     [255, 179, 255, 255, 255, 255],
    "Fist":     [67,  151, 0,   0,   0,   0],
    "Thumb-up": [255, 31,  0,   0,   0,   0],
    "OK":       [54,  41,  164, 250, 250, 250],
    "One":      [0,   31,  255, 0,   0,   0],
    "Two":      [0,   31,  255, 255, 0,   0],
    "Three":    [0,   30,  255, 255, 255, 0],
    "Four":     [0,   30,  255, 255, 255, 255],
    "Five":     [250, 250, 250, 250, 250, 250],
}
PRESETS_RIGHT = {
    "Open":     [255, 70,  255, 255, 255, 255],
    "Fist":     [49,  61,  0,   0,   0,   0],
    "Thumb-up": [255, 70,  0,   0,   0,   0],
    "OK":       [54,  41,  164, 250, 250, 250],
    "One":      [0,   70,  255, 0,   0,   0],
    "Two":      [0,   70,  255, 255, 0,   0],
    "Three":    [0,   70,  255, 255, 255, 0],
    "Four":     [0,   70,  255, 255, 255, 255],
    "Five":     [250, 250, 250, 250, 250, 250],
}

INIT_LEFT  = PRESETS_LEFT["Open"]
INIT_RIGHT = PRESETS_RIGHT["Open"]


class HandPanel(QGroupBox):
    """One panel = 6 sliders + preset buttons for one hand. Emits pose_changed(list[int])."""
    pose_changed = pyqtSignal(list)

    def __init__(self, title, presets, init_pose, parent=None):
        super().__init__(title, parent)
        self.presets = presets
        self._pose = list(init_pose)
        self._emitting = True  # set False when applying external updates to avoid echo

        outer = QVBoxLayout(self)

        # Sliders grid
        grid = QGridLayout()
        self.sliders = []
        self.value_labels = []
        for i, name in enumerate(JOINT_NAMES):
            grid.addWidget(QLabel(name), i, 0)
            sl = QSlider(Qt.Horizontal)
            sl.setRange(0, 255)
            sl.setValue(init_pose[i])
            sl.setTickPosition(QSlider.TicksBelow)
            sl.setTickInterval(32)
            sl.valueChanged.connect(lambda v, idx=i: self._on_slider(idx, v))
            grid.addWidget(sl, i, 1)
            vl = QLabel(str(init_pose[i]))
            vl.setMinimumWidth(32)
            vl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(vl, i, 2)
            self.sliders.append(sl)
            self.value_labels.append(vl)
        outer.addLayout(grid)

        # Preset buttons grid (3 cols)
        btn_box = QGroupBox("Presets")
        btn_grid = QGridLayout(btn_box)
        for idx, (name, pose) in enumerate(self.presets.items()):
            b = QPushButton(name)
            b.clicked.connect(lambda _, p=pose: self.apply_pose(p, emit=True))
            btn_grid.addWidget(b, idx // 3, idx % 3)
        outer.addWidget(btn_box)

    def _on_slider(self, idx, v):
        self._pose[idx] = v
        self.value_labels[idx].setText(str(v))
        if self._emitting:
            self.pose_changed.emit(list(self._pose))

    def apply_pose(self, pose, emit=False):
        """Set all sliders to pose values. If emit=False, don't re-emit pose_changed."""
        self._emitting = emit
        try:
            for i, v in enumerate(pose):
                v = max(0, min(255, int(v)))
                self.sliders[i].setValue(v)
                # slider.setValue triggers _on_slider which sets _pose[i] and label
        finally:
            self._emitting = True
        if emit:
            # explicit emit since _on_slider was suppressed
            self._pose = [max(0, min(255, int(x))) for x in pose]
            self.pose_changed.emit(list(self._pose))

    def current_pose(self):
        return list(self._pose)


class DualHandWindow(QWidget):
    def __init__(self, left_api, right_api):
        super().__init__()
        self.left_api = left_api
        self.right_api = right_api
        self.setWindowTitle("Linker Hand L6 — Dual Control (left=can0 / right=can1)")

        top = QHBoxLayout()
        self.sync_cb = QCheckBox("Sync both hands (mirror movement)")
        self.sync_cb.setChecked(False)
        top.addWidget(self.sync_cb)
        top.addStretch()
        self.reset_btn = QPushButton("Reset both → Open")
        self.reset_btn.clicked.connect(self.reset_all)
        top.addWidget(self.reset_btn)

        hands = QHBoxLayout()
        self.left_panel  = HandPanel("Left hand (can0)",  PRESETS_LEFT,  INIT_LEFT)
        self.right_panel = HandPanel("Right hand (can1)", PRESETS_RIGHT, INIT_RIGHT)
        hands.addWidget(self.left_panel)
        hands.addWidget(self.right_panel)

        root = QVBoxLayout(self)
        root.addLayout(top)
        root.addLayout(hands)

        # Wire slider/preset events → send over CAN, and sync if enabled
        self.left_panel.pose_changed.connect(self.on_left_changed)
        self.right_panel.pose_changed.connect(self.on_right_changed)

        # Throttle: coalesce rapid slider events into ~20Hz sends
        self._pending_left = None
        self._pending_right = None
        self._tx_timer = QTimer(self)
        self._tx_timer.setInterval(50)
        self._tx_timer.timeout.connect(self._flush_tx)
        self._tx_timer.start()

        # Push initial open pose on startup
        self._pending_left = INIT_LEFT[:]
        self._pending_right = INIT_RIGHT[:]

    def on_left_changed(self, pose):
        self._pending_left = pose
        if self.sync_cb.isChecked():
            # Mirror to right, but using RIGHT-hand preset for the thumb-abduct axis
            # (joint index 1). Keep index 0 and 2-5 identical. This is a naive mirror.
            mirrored = pose[:]
            # Simple: just copy same values (user can pick "Open"/"Fist" per side if needed)
            self._pending_right = mirrored
            self.right_panel.apply_pose(mirrored, emit=False)

    def on_right_changed(self, pose):
        self._pending_right = pose
        if self.sync_cb.isChecked():
            mirrored = pose[:]
            self._pending_left = mirrored
            self.left_panel.apply_pose(mirrored, emit=False)

    def _flush_tx(self):
        if self._pending_left is not None:
            try:
                self.left_api.finger_move(self._pending_left)
            except Exception as e:
                print(f"[left] send error: {e}", file=sys.stderr)
            self._pending_left = None
        if self._pending_right is not None:
            try:
                self.right_api.finger_move(self._pending_right)
            except Exception as e:
                print(f"[right] send error: {e}", file=sys.stderr)
            self._pending_right = None

    def reset_all(self):
        self.left_panel.apply_pose(INIT_LEFT, emit=True)
        self.right_panel.apply_pose(INIT_RIGHT, emit=True)


def main():
    # Connect both hands up front — fail fast if either is not reachable.
    print("Connecting to LEFT hand on can0...")
    left_api = LinkerHandApi(hand_type="left", hand_joint="L6", can="can0")
    print("Connecting to RIGHT hand on can1...")
    right_api = LinkerHandApi(hand_type="right", hand_joint="L6", can="can1")

    app = QApplication(sys.argv)
    w = DualHandWindow(left_api, right_api)
    w.resize(900, 520)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
