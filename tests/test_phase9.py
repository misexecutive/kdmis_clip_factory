"""
Tests for Phase 9: Unified CLI & Frontend API Integration
"""
import sys
import logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess
from web.app import get_categories, get_aura_profiles, get_hardware_info

def test_api_endpoints():
    # 1. Categories
    cats = get_categories()
    assert "categories" in cats
    assert len(cats["categories"]) == 16
    assert "Epic Explosions" in cats["categories"]
    assert "Cinematic Gameplay" in cats["categories"]
    print("PASS: /api/categories returned 16 content categories")

    # 2. AURA Profiles
    auras = get_aura_profiles()
    assert "profiles" in auras
    assert len(auras["profiles"]) == 7
    assert "CINEMATIC AURA" in auras["profiles"]
    assert "CHAOS AURA" in auras["profiles"]
    print("PASS: /api/aura_profiles returned 7 AURA profiles")

    # 3. Hardware Inspector
    hw = get_hardware_info()
    assert "cpu_count" in hw
    assert "recommended_encoder" in hw
    assert hw["recommended_encoder"] in ["h264_mf", "libx264", "h264_nvenc"]
    print(f"PASS: /api/hardware returned encoder '{hw['recommended_encoder']}' and {hw['cpu_count']} CPU cores")

def test_cli_subcommands():
    subcmds = ["analyze", "discover", "export", "metadata", "validate", "pipeline"]
    for sc in subcmds:
        res = subprocess.run([sys.executable, "main.py", sc, "--help"], capture_output=True, text=True)
        assert res.returncode == 0, f"CLI subcommand '{sc} --help' failed: {res.stderr}"
    print("PASS: All CLI subcommands (analyze, discover, export, metadata, validate, pipeline) --help verified successfully")

if __name__ == "__main__":
    test_api_endpoints()
    test_cli_subcommands()
    print("\n=======================================================")
    print("ALL PHASE 9 TESTS PASSED SUCCESSFULLY!")
    print("=======================================================")
