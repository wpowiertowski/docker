import shutil
import subprocess
from pathlib import Path


def _par2_available() -> bool:
    return shutil.which("par2") is not None


def generate_par2(image_path: Path, redundancy_pct: int = 10) -> Path:
    """
    Generate a .par2 redundancy file for the given image.
    Returns path to the generated .par2 file.

    Uses the `par2` CLI tool if available, otherwise falls back to a
    pure-Python Reed-Solomon implementation via `reedsolo`.
    """
    if _par2_available():
        return _generate_par2_cli(image_path, redundancy_pct)
    return _generate_par2_python(image_path, redundancy_pct)


def _generate_par2_cli(image_path: Path, redundancy_pct: int) -> Path:
    par2_base = image_path.with_suffix(image_path.suffix + ".par2")
    cmd = [
        "par2", "create",
        f"-r{redundancy_pct}",
        "-n1",          # single par2 file
        "-q",           # quiet
        str(par2_base),
        str(image_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    # par2 names the file <base>.par2
    return par2_base


def _generate_par2_python(image_path: Path, redundancy_pct: int) -> Path:
    """Fallback: encode the file with reedsolo and write a simple recovery blob."""
    import reedsolo

    data = image_path.read_bytes()
    # nsym is number of ECC bytes per 255-byte block
    # redundancy_pct applies to the whole file via proportional nsym
    nsym = max(1, min(127, int(255 * redundancy_pct / 100)))
    rsc = reedsolo.RSCodec(nsym)
    encoded = bytes(rsc.encode(data))
    par2_path = image_path.with_suffix(image_path.suffix + ".par2")
    par2_path.write_bytes(encoded)
    return par2_path


def verify_with_par2(image_path: Path, par2_path: Path) -> bool:
    """Check if image is intact against its par2 file."""
    if _par2_available():
        result = subprocess.run(
            ["par2", "verify", "-q", str(par2_path), str(image_path)],
            capture_output=True,
        )
        return result.returncode == 0
    return _verify_python(image_path, par2_path)


def _verify_python(image_path: Path, par2_path: Path) -> bool:
    import reedsolo

    data = image_path.read_bytes()
    encoded = par2_path.read_bytes()
    nsym = len(encoded) - len(data)
    if nsym <= 0:
        return False
    # nsym stored per block; approximate from total difference
    block_nsym = max(1, nsym * 255 // max(1, len(encoded)))
    rsc = reedsolo.RSCodec(block_nsym)
    try:
        decoded, _, _ = rsc.decode(encoded)
        return bytes(decoded) == data
    except reedsolo.ReedSolomonError:
        return False


def repair_with_par2(image_path: Path, par2_path: Path) -> bool:
    """Attempt to repair a corrupted image using its par2 file."""
    if _par2_available():
        result = subprocess.run(
            ["par2", "repair", "-q", str(par2_path), str(image_path)],
            capture_output=True,
        )
        return result.returncode == 0
    return _repair_python(image_path, par2_path)


def _repair_python(image_path: Path, par2_path: Path) -> bool:
    import reedsolo

    encoded = par2_path.read_bytes()
    original_size = image_path.stat().st_size
    block_nsym = max(1, (len(encoded) - original_size) * 255 // max(1, len(encoded)))
    rsc = reedsolo.RSCodec(block_nsym)
    try:
        decoded, _, _ = rsc.decode(encoded)
        image_path.write_bytes(bytes(decoded))
        return True
    except reedsolo.ReedSolomonError:
        return False
