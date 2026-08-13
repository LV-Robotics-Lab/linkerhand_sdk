#!/usr/bin/env python3
"""Run the L6 preset gesture set on one or both hands."""
import sys, os, time, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "LinkerHand"))
from linker_hand_api import LinkerHandApi

# Per README: L6 order = [Thumb Flex, Thumb Abduct, Index, Middle, Ring, Pinky], values 0-255
GESTURES_LEFT = [
    ("张开 Open",    [255, 179, 255, 255, 255, 255]),
    ("壹 One",       [0,   31,  255, 0,   0,   0]),
    ("贰 Two",       [0,   31,  255, 255, 0,   0]),
    ("叁 Three",     [0,   30,  255, 255, 255, 0]),
    ("肆 Four",      [0,   30,  255, 255, 255, 255]),
    ("伍 Five",      [250, 250, 250, 250, 250, 250]),
    ("OK",           [54,  41,  164, 250, 250, 250]),
    ("点赞 Thumb-up",[255, 31,  0,   0,   0,   0]),
    ("握拳 Fist",    [67,  151, 0,   0,   0,   0]),
    ("张开 Open",    [255, 179, 255, 255, 255, 255]),
]

# Right hand: same pose shape, but thumb-abduct axis is mirrored.
# Approximate mirror: left 179->70, left 31->70, left 30->70, left 41->41, left 151->61, left 250->250
GESTURES_RIGHT = [
    ("张开 Open",    [255, 70,  255, 255, 255, 255]),
    ("壹 One",       [0,   70,  255, 0,   0,   0]),
    ("贰 Two",       [0,   70,  255, 255, 0,   0]),
    ("叁 Three",     [0,   70,  255, 255, 255, 0]),
    ("肆 Four",      [0,   70,  255, 255, 255, 255]),
    ("伍 Five",      [250, 250, 250, 250, 250, 250]),
    ("OK",           [54,  41,  164, 250, 250, 250]),
    ("点赞 Thumb-up",[255, 70,  0,   0,   0,   0]),
    ("握拳 Fist",    [49,  61,  0,   0,   0,   0]),
    ("张开 Open",    [255, 70,  255, 255, 255, 255]),
]

def run(hand_type, can_channel, dwell):
    seq = GESTURES_LEFT if hand_type == "left" else GESTURES_RIGHT
    print(f"\n=== {hand_type} hand on {can_channel} — {len(seq)} gestures @ {dwell}s ===")
    api = LinkerHandApi(hand_type=hand_type, hand_joint="L6", can=can_channel)
    time.sleep(0.3)
    for i, (name, pose) in enumerate(seq, 1):
        print(f"  [{i:2d}/{len(seq)}] {name:<18} {pose}")
        api.finger_move(pose)
        time.sleep(dwell)
    print(f"Done with {hand_type}.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--hand", choices=["left", "right", "both"], default="both")
    p.add_argument("--dwell", type=float, default=1.2, help="seconds to hold each pose")
    args = p.parse_args()
    if args.hand in ("left", "both"):
        run("left", "can0", args.dwell)
    if args.hand in ("right", "both"):
        run("right", "can1", args.dwell)
