import os
import json
import cv2
import numpy as np
from PIL import Image as PILImage
from PIL.ExifTags import TAGS, GPSTAGS
from typing import Dict, Any, Tuple, Optional

class ImagePreprocessor:
    @staticmethod
    def extract_exif_telemetry(image_path: str) -> Dict[str, Any]:
        """Extract EXIF, GPS and basic camera telemetry.
        Returns a dict with safe defaults when data is missing.
        """
        telemetry: Dict[str, Any] = {
            "camera_make": "Unknown",
            "camera_model": "Unknown",
            "focal_length_mm": None,
            "iso": None,
            "exposure_time": None,
            "altitude_m": None,
            "latitude": None,
            "longitude": None,
            "heading_deg": None,
            "capture_time": None,
        }
        try:
            with PILImage.open(image_path) as img:
                exif_raw = img._getexif()
                if not exif_raw:
                    return telemetry
                exif: Dict[str, Any] = {TAGS.get(k, k): v for k, v in exif_raw.items()}
                # Camera make/model
                if "Make" in exif:
                    telemetry["camera_make"] = str(exif["Make"]).strip()
                if "Model" in exif:
                    telemetry["camera_model"] = str(exif["Model"]).strip()
                # Focal length, ISO, exposure
                if "FocalLength" in exif:
                    try:
                        telemetry["focal_length_mm"] = float(exif["FocalLength"])
                    except Exception:
                        pass
                if "ISOSpeedRatings" in exif:
                    try:
                        telemetry["iso"] = int(exif["ISOSpeedRatings"])
                    except Exception:
                        pass
                if "ExposureTime" in exif:
                    telemetry["exposure_time"] = str(exif["ExposureTime"])
                if "DateTimeOriginal" in exif:
                    telemetry["capture_time"] = str(exif["DateTimeOriginal"])
                # GPS handling
                if "GPSInfo" in exif:
                    gps_info_raw = exif["GPSInfo"]
                    gps_info = {GPSTAGS.get(k, k): v for k, v in gps_info_raw.items()}
                    # Latitude
                    if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info:
                        d, m, s = gps_info["GPSLatitude"]
                        lat = float(d) + float(m) / 60 + float(s) / 3600
                        if gps_info["GPSLatitudeRef"] == "S":
                            lat = -lat
                        telemetry["latitude"] = round(lat, 6)
                    # Longitude
                    if "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
                        d, m, s = gps_info["GPSLongitude"]
                        lon = float(d) + float(m) / 60 + float(s) / 3600
                        if gps_info["GPSLongitudeRef"] == "W":
                            lon = -lon
                        telemetry["longitude"] = round(lon, 6)
                    # Altitude
                    if "GPSAltitude" in gps_info:
                        try:
                            telemetry["altitude_m"] = float(gps_info["GPSAltitude"])
                        except Exception:
                            pass
        except Exception:
            # Silently ignore EXIF parsing errors – defaults stay.
            pass
        return telemetry

    @staticmethod
    def preprocess_aerial_image(
        input_path: str,
        output_path: str,
        enhance_contrast: bool = True,
        sharpen: bool = True,
        denoise: bool = True,
    ) -> Tuple[int, int]:
        """
        Enhances drone imagery for computer vision:
        - CLAHE on L channel in LAB color space
        - Bilateral filtering for detail-preserving noise reduction
        - Unsharp masking for boundary & edge contrast enhancement
        """
        img = cv2.imread(input_path)
        if img is None:
            raise ValueError(f"Could not read image at {input_path}")

        h, w = img.shape[:2]

        # 1. Bilateral filtering for atmospheric haze & drone sensor noise reduction
        if denoise:
            img = cv2.bilateralFilter(img, d=5, sigmaColor=35, sigmaSpace=35)

        # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization) on Luminance
        if enhance_contrast:
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            merged = cv2.merge((cl, a, b))
            img = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

        # 3. Unsharp Masking for rooftop & road structural edge definition
        if sharpen:
            gaussian = cv2.GaussianBlur(img, (0, 0), 2.0)
            img = cv2.addWeighted(img, 1.25, gaussian, -0.25, 0)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return w, h

    @staticmethod
    def create_thumbnail(input_path: str, thumb_path: str, size: Tuple[int, int] = (400, 300)) -> str:
        """Creates a fast, high-quality thumbnail for web grid rendering."""
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        with PILImage.open(input_path) as img:
            img.thumbnail(size, PILImage.Resampling.LANCZOS)
            img.convert("RGB").save(thumb_path, "JPEG", quality=85)
        return thumb_path

