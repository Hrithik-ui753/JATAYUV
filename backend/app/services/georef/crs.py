from __future__ import annotations

from typing import Optional
from pyproj import CRS, Transformer


def ensure_pyproj():
    try:
        from pyproj import CRS, Transformer
        return CRS, Transformer
    except ImportError:
        raise RuntimeError("pyproj is required for P5 georeferencing")


def wgs84_crs() -> CRS:
    CRS, _ = ensure_pyproj()
    return CRS.from_epsg(4326)


def utm_zone_from_lat_lon(lat: float, lon: float) -> Optional[str]:
    CRS, _ = ensure_pyproj()
    try:
        zone = int((lon + 180) / 6) + 1
        hemisphere = "N" if lat >= 0 else "S"
        epsg = 32600 + zone if hemisphere == "N" else 32700 + zone
        return CRS.from_epsg(epsg).to_string()
    except Exception:
        return None


def create_transformer(source: str, target: str, always_xy: bool = True) -> Transformer:
    CRS, Transformer = ensure_pyproj()
    return Transformer.from_crs(CRS.from_string(source), CRS.from_string(target), always_xy=always_xy)


def transform_point(transformer: Transformer, x: float, y: float, z: Optional[float] = None):
    if z is not None:
        return transformer.transform(x, y, z)
    return transformer.transform(x, y)
