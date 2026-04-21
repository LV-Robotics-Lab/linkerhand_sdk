#!/usr/bin/env python3
import sys, os, time, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "LinkerHand"))
from linker_hand_api import LinkerHandApi

OPEN = {
    "left":  [255, 179, 255, 255, 255, 255],
    "right": [255,  70, 255, 255, 255, 255],
}
HALF = {
    "left":  [150, 150, 128, 128, 128, 128],
    "right": [150, 110, 128, 128, 128, 128],
}
FIST = {
    "left":  [67, 151, 0, 0, 0, 0],
    "right": [49,  61, 0, 0, 0, 0],
}

def run(hand_type, can_channel, dwell=1.5):
    print(f"\n=== Connecting to {hand_type} hand on {can_channel} ===")
    api = LinkerHandApi(hand_type=hand_type, hand_joint="L6", can=can_channel)
    time.sleep(0.3)

    print(f"Step 1/3: OPEN   -> {OPEN[hand_type]}")
    api.finger_move(OPEN[hand_type])
    time.sleep(dwell)

    print(f"Step 2/3: HALF   -> {HALF[hand_type]}")
    api.finger_move(HALF[hand_type])
    time.sleep(dwell)

    print(f"Step 3/3: OPEN   -> {OPEN[hand_type]}")
    api.finger_move(OPEN[hand_type])
    time.sleep(dwell)

    print(f"Done with {hand_type}.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--hand", choices=["left", "right", "both"], default="left")
    args = p.parse_args()

    if args.hand in ("left", "both"):
        run("left", "can0")
    if args.hand in ("right", "both"):
        run("right", "can1")
