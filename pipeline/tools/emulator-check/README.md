# Emulator check of a newly built text

Helper scripts written during the emulator checks of the Sophocles plays (2026-11-15/16). The
method and the commands are in `pipeline/PLAN-sophocles.md` ("Trachiniae emulator check and
what it led to") and `pipeline/PLAN-drama.md` ("Housekeeping": memory rules).

* `patch_aab.py`: adds the sale mark for the texts under check to a **scratch copy** of the
  debug bundle's catalogue, because the shop offers only texts marked for sale. The repository
  and the real bundle are not touched.
* `ui.py`, `ui_lib.py`, `goto.py`: taps, swipes and screenshots through adb.

Work in a folder under `pipeline/build/agent-scratch/` (on disk, ignored by git), not in the
session scratchpad: on this machine `/tmp` is a RAM disk, so what is written there counts
against memory and is gone after a restart.
