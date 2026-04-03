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
    """
    Fallback: store only ECC bytes (not data) in the .par2 file.

    File format: 1 header byte (nsym) followed by nsym ECC bytes per block.
    Block size is (255 - nsym) data bytes → 255-byte RS codeword.
    """
    import reedsolo

    data = image_path.read_bytes()
    nsym = max(1, min(127, int(255 * redundancy_pct / 100)))
    rsc = reedsolo.RSCodec(nsym)
    block_size = 255 - nsym

    ecc = bytearray()
    for i in range(0, len(data), block_size):
        chunk = data[i:i + block_size]
        encoded_block = bytes(rsc.encode(chunk))
        ecc.extend(encoded_block[len(chunk):])  # append only ECC tail

    par2_path = image_path.with_suffix(image_path.suffix + ".par2")
    par2_path.write_bytes(bytes([nsym]) + bytes(ecc))
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
    raw = par2_path.read_bytes()
    nsym, stored_ecc = raw[0], raw[1:]

    rsc = reedsolo.RSCodec(nsym)
    block_size = 255 - nsym

    computed = bytearray()
    for i in range(0, len(data), block_size):
        chunk = data[i:i + block_size]
        encoded_block = bytes(rsc.encode(chunk))
        computed.extend(encoded_block[len(chunk):])

    return bytes(computed) == stored_ecc


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

    corrupted = bytearray(image_path.read_bytes())
    raw = par2_path.read_bytes()
    nsym, stored_ecc = raw[0], raw[1:]

    rsc = reedsolo.RSCodec(nsym)
    block_size = 255 - nsym

    repaired = bytearray()
    ecc_offset = 0
    for i in range(0, len(corrupted), block_size):
        chunk = corrupted[i:i + block_size]
        ecc_block = stored_ecc[ecc_offset:ecc_offset + nsym]
        ecc_offset += nsym
        codeword = bytes(chunk) + bytes(ecc_block)  # reassemble for decode
        try:
            decoded, _, _ = rsc.decode(codeword)
            repaired.extend(decoded)
        except reedsolo.ReedSolomonError:
            return False

    image_path.write_bytes(bytes(repaired))
    return True
