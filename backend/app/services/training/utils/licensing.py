import os
import hashlib
from typing import Dict, Any, List

DATASET_LICENSES: Dict[str, Dict[str, Any]] = {
    "LoveDA": {
        "full_name": "Land-Cover Semantic Segmentation Dataset for Aerial Imagery (LoveDA)",
        "license": "CC BY-NC-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "author": "Wang et al., Wuhan University & LIESMARS",
        "citation": "Wang, J., et al. LoveDA: A Remote Sensing Land-Cover Dataset for Domain Adaptive Semantic Segmentation. NeurIPS 2021.",
        "commercial_use_allowed": False,
        "classes": [
            "Background",
            "Building",
            "Road",
            "Water",
            "Barren",
            "Forest",
            "Agricultural"
        ],
        "acquisition_procedure": (
            "1. Download LoveDA from official Zenodo repository or GitHub: https://github.com/Junjue-Wang/LoveDA\n"
            "2. Extract Train.zip and Val.zip into storage/datasets/LoveDA/Urban and storage/datasets/LoveDA/Rural.\n"
            "3. Verify SHA256 checksums before initiating training.\n"
            "4. Adhere to non-commercial academic research attribution license."
        )
    },
    "xBD": {
        "full_name": "xBD: Building Damage Assessment from High-Resolution Aerial Imagery",
        "license": "Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)",
        "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
        "author": "Gupta et al., Defense Innovation Unit (DIU) & xView2 Challenge",
        "citation": "Gupta, R., et al. Creating xBD: A Dataset for Assessing Building Damage from Satellite Imagery. CVPR Workshops 2019.",
        "commercial_use_allowed": False,
        "damage_classes": [
            "no-damage",
            "minor-damage",
            "major-damage",
            "destroyed"
        ],
        "acquisition_procedure": (
            "1. Register and request access via xView2 challenge portal: https://xview2.org/\n"
            "2. Download disaster disaster event archives (e.g., hurricane-michael, woolsey-fire, tsunami, etc.).\n"
            "3. Extract pre_images, post_images, and targets JSON polygons into storage/datasets/xBD/.\n"
            "4. Validate geometry integrity and polygon label sanity."
        )
    },
    "LEVIR-CD": {
        "full_name": "LEVIR-CD: Large-scale Remote Sensing Dataset for Building Change Detection",
        "license": "CC BY 4.0 (Creative Commons Attribution 4.0 International)",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "author": "Chen et al., Beihang University LEVIR Lab",
        "citation": "Chen, H., & Shi, Z. A Spatial-Temporal Attention-Based Method and a New Dataset for Remote Sensing Image Change Detection. Remote Sensing 2020.",
        "commercial_use_allowed": True,
        "classes": [
            "No Change",
            "Change (New/Altered Building)"
        ],
        "acquisition_procedure": (
            "1. Download LEVIR-CD from official Google Drive / Baidu Wangpan repository link.\n"
            "2. Extract paired images A (T0), B (T1), and label masks into storage/datasets/LEVIR-CD/train, val, test.\n"
            "3. Verify 1024x1024 bi-temporal RGB pairs and binary change masks."
        )
    }
}

def verify_file_integrity(filepath: str, expected_sha256: str = None) -> Dict[str, Any]:
    """Computes SHA256 checksum and verifies file existence and integrity."""
    if not os.path.isfile(filepath):
        return {"exists": False, "sha256": None, "verified": False, "size_bytes": 0}
    
    hasher = hashlib.sha256()
    size = os.path.getsize(filepath)
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    digest = hasher.hexdigest()
    
    verified = (digest.lower() == expected_sha256.lower()) if expected_sha256 else True
    return {
        "exists": True,
        "sha256": digest,
        "verified": verified,
        "size_bytes": size
    }

def get_dataset_license_info(dataset_name: str) -> Dict[str, Any]:
    """Returns license, attribution, and acquisition protocol for a supported dataset."""
    return DATASET_LICENSES.get(dataset_name, {
        "error": f"Unknown dataset '{dataset_name}'. Supported: {list(DATASET_LICENSES.keys())}"
    })
