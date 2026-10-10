#!/usr/bin/env python3
"""Package an official Lean 4.35.0-rc4 Linux proof host without native compilers."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import shutil
import subprocess

PIN = "c29b6dda4f7c20e3eeaa717c4e565663c5cfa364"

def metrics(directory):
    files = [p for p in directory.rglob("*") if p.is_file() and not p.is_symlink()]
    return sum(p.stat().st_size for p in files), len(files)

def retain(filename, profile):
    return (filename.endswith(".olean")
            or (profile != "no-ir" and (filename.endswith(".ir") or filename.endswith(".ir.sig")))
            or filename.endswith(".olean.server")
            or (profile != "no-private" and filename.endswith(".olean.private")))

def copy(src, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["headless", "no-ir", "no-private"], default="headless")
    parser.add_argument("--no-archive", action="store_true")
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise RuntimeError("Only Linux x86_64 is supported")
    root = Path(subprocess.check_output(["elan", "which", "lean"], text=True).strip()).resolve().parent.parent
    version = subprocess.check_output([str(root / "bin/lean"), "--version"], text=True)
    if "4.35.0-rc4" not in version or PIN not in version:
        raise RuntimeError("Wrong official Lean version: " + version)

    out = args.output.absolute()
    if out.exists():
        raise FileExistsError("Refusing to overwrite existing package: " + str(out))
    out.mkdir(parents=True)
    copy(root / "bin/lean", out / "bin/lean")
    pscv0_exe = Path(".lake/build/bin/pscv0")
    if pscv0_exe.is_file():
        copy(pscv0_exe, out / "bin/pscv0")
        (out / "bin/pscv0").chmod(0o755)
    numbers = {"olean": 0, "ir": 0, "private": 0, "server": 0, "shared": 0, "plugin": 0}
    for p in (root / "lib/lean").rglob("*"):
        if not p.is_file():
            continue
        top = p.relative_to(root / "lib/lean").parts[0]
        if (top == "Lake" or top == "libLake_shared.so" or
                top.startswith(("Lake.", "LakeMain.", "LeanIR.", "LeanExport.", "LeanChecker.", "Leanc."))):
            continue
        if ".so" in p.name or retain(p.name, args.mode):
            copy(p, out / p.relative_to(root))
            key = ("shared" if ".so" in p.name else
                   "olean" if p.name.endswith(".olean") else
                   "private" if p.name.endswith(".olean.private") else
                   "server" if p.name.endswith(".olean.server") else "ir")
            numbers[key] += 1
    for p in (root / "lib").iterdir():
        if p.is_file() and ".so" in p.name and not p.name.lower().startswith(("libllvm", "libclang", "liblld")):
            copy(p, out / "lib" / p.name)
            numbers["shared"] += 1
    plugin_dir = Path(".lake/build/lib/lean")
    if not (plugin_dir / "LeanTs.olean").is_file():
        raise FileNotFoundError("Build the LeanTs Lake package before packaging")
    for p in plugin_dir.rglob("*"):
        if p.is_file() and retain(p.name, args.mode):
            copy(p, out / "lib/lean" / p.relative_to(plugin_dir))
            numbers["plugin"] += 1
    for license_name in ("LICENSE", "LICENSES"):
        if (root / license_name).is_file():
            copy(root / license_name, out / license_name)
    launcher = out / "bin/lean-ts-lean"
    launcher.write_text(
        '#!/bin/sh\nset -eu\n'
        'root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)\n'
        'export LEAN_SYSROOT="$root"\n'
        'export LEAN_PATH="$root/lib/lean"\n'
        'export LD_LIBRARY_PATH="$root/lib/lean:$root/lib"\n'
        'exec "$root/bin/lean" "$@"\n',
        encoding="utf-8")
    launcher.chmod(0o755)
    full_bytes, full_files = metrics(root)
    slim_bytes, slim_files = metrics(out)
    data = {"lean": "4.35.0-rc4", "commit": PIN, "profile": args.mode,
            "official_bytes": full_bytes, "official_files": full_files,
            "slim_bytes": slim_bytes, "slim_files": slim_files,
            "reduction_percent": round(100*(1-slim_bytes/full_bytes), 2),
            "selected": numbers}
    if not args.no_archive:
        archive = out.parent / (out.name + ".tar.zst")
        tar = subprocess.Popen(["tar", "-cf", "-", "-C", str(out.parent), out.name], stdout=subprocess.PIPE)
        try:
            subprocess.run(["zstd", "-T2", "-9", "-q", "-o", str(archive)], stdin=tar.stdout, check=True)
        finally:
            tar.stdout.close()
        if tar.wait() != 0:
            raise RuntimeError("tar archiving failed")
        with archive.open("rb") as file:
            data["sha256"] = hashlib.file_digest(file, "sha256").hexdigest()
        data["archive_bytes"] = archive.stat().st_size
        data["compression"] = "tar.zst zstd -9"
    (out.parent / (out.name + "-sizes.json")).write_text(json.dumps(data, indent=2) + "\n")
    print("SLIM_METRICS", json.dumps(data), flush=True)

if __name__ == "__main__":
    main()
