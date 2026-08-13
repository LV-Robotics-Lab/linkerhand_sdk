# Upstream synchronization

This repository follows
[`linker-bot/linkerhand-python-sdk`](https://github.com/linker-bot/linkerhand-python-sdk)
while retaining LV Robotics Lab's dual-L6 integration.

## Current baseline

- SDK release: `3.1.1`
- Upstream commit: `0cc0585b97214b2cc4a9a5afcc84aee9f414e0e8`
- Synchronized: 2026-08-13
- Frozen upstream English README: `doc/UPSTREAM_README_3.1.1.md`

The upstream `LinkerHand/`, `example/`, `doc/`, `resource/`, discovery scripts,
requirements, and release notes are carried forward. The repository keeps its
own top-level `README.md` because it documents the lab's actual dual-hand setup.

## Lab-maintained additions

- `linker_hand_l6.py`
- `dual_gui.py`
- `diagnose.py`
- `gestures.py`
- `test_hand.py`
- the dual-L6 `LinkerHand/config/setting.yaml` hardware profile

When updating again, overlay upstream source without deleting these additions.
Review `setting.yaml` manually: upstream defaults describe a single example
hand, while this repository intentionally keeps left L6 on `can0` and right L6
on `can1`.
