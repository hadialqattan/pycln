---
name: Bug report
about: Report a bug
title: "[BUG]"
labels: [bug]
assignees: ""
---

**Describe the bug** A clear and concise description of what the bug is.

**To Reproduce** Steps to reproduce the behavior:

1. Take this code snippet:

   ```python
   import foo

   print(foo)
   ```

2. Run this Pycln command:
   ```bash
   $ pycln example.py --diff --all  # exmaple.
   ```
3. Error traceback or unexpected output (if present):
   ```bash
   {paste it here}
   ```
4. Unexpected fixed code (if present):
   > `import foo` has removed!
   ```python
   print(foo)
   ```

**Expected behavior**:

1.  Description: A clear and concise description of what you expected to happen.
2.  Expected output (if present):
    ```bash
    {paste it here}
    ```
3.  Expected fixed code (if present):

    > nothing would change.

    ```python
    import foo

    print(foo)
    ```

**Environment (please complete the following informations):**

- Python Version: [e.g. Python 3.8]
- Pycln Version: [e.g. v0.0.1]
- OS Type: [e.g. Linux]

**Additional context** Add any other context about the problem here.
