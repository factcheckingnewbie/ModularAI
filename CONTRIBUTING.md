## Repo-first patch rule

All code patches—whether human-written or AI-generated—**must**:

1. Be generated against the **current** `HEAD` of the target file.
2. Include at least three lines of unchanged context before and after each hunk.
3. Apply cleanly with `git apply --check`.
4. Fail CI or local checks if any hunk cannot be applied to `HEAD`.

Please do **not** edit from memory or stale copies.  

