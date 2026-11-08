"""GPS association for extracted frames.

 Associates GPS coordinates with frames using timestamps from P1
 FlightMetadata and other supported telemetry sources.

 No GPS coordinates are fabricated. When telemetry is missing or a frame falls
 outside the configurable gap policy, the frame’s GPS fields remain null and the
 association method/source is recorded.
"""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from backend.app.models.flight_metadata import FlightMetadata
from backend.app.core.database import SessionLocal


@dataclass
class GPSRecord:
    latitude: Optional[float]
    longitude: Optional[float]
    altitude: Optional[float]
    altitude_datum: Optional[str]
    timestamp_seconds: Optional[float]
    timestamp_str: Optional[str]
    gps_quality: Optional[str]
    source: str
    horizontal_accuracy: Optional[float] = None
    vertical_accuracy: Optional[float] = None


@dataclass
class GPSAssociationConfig:
    # Maximum allowed gap (seconds) between a frame timestamp and the nearest
    # telemetry record for an association to be considered valid.
    max_gap_seconds: float = 1.0
    # If True, interpolate between two telemetry records across small gaps.
    # Interpolation is only applied when both endpoints are present and the gap
    # is within the configured limit; the result is explicitly marked as
    # interpolated.
    allow_interpolation: bool = False
    interpolation_max_gap_seconds: float = 2.0
    default_altitude_datum: Optional[str] = "ellipsoidal"


def _parse_timestamp_to_seconds(ts: Any) -> Optional[float]:
    """Best-effort parse of ISO-ish/GPS timestamps to epoch seconds."""
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return float(ts)
    s = str(ts).strip()
    if not s:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            continue
    return None


def flight_metadata_to_gps_records(
    records: Iterable[FlightMetadata],
) -> List[GPSRecord]:
    """Convert P1 FlightMetadata rows into GPSRecord list for association.

    FlightMetadata can represent mission-level or video-level metadata; where a
    GPS timestamp is not available we use a placeholder only if there is another
    usable timestamp; otherwise the record is skipped.
    """
    out: List[GPSRecord] = []
    for fm in records:
        ts = _parse_timestamp_to_seconds(fm.start_timestamp)
        if ts is None:
            continue
        if fm.latitude is None or fm.longitude is None:
            continue
        out.append(
            GPSRecord(
                latitude=float(fm.latitude),
                longitude=float(fm.longitude),
                altitude=float(fm.altitude) if fm.altitude is not None else None,
                altitude_datum=fm.altitude_datum or None,
                timestamp_seconds=ts,
                timestamp_str=fm.start_timestamp,
                gps_quality=None,
                source=fm.metadata_source or "flight_metadata",
                horizontal_accuracy=fm.horizontal_accuracy,
                vertical_accuracy=fm.vertical_accuracy,
            )
        )
    return sorted(out, key=lambda r: r.timestamp_seconds or 0.0)


def parse_csv_telemetry(
    csv_path: str,
    *,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    alt_col: Optional[str] = "altitude",
    time_col: str = "timestamp",
    quality_col: Optional[str] = None,
) -> List[GPSRecord]:
    """Parse a timestamped CSV telemetry file into GPSRecord list."""
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Telemetry CSV not found: {csv_path}")

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows: List[Dict[str, str]] = list(reader)

    records: List[GPSRecord] = []
    for row in rows:
        lat = _float(row.get(lat_col))
        lon = _float(row.get(lon_col))
        if lat is None or lon is None:
            continue
        ts = _parse_timestamp_to_seconds(row.get(time_col))
        if ts is None:
            continue
        alt = _float(row.get(alt_col)) if alt_col else None
        q = row.get(quality_col) if quality_col else None
        records.append(
            GPSRecord(
                latitude=lat,
                longitude=lon,
                altitude=alt,
                altitude_datum=None,
                timestamp_seconds=ts,
                timestamp_str=row.get(time_col),
                gps_quality=q,
                source="csv_telemetry",
                horizontal_accuracy=None,
                vertical_accuracy=None,
            )
        )

    return sorted(records, key=lambda r: r.timestamp_seconds or 0.0)


def _float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def associate_gps_for_frames(
    frames: List[Dict[str, Any]],
    telemetry_records: List[GPSRecord],
    *,
    config: Optional[GPSAssociationConfig] = None,
) -> List[Dict[str, Any]]:
    """Associate GPS with frames by timestamp.

    Returns frame dicts with gps fields populated where association succeeded.
    Frames that cannot be associated are left untouched (gps fields null) and a
    gps_source of "none" is set where appropriate.
    """
    cfg = config or GPSAssociationConfig()
    if not telemetry_records:
        for f in frames:
            f = dict(f)
            f["gps_source"] = "none"
        return frames

    sorted_telemetry = sorted(telemetry_records, key=lambda r: r.timestamp_seconds or 0.0)
    result: List[Dict[str, Any]] = []

    for frame in frames:
        frame = dict(frame)
        t = frame.get("timestamp_seconds")
        if t is None:
            frame["gps_source"] = "none"
            result.append(frame)
            continue

        nearest = _nearest_telemetry(sorted_telemetry, t, cfg)
        if nearest is None:
            frame["gps_source"] = "none"
            result.append(frame)
            continue

        gap = abs((nearest.timestamp_seconds or 0.0) - t)
        if gap > cfg.max_gap_seconds:
            frame["gps_source"] = "none"
            frame["gps_association_gap_seconds"] = gap
            result.append(frame)
            continue

        # If interpolation is enabled and we have two endpoints bracketing the
        # frame within the interpolation gap, interpolate.
        if cfg.allow_interpolation and gap > 0:
            interp = _interpolate_telemetry(sorted_telemetry, t, cfg.interpolation_max_gap_seconds)
            if interp is not None:
                frame = _write_gps(frame, interp, source="interpolated_telemetry", gap=gap)
                result.append(frame)
                continue

        frame = _write_gps(frame, nearest, source="flight_metadata", gap=gap)
        result.append(frame)

    return result


def _nearest_telemetry(
    telemetry: List[GPSRecord],
    t: float,
    cfg: GPSAssociationConfig,
) -> Optional[GPSRecord]:
    best: Optional[GPSRecord] = None
    best_gap: Optional[float] = None
    for rec in telemetry:
        if rec.timestamp_seconds is None:
            continue
        gap = abs(rec.timestamp_seconds - t)
        if best_gap is None or gap < best_gap:
            best = rec
            best_gap = gap
            if best_gap <= 0:
                break
    return best


def _interpolate_telemetry(
    telemetry: List[GPSRecord],
    t: float,
    max_gap: float,
) -> Optional[GPSRecord]:
    before: Optional[GPSRecord] = None
    after: Optional[GPSRecord] = None
    for rec in telemetry:
        if rec.timestamp_seconds is None:
            continue
        if rec.timestamp_seconds <= t:
            before = rec
        if rec.timestamp_seconds >= t and after is None:
            after = rec
            break
    if before is None or after is None:
        return None
    gap_before = (t - (before.timestamp_seconds or 0.0))
    gap_after = ((after.timestamp_seconds or 0.0) - t)
    if gap_before > max_gap or gap_after > max_gap:
        return None
    total = (after.timestamp_seconds or 0.0) - (before.timestamp_seconds or 0.0)
    if total <= 0:
        return None
    ratio = gap_before / total

    def lerp(a, b):
        if a is None or b is None:
            return None
        return float(a + (b - a) * ratio)

    return GPSRecord(
        latitude=lerp(before.latitude, after.latitude),
        longitude=lerp(before.longitude, after.longitude),
        altitude=lerp(before.altitude, after.altitude),
        altitude_datum=before.altitude_datum or after.altitude_datum,
        timestamp_seconds=t,
        timestamp_str=None,
        gps_quality=None,
        source="interpolated_telemetry",
        horizontal_accuracy=None,
        vertical_accuracy=None,
    )


def _write_gps(
    frame: Dict[str, Any],
    rec: GPSRecord,
    *,
    source: str,
    gap: float,
) -> Dict[str, Any]:
    frame["gps_latitude"] = rec.latitude
    frame["gps_longitude"] = rec.longitude
    frame["altitude"] = rec.altitude
    if rec.altitude_datum:
        frame["altitude_datum"] = rec.altitude_datum
    elif frame.get("altitude_datum") is None:
        frame["altitude_datum"] = "ellipsoidal"
    frame["gps_timestamp_seconds"] = rec.timestamp_seconds
    frame["gps_timestamp_str"] = rec.timestamp_str
    frame["gps_quality"] = rec.gps_quality
    frame["gps_source"] = source
    frame["gps_association_gap_seconds"] = gap
    return frame
