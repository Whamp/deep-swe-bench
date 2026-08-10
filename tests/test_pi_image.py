import re
from pathlib import Path

from harness.lib import PI_IMAGE_REV

REPO = Path(__file__).resolve().parents[1]


def test_pi_image_revision_tracks_pinned_pi_version():
    dockerfile = (REPO / "harness" / "Dockerfile.pi-agent").read_text()
    match = re.search(r"^ARG PI_VERSION=(\S+)$", dockerfile, re.MULTILINE)

    assert match is not None
    version = match.group(1)
    assert version == "0.84.1"
    assert f"pi{version.replace('.', '')}" in PI_IMAGE_REV
