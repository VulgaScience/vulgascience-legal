import argparse
import json
from pathlib import Path


RISKY_PATTERNS = ["\\u00", "\\u201", "Ã", "�"]


def check_script(path):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    warnings = []
    segments = data.get("segments", [])

    previous_end = 0.0
    for index, segment in enumerate(segments):
        start = float(segment.get("start", 0))
        end = float(segment.get("end", 0))
        text = str(segment.get("text", ""))
        if start < previous_end - 0.05:
            warnings.append(f"segment {index} overlaps previous segment")
        if end <= start:
            warnings.append(f"segment {index} has invalid timing")
        if len(text) > 92:
            warnings.append(f"segment {index} subtitle text may be too long")
        for pattern in RISKY_PATTERNS:
            if pattern in text:
                warnings.append(f"segment {index} contains risky encoding pattern {pattern}")
        previous_end = max(previous_end, end)

    duration = segments[-1]["end"] if segments else 0
    targets = data.get("quality_targets", {})
    min_duration = float(targets.get("min_duration_seconds", 0))
    max_duration = float(targets.get("max_duration_seconds", 9999))
    if duration < min_duration:
        warnings.append(f"duration {duration:.2f}s is below target minimum {min_duration:.2f}s")
    if duration > max_duration:
        warnings.append(f"duration {duration:.2f}s is above target maximum {max_duration:.2f}s")

    return {
        "path": str(path),
        "ok": not warnings,
        "id": data.get("id"),
        "duration_seconds": round(duration, 2),
        "segment_count": len(segments),
        "warnings": warnings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate structured VulgaScience video scripts.")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    reports = [check_script(path) for path in args.paths]
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    if any(not report["ok"] for report in reports):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
