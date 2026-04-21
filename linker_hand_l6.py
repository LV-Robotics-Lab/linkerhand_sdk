"""High-level wrapper for Linker Hand L6 — single-side and bimanual control.

Usage:
    from linker_hand_l6 import LinkerHandL6, BimanualL6

    # Single hand
    with LinkerHandL6.left() as h:
        h.open()
        h.fist()
        h.set_pose([255, 179, 255, 255, 255, 255])
        h.set_finger(LinkerHandL6.INDEX, 0)
        print(h.get_state())

    # Both hands
    with BimanualL6.auto() as bi:
        bi.open()
        bi.set(left=[...], right=[...])        # independent poses
        bi.mirror([255, 70, 0, 0, 0, 0])       # identical raw values
        bi.preset("thumb_up")                  # anatomical gesture both sides
        print(bi.get_state())

Joint index order (6 joints per hand):
    0 thumb_flex, 1 thumb_abduct, 2 index, 3 middle, 4 ring, 5 pinky
All values are integers 0..255.

Notes:
- `thumb_abduct` has a different neutral on left (~179) vs right (~70), so
  anatomically-equivalent gestures use side-specific values. `preset()` picks
  the right values for each side automatically.
- The wrapper assumes left is on can0 and right is on can1 by default.
  Change via the `can=` kwarg.
"""
from __future__ import annotations

import os
import sys
import time
from typing import Dict, List, Literal, Optional, Sequence

_HERE = os.path.dirname(os.path.abspath(__file__))
_SDK_DIR = os.path.join(_HERE, "LinkerHand")
if _SDK_DIR not in sys.path:
    sys.path.insert(0, _SDK_DIR)

from linker_hand_api import LinkerHandApi  # noqa: E402

Side = Literal["left", "right"]
Pose = Sequence[int]

JOINT_NAMES = ("thumb_flex", "thumb_abduct", "index", "middle", "ring", "pinky")

# Anatomical gesture presets. Thumb-abduct (index 1) differs per side because
# the two hands are mirror-image mechanisms with different neutral angles.
PRESETS: Dict[str, Dict[str, List[int]]] = {
    "open":     {"left": [255, 179, 255, 255, 255, 255], "right": [255,  70, 255, 255, 255, 255]},
    "fist":     {"left": [ 67, 151,   0,   0,   0,   0], "right": [ 49,  61,   0,   0,   0,   0]},
    "thumb_up": {"left": [255,  31,   0,   0,   0,   0], "right": [255,  70,   0,   0,   0,   0]},
    "ok":       {"left": [ 54,  41, 164, 250, 250, 250], "right": [ 54,  41, 164, 250, 250, 250]},
    "point":    {"left": [  0,  31, 255,   0,   0,   0], "right": [  0,  70, 255,   0,   0,   0]},
    "two":      {"left": [  0,  31, 255, 255,   0,   0], "right": [  0,  70, 255, 255,   0,   0]},
    "three":    {"left": [  0,  30, 255, 255, 255,   0], "right": [  0,  70, 255, 255, 255,   0]},
    "four":     {"left": [  0,  30, 255, 255, 255, 255], "right": [  0,  70, 255, 255, 255, 255]},
    "five":     {"left": [250, 250, 250, 250, 250, 250], "right": [250, 250, 250, 250, 250, 250]},
}


def _clamp_pose(pose: Pose) -> List[int]:
    if len(pose) != 6:
        raise ValueError(f"L6 pose must have exactly 6 values, got {len(pose)}")
    return [max(0, min(255, int(v))) for v in pose]


class LinkerHandL6:
    """Single-side Linker Hand L6 over SocketCAN."""

    # Joint index constants for readable per-finger addressing.
    THUMB_FLEX, THUMB_ABDUCT, INDEX, MIDDLE, RING, PINKY = range(6)

    def __init__(self, side: Side, can: str = "can0"):
        if side not in ("left", "right"):
            raise ValueError(f"side must be 'left' or 'right', got {side!r}")
        self.side: Side = side
        self.can = can
        self._api = LinkerHandApi(hand_type=side, hand_joint="L6", can=can)
        time.sleep(0.3)  # give the handshake a moment to settle

    # Convenience constructors -------------------------------------------------
    @classmethod
    def left(cls, can: str = "can0") -> "LinkerHandL6":
        return cls("left", can)

    @classmethod
    def right(cls, can: str = "can1") -> "LinkerHandL6":
        return cls("right", can)

    # Motion commands ----------------------------------------------------------
    def set_pose(self, pose: Pose) -> None:
        """Send all 6 joint values (0..255)."""
        self._api.finger_move(_clamp_pose(pose))

    def set_finger(self, idx: int, value: int) -> None:
        """Move a single finger, holding the others at their current state."""
        if not 0 <= idx < 6:
            raise IndexError(f"joint index must be 0..5, got {idx}")
        pose = self.get_state()
        if len(pose) != 6:
            pose = list(PRESETS["open"][self.side])
        pose[idx] = value
        self.set_pose(pose)

    def preset(self, name: str) -> None:
        """Apply a named anatomical gesture (e.g. 'open', 'fist', 'ok')."""
        entry = PRESETS.get(name.lower())
        if entry is None:
            raise KeyError(f"unknown preset {name!r}; valid: {sorted(PRESETS)}")
        self.set_pose(entry[self.side])

    # Preset shortcuts
    def open(self) -> None:     self.preset("open")
    def fist(self) -> None:     self.preset("fist")
    def thumb_up(self) -> None: self.preset("thumb_up")
    def ok(self) -> None:       self.preset("ok")
    def point(self) -> None:    self.preset("point")
    def two(self) -> None:      self.preset("two")
    def three(self) -> None:    self.preset("three")
    def four(self) -> None:     self.preset("four")
    def five(self) -> None:     self.preset("five")

    # Tuning -------------------------------------------------------------------
    def set_speed(self, speed: Pose = (180,) * 6) -> None:
        self._api.set_joint_speed(list(speed))

    def set_torque(self, torque: Pose = (180,) * 6) -> None:
        self._api.set_torque(list(torque))

    # Status -------------------------------------------------------------------
    def get_state(self) -> List[int]:        return list(self._api.get_state())
    def get_current(self) -> List[int]:      return list(self._api.get_current())
    def get_torque(self) -> List[int]:       return list(self._api.get_torque())
    def get_temperature(self) -> List[int]:  return list(self._api.get_temperature())
    def get_fault(self) -> List[int]:        return list(self._api.get_fault())
    def get_serial_number(self) -> str:      return self._api.get_serial_number()

    # Lifecycle ----------------------------------------------------------------
    def close(self) -> None:
        if hasattr(self._api, "close_can"):
            try: self._api.close_can()
            except Exception: pass

    def __enter__(self) -> "LinkerHandL6":
        return self

    def __exit__(self, *_exc) -> None:
        # Leave the hand in a safe rest pose, then release the CAN handle.
        try: self.open()
        except Exception: pass
        self.close()

    def __repr__(self) -> str:
        return f"LinkerHandL6(side={self.side!r}, can={self.can!r})"


class BimanualL6:
    """Coordinated control of a left + right L6 pair.

    Exposes `bi.left` and `bi.right` for per-side access, plus top-level
    convenience methods that act on both hands.
    """

    def __init__(self, left: LinkerHandL6, right: LinkerHandL6):
        if left.side != "left" or right.side != "right":
            raise ValueError("BimanualL6 needs a LEFT and a RIGHT LinkerHandL6")
        self.left = left
        self.right = right

    @classmethod
    def auto(cls, left_can: str = "can0", right_can: str = "can1") -> "BimanualL6":
        """Connect to left on can0 and right on can1 (the defaults)."""
        return cls(LinkerHandL6.left(left_can), LinkerHandL6.right(right_can))

    # Coordinated commands -----------------------------------------------------
    def set(self,
            left: Optional[Pose] = None,
            right: Optional[Pose] = None) -> None:
        """Send (possibly different) poses to each side. None = skip that side."""
        if left is not None:
            self.left.set_pose(left)
        if right is not None:
            self.right.set_pose(right)

    def mirror(self, pose: Pose) -> None:
        """Send identical raw joint values to both hands.

        WARNING: this is not an anatomical mirror — the two hands have
        different neutral angles for thumb_abduct, so identical values
        will *look* asymmetric. For gestures that should look symmetric,
        use `preset()` instead.
        """
        both = _clamp_pose(pose)
        self.left.set_pose(both)
        self.right.set_pose(both)

    def preset(self, name: str) -> None:
        """Apply a named gesture to both hands (anatomically mirrored)."""
        self.left.preset(name)
        self.right.preset(name)

    # Preset shortcuts
    def open(self) -> None:     self.preset("open")
    def fist(self) -> None:     self.preset("fist")
    def thumb_up(self) -> None: self.preset("thumb_up")
    def ok(self) -> None:       self.preset("ok")
    def point(self) -> None:    self.preset("point")
    def two(self) -> None:      self.preset("two")
    def three(self) -> None:    self.preset("three")
    def four(self) -> None:     self.preset("four")
    def five(self) -> None:     self.preset("five")

    # Status -------------------------------------------------------------------
    def get_state(self) -> Dict[str, List[int]]:
        return {"left": self.left.get_state(), "right": self.right.get_state()}

    def get_fault(self) -> Dict[str, List[int]]:
        return {"left": self.left.get_fault(), "right": self.right.get_fault()}

    def get_temperature(self) -> Dict[str, List[int]]:
        return {"left": self.left.get_temperature(), "right": self.right.get_temperature()}

    def get_current(self) -> Dict[str, List[int]]:
        return {"left": self.left.get_current(), "right": self.right.get_current()}

    # Lifecycle ----------------------------------------------------------------
    def close(self) -> None:
        try: self.left.close()
        except Exception: pass
        try: self.right.close()
        except Exception: pass

    def __enter__(self) -> "BimanualL6":
        return self

    def __exit__(self, *_exc) -> None:
        try: self.open()
        except Exception: pass
        self.close()

    def __repr__(self) -> str:
        return f"BimanualL6(left={self.left!r}, right={self.right!r})"


__all__ = [
    "LinkerHandL6",
    "BimanualL6",
    "PRESETS",
    "JOINT_NAMES",
    "Side",
    "Pose",
]


# ---------------------------------------------------------------------------
# Demo — run this file directly for a quick hello-world on both hands.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Linker Hand L6 wrapper demo")
    p.add_argument("--mode", choices=["left", "right", "bimanual"], default="bimanual")
    p.add_argument("--dwell", type=float, default=1.0)
    args = p.parse_args()

    if args.mode == "left":
        with LinkerHandL6.left() as h:
            for g in ("open", "fist", "thumb_up", "ok", "point", "open"):
                print(f"left -> {g}")
                h.preset(g); time.sleep(args.dwell)
    elif args.mode == "right":
        with LinkerHandL6.right() as h:
            for g in ("open", "fist", "thumb_up", "ok", "point", "open"):
                print(f"right -> {g}")
                h.preset(g); time.sleep(args.dwell)
    else:
        with BimanualL6.auto() as bi:
            print("serials:", bi.left.get_serial_number(), "|", bi.right.get_serial_number())
            for g in ("open", "fist", "thumb_up", "ok", "point", "two", "three", "four", "five", "open"):
                print(f"both -> {g}")
                bi.preset(g); time.sleep(args.dwell)
            print("\nSplit pose: left=fist, right=open")
            bi.set(left=PRESETS["fist"]["left"], right=PRESETS["open"]["right"])
            time.sleep(args.dwell * 1.5)
            print("state:", bi.get_state())
