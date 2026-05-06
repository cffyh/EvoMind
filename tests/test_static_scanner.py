import os
import tempfile

from epm.autoresearch.static_scanner import scan_for_leakage


def test_detects_negative_shift():
    with tempfile.TemporaryDirectory() as td:
        bad = os.path.join(td, "bad.py")
        with open(bad, "w") as f:
            f.write("import pandas as pd\nx = df.shift(-1)\n")
        findings = scan_for_leakage([td], allowlist_files=())
        assert any(f.pattern == "negative-shift" for f in findings)


def test_clean_file_no_findings():
    with tempfile.TemporaryDirectory() as td:
        good = os.path.join(td, "good.py")
        with open(good, "w") as f:
            f.write("import pandas as pd\nx = df.shift(7).rolling(10).mean()\n")
        findings = scan_for_leakage([td], allowlist_files=())
        assert findings == []


def test_allowlist_skips_path():
    with tempfile.TemporaryDirectory() as td:
        sub = os.path.join(td, "src_legacy")
        os.makedirs(sub)
        bad = os.path.join(sub, "bad.py")
        with open(bad, "w") as f:
            f.write("x = df.shift(-1)\n")
        findings = scan_for_leakage([td])  # default allowlist includes src_legacy
        assert findings == []
