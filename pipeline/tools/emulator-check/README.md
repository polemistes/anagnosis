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

## Keeping the desktop responsive (2026-11-16)

The machine is the author's working laptop (8 cores / 16 threads, graphics on the same chip).
A Gradle build and the emulator at normal priority take every core and make the whole desktop
sluggish while they run. So:

* Gradle at low priority and on half the threads:
  `nice -n 19 ionice -c 3 ./gradlew --priority low --max-workers 8 :androidApp:bundleDebug`
* The emulator at low priority, and without its window unless a check needs to be watched
  (screenshots through adb work without it):
  `nice -n 19 emulator -avd anagnosis -no-window -no-snapshot-save -no-boot-anim -no-audio`
* As before: at least 8 GB "available" before either, never both at once, `./gradlew --stop`
  after a build, the emulator closed when the check is done.
