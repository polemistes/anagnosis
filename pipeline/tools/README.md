# Tools

* `pre-push`: the public repository's pre-push hook, which refuses a push that carries a file of a
  private text (Murray's Euripides, see pipeline/PLAN-euripides.md) or anything under `private/`.
  Install it with `cp pipeline/tools/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push`.
* `emulator-check/`: helper scripts for the emulator check of a newly built text (its README).
