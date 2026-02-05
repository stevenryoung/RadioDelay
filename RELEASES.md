# 0.3.0
- Drop Python 2 support; require active version (3.10+)
- Add command-line arguments to optionally list & select audio device
- Increase default chunk size from 2048 to 4096 (more robust on slower devices)
- Eliminate write-buffer underflow handler; ignore exceptions instead
- Repackage project definition from `setup.py` to `pyproject.toml`
- Create command-line script alias
- Add annotations

# 0.2.1
- Package info changes. No functional change.

# 0.2.0
- Updated for Python 3 compatibility
- Removed gflags dependency and replaced with argparse
- Other minor changes

# 0.1.0
- Packaged and uploaded to PyPI
- Other minor changes

# 0.0.1
- First formal release
- Adds command line arguments for various parameters using gflags
- Made source PEP-8 compliant
- Added logging support
