# linkerhand_sdk

Local working copy of the [Linker Hand Python SDK](https://github.com/linker-bot/linkerhand-python-sdk)
configured for a **dual Linker Hand L6** setup (one left + one right) controlled
over two PEAK PCAN-USB adapters.

The upstream SDK source is synchronized to **3.1.1** at commit
[`0cc0585`](https://github.com/linker-bot/linkerhand-python-sdk/commit/0cc0585b97214b2cc4a9a5afcc84aee9f414e0e8).
The lab-specific dual-hand wrapper, diagnostics, gestures, GUI, tests, and the
dual-L6 hardware configuration remain maintained in this repository. See
[`UPSTREAM.md`](UPSTREAM.md) for the synchronization boundary.

Adds a high-level wrapper (`linker_hand_l6.py`), a dual-hand GUI (`dual_gui.py`),
and a few utility scripts on top of the upstream SDK. The original SDK source
lives in `LinkerHand/` and the upstream examples in `example/`.

---

## Hardware

| Side  | SocketCAN | Serial | Firmware |
|-------|-----------|--------|----------|
| Left  | `can0`    | `LHL6-03-253-L-B-1-C` | 2.3.7 |
| Right | `can1`    | `LHL6-03-240-R-B-1-C` | 2.3.7 |

- 2× PEAK PCAN-USB adapters (`lsusb: 0c72:000c`)
- XT30 (2+2) connector per hand: `VCC / GND / CAN_H / CAN_L`
- CAN bitrate: **1 Mbps**
- Power: DC 24V ±10% via the supplied AC adapter

## System requirements

- Ubuntu 22.04+
- `can-utils`, `ethtool` (apt)
- Anaconda / Miniconda for env management
- `uv` for fast package installs inside the conda env

## One-time setup

```bash
# System packages
sudo apt install -y can-utils ethtool

# Conda env (Python 3.10)
conda create -n linkerhand python=3.10 -y
conda activate linkerhand

# SDK dependencies (uv is significantly faster than pip)
uv pip install -r requirements.txt
```

## Bring up CAN

```bash
sudo ip link set can0 up type can bitrate 1000000
sudo ip link set can1 up type can bitrate 1000000
ip -br link show type can   # both should show UP
```

The SDK can also auto-open CAN if you set your sudo password in
`LinkerHand/config/setting.yaml` under the `PASSWORD:` field — handled for you
in this workspace already.

## Identify which hand is on which port

```bash
./find_linker_hand.sh
```

Sends `0FF#C0` to each CAN interface and reads back the factory serial + a
response ID (`0x28` = left, `0x27` = right).

---

## High-level wrapper — `linker_hand_l6.py`

Clean API over the SDK for single-hand and bimanual control. Joint values are
integers 0..255 in the order
`[thumb_flex, thumb_abduct, index, middle, ring, pinky]`.

### Single hand

```python
from linker_hand_l6 import LinkerHandL6

with LinkerHandL6.left() as h:        # .right() for the right hand
    h.open()
    h.fist()
    h.thumb_up()
    h.set_pose([255, 179, 255, 255, 255, 255])
    h.set_finger(LinkerHandL6.INDEX, 0)   # move only the index finger
    print(h.get_state())                  # [thumb, abduct, index, ...]
```

### Bimanual

```python
from linker_hand_l6 import BimanualL6, PRESETS

with BimanualL6.auto() as bi:           # left=can0, right=can1
    bi.open()                           # both hands open
    bi.fist()                           # both hands fist
    bi.preset("thumb_up")               # named gesture, anatomically mirrored
    bi.set(left=PRESETS["fist"]["left"],
           right=PRESETS["open"]["right"])   # independent poses
    print(bi.get_state())               # {'left': [...], 'right': [...]}
```

### Why `preset()` vs `mirror()`

`preset("open")` uses **side-specific** values because the two hands are
mirror-image mechanisms with different neutral angles on the thumb-abduct
joint (~179 on left, ~70 on right). `mirror(pose)` sends **identical raw
values** to both hands, which will look asymmetric.

### Available presets

`open`, `fist`, `thumb_up`, `ok`, `point`, `two`, `three`, `four`, `five`.

---

## Dual-hand GUI — `dual_gui.py`

Side-by-side sliders and gesture buttons for both hands at once, with a
"Sync both hands" checkbox to mirror movement between panels. The upstream
`example/gui_control/gui_control.py` hard-codes a single hand; this replaces
it for bimanual work.

```bash
QT_QPA_PLATFORM=wayland python dual_gui.py
```

(Use `QT_QPA_PLATFORM=xcb` on X11.)

---

## Utility scripts

| Script | What it does |
|---|---|
| `test_hand.py` | Quick open → half → open cycle on either/both hands. `--hand left\|right\|both` |
| `gestures.py` | Runs the 9-gesture sequence (open, 1, 2, 3, 4, 5, OK, thumbs-up, fist) |
| `diagnose.py` | Reads state/current/torque/temp/fault and wiggles each hand to verify the servos actually track commanded positions — used to triage a stuck finger |

`test_hand.py` and `gestures.py` take `--hand left|right|both`.

---

## Known issues on this pair

- **Right hand index finger stuck at state ≈ 180.** The motor draws elevated
  current (~80 vs <25 on the others) when commanded but the finger doesn't
  track. Likely mechanical obstruction inside the joint; see `diagnose.py`
  output for the signature. Contact `support@linkerbot.cn` with the serial
  if it doesn't free up on inspection.

---

## References

- Upstream SDK: <https://github.com/linker-bot/linkerhand-python-sdk>
- Upstream snapshot: `3.1.1` / `0cc0585b97214b2cc4a9a5afcc84aee9f414e0e8`
- API reference: `doc/API-Reference.md`
- Original SDK docs: `README_CN.md` (Chinese), `doc/`
- Support: support@linkerbot.cn
