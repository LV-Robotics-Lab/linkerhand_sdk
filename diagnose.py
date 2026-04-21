#!/usr/bin/env python3
"""Diagnose why the right hand's index finger (joint index 2) won't move.

Plan:
  1. Connect to both hands.
  2. Dump state/current/torque/temp/fault for both.
  3. Command OPEN, wait, read state — expect state[2] ~ 255.
  4. Command FIST, wait, read state — expect state[2] ~ 0.
  5. Command ISOLATED index move (only joint 2 changes) — confirm only index reacts.
  6. Compare left vs right: if left[2] changes but right[2] stays fixed, the issue is
     hardware/firmware on the right index motor, not the CAN command path.
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "LinkerHand"))
from linker_hand_api import LinkerHandApi

JOINT = ["Thumb flex","Thumb abduct","Index","Middle","Ring","Pinky"]

OPEN = {"left":[255,179,255,255,255,255], "right":[255,70,255,255,255,255]}
FIST = {"left":[67,151,0,0,0,0],          "right":[49,61,0,0,0,0]}

def dump(label, api):
    print(f"\n--- {label} ---")
    for name, fn in [
        ("state",       api.get_state),
        ("current",     api.get_current),
        ("torque",      api.get_torque),
        ("temperature", api.get_temperature),
        ("fault",       api.get_fault),
        ("speed",       api.get_speed),
    ]:
        try:
            val = fn()
            print(f"  {name:11s}: {val}")
        except Exception as e:
            print(f"  {name:11s}: <error {e}>")

def move_and_read(api, pose, label, side):
    print(f"\n>>> {label}: sending {pose}")
    api.finger_move(pose)
    time.sleep(1.2)
    try:
        s = api.get_state()
        print(f"    state after {label}: {s}")
        return s
    except Exception as e:
        print(f"    state read failed: {e}")
        return None

def main():
    print("=== Connecting ===")
    L = LinkerHandApi(hand_type="left",  hand_joint="L6", can="can0")
    R = LinkerHandApi(hand_type="right", hand_joint="L6", can="can1")
    time.sleep(0.3)

    # Initial snapshot
    dump("LEFT  initial",  L)
    dump("RIGHT initial",  R)

    # OPEN both
    sL_open = move_and_read(L, OPEN["left"],  "OPEN",  "left")
    sR_open = move_and_read(R, OPEN["right"], "OPEN",  "right")

    # FIST both
    sL_fist = move_and_read(L, FIST["left"],  "FIST",  "left")
    sR_fist = move_and_read(R, FIST["right"], "FIST",  "right")

    # Isolated index move: keep thumb in OPEN thumb-abduct, wiggle only index
    iso_open_L = list(OPEN["left"]);  iso_open_L[2] = 255
    iso_fist_L = list(OPEN["left"]);  iso_fist_L[2] = 0
    iso_open_R = list(OPEN["right"]); iso_open_R[2] = 255
    iso_fist_R = list(OPEN["right"]); iso_fist_R[2] = 0

    print("\n=== Isolated index-finger wiggle ===")
    move_and_read(L, iso_open_L, "LEFT  index=255", "left")
    sL_idx0 = move_and_read(L, iso_fist_L, "LEFT  index=0",   "left")
    move_and_read(R, iso_open_R, "RIGHT index=255", "right")
    sR_idx0 = move_and_read(R, iso_fist_R, "RIGHT index=0",   "right")

    # Fault/current/temp after movement
    dump("LEFT  after",  L)
    dump("RIGHT after",  R)

    # Summary table: show how state[2] (index) changed
    def safe(s, i):
        try: return s[i]
        except: return "?"
    print("\n=== Index-joint (i=2) tracking ===")
    print(f"{'state':25s} {'LEFT[2]':>10s} {'RIGHT[2]':>10s}")
    print(f"{'after OPEN':25s} {safe(sL_open,2):>10} {safe(sR_open,2):>10}")
    print(f"{'after FIST':25s} {safe(sL_fist,2):>10} {safe(sR_fist,2):>10}")
    print(f"{'after isolated index=0':25s} {safe(sL_idx0,2):>10} {safe(sR_idx0,2):>10}")

    # Return to safe rest
    L.finger_move(OPEN["left"])
    R.finger_move(OPEN["right"])

if __name__ == "__main__":
    main()
