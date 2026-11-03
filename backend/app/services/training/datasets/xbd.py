import os
import json
import glob
import cv2
import numpy as np
import torch
from typing import Dict, Any, List, Tuple, Optional
from .base import BaseAerialDataset
from ..utils.licensing import DATASET_LICENSES

class XBDDataset(BaseAerialDataset):
    """
    xBD / xView2 Disaster Building Damage Assessment Dataset.
    Features:
    - Pre/Post disaster paired imagery.
    - Polygon annotation parsing.
    - Building crop extraction or full scene damage mask generation.
    - 4 Standard Damage Levels:
      0: no-damage
      1: minor-damage
      2: major-damage
      3: destroyed
    - Scene-separated dataset splitting (prevents geographic data leakage).
    - Class imbalance frequency weighting.
    """

    DAMAGE_MAPPING = {
        "no-damage": 0,
        "minor-damage": 1,
        "major-damage": 2,
        "destroyed": 3,
        "un-classified": 0  # Default un-classified to 0 or mask
    }

    CLASS_NAMES = ["no-damage", "minor-damage", "major-damage", "destroyed"]

    def __init__(
        self,
        root_dir: str,
        split: str = "train",  # "train", "val", "test"
        target_size: Tuple[int, int] = (256, 256),
        transform: bool = True,
        val_ratio: float = 0.2,
        seed: int = 42
    ):
        super().__init__(is_train=(split == "train" and transform), target_size=target_size)
        self.root_dir = root_dir
        self.split = split
        self.val_ratio = val_ratio
        self.seed = seed
        self.pairs: List[Dict[str, Any]] = []

        self._discover_and_split_scenes()

    def _discover_and_split_scenes(self):
        """Discovers pre/post image pairs and json annotations, grouping by disaster scene."""
        images_dir = os.path.join(self.root_dir, "images")
        labels_dir = os.path.join(self.root_dir, "labels")

        if not os.path.isdir(images_dir):
            images_dir = self.root_dir
        if not os.path.isdir(labels_dir):
            labels_dir = self.root_dir

        post_files = sorted(glob.glob(os.path.join(images_dir, "*_post_disaster.png")) +
                            glob.glob(os.path.join(images_dir, "*_post_disaster.jpg")))

        # Group by disaster scene name (e.g., 'guatemala-volcano_00000001')
        scenes: Dict[str, List[Dict[str, Any]]] = {}
        for post_img_path in post_files:
            bname = os.path.basename(post_img_path)
            prefix = bname.replace("_post_disaster.png", "").replace("_post_disaster.jpg", "")
            ext = os.path.splitext(bname)[1]

            pre_img_path = os.path.join(images_dir, f"{prefix}_pre_disaster{ext}")
            post_label_path = os.path.join(labels_dir, f"{prefix}_post_disaster.json")
            pre_label_path = os.path.join(labels_dir, f"{prefix}_pre_disaster.json")

            if os.path.isfile(pre_img_path):
                # Scene identifier before underscore
                scene_key = prefix.split("_")[0] if "_" in prefix else prefix
                if scene_key not in scenes:
                    scenes[scene_key] = []
                scenes[scene_key].append({
                    "pre_image_path": pre_img_path,
                    "post_image_path": post_img_path,
                    "post_label_path": post_label_path if os.path.isfile(post_label_path) else None,
                    "pre_label_path": pre_label_path if os.path.isfile(pre_label_path) else None,
                    "scene": scene_key
                })

        # Scene-separated deterministic split
        sorted_scenes = sorted(scenes.keys())
        rng = np.random.RandomState(self.seed)
        shuffled_scenes = sorted_scenes.copy()
        rng.shuffle(shuffled_scenes)

        val_count = max(1, int(len(shuffled_scenes) * self.val_ratio)) if len(shuffled_scenes) > 1 else 0
        if self.split == "val":
            target_scenes = set(shuffled_scenes[:val_count]) if val_count > 0 else set(shuffled_scenes)
        elif self.split == "test":
            target_scenes = set(shuffled_scenes[:val_count]) if val_count > 0 else set(shuffled_scenes)
        else:  # train
            target_scenes = set(shuffled_scenes[val_count:]) if val_count > 0 else set(shuffled_scenes)

        for s in target_scenes:
            self.pairs.extend(scenes[s])

    def __len__(self) -> int:
        return len(self.pairs)

    def _parse_damage_polygons(self, label_path: Optional[str], shape: Tuple[int, int]) -> np.ndarray:
        """Parses xBD JSON building polygons into discrete damage label mask [H, W]."""
        mask = np.zeros(shape, dtype=np.uint8)
        if not label_path or not os.path.isfile(label_path):
            return mask

        try:
            with open(label_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            features = data.get("features", {}).get("xy", [])
            for feat in features:
                properties = feat.get("properties", {})
                subtype = properties.get("subtype", "no-damage")
                damage_id = self.DAMAGE_MAPPING.get(subtype, 0)

                wkt = feat.get("wkt", "")
                if "POLYGON" in wkt:
                    pts_str = wkt.replace("POLYGON ((", "").replace("))", "")
                    pts = []
                    for pair in pts_str.split(","):
                        parts = pair.strip().split(" ")
                        if len(parts) >= 2:
                            try:
                                pts.append([float(parts[0]), float(parts[1])])
                            except ValueError:
                                pass
                    if len(pts) >= 3:
                        poly = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))
                        cv2.fillPoly(mask, [poly], damage_id)
        except Exception:
            pass

        return mask

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        pair = self.pairs[idx]
        pre_img = cv2.imread(pair["pre_image_path"])
        post_img = cv2.imread(pair["post_image_path"])

        if pre_img is None or post_img is None:
            raise ValueError(f"Could not load image pair: {pair['pre_image_path']}")

        damage_mask = self._parse_damage_polygons(pair["post_label_path"], post_img.shape[:2])

        # Dual-image synchronized spatial augmentations
        if self.is_train and np.random.rand() > 0.5:
            pre_img = cv2.flip(pre_img, 1)
            post_img = cv2.flip(post_img, 1)
            damage_mask = cv2.flip(damage_mask, 1)

        if self.is_train and np.random.rand() > 0.5:
            pre_img = cv2.flip(pre_img, 0)
            post_img = cv2.flip(post_img, 0)
            damage_mask = cv2.flip(damage_mask, 0)

        # Resize to target size
        if pre_img.shape[:2] != self.target_size:
            pre_img = cv2.resize(pre_img, self.target_size, interpolation=cv2.INTER_LINEAR)
        if post_img.shape[:2] != self.target_size:
            post_img = cv2.resize(post_img, self.target_size, interpolation=cv2.INTER_LINEAR)
        if damage_mask.shape[:2] != self.target_size:
            damage_mask = cv2.resize(damage_mask, self.target_size, interpolation=cv2.INTER_NEAREST)

        damage_mask = np.clip(damage_mask, 0, len(self.CLASS_NAMES) - 1).astype(np.int64)

        return {
            "pre_image": self.to_tensor(pre_img),
            "post_image": self.to_tensor(post_img),
            "damage_mask": torch.from_numpy(damage_mask).long(),
            "scene": pair["scene"]
        }

    def compute_class_weights(self) -> torch.Tensor:
        """
        Calculates inverse-frequency class weights to combat extreme disaster damage imbalance
        (e.g., destroyed buildings are rare compared to intact background).
        """
        counts = np.zeros(len(self.CLASS_NAMES), dtype=np.int64)
        for pair in self.pairs:
            if pair["post_label_path"] and os.path.isfile(pair["post_label_path"]):
                mask = self._parse_damage_polygons(pair["post_label_path"], (256, 256))
                for c in range(len(self.CLASS_NAMES)):
                    counts[c] += np.sum(mask == c)

        total = np.sum(counts)
        if total == 0 or np.any(counts == 0):
            # Smooth default weights
            return torch.tensor([0.2, 1.5, 2.0, 3.0], dtype=torch.float32)

        freq = counts / total
        weights = 1.0 / (np.log(1.02 + freq))
        norm_weights = weights / np.mean(weights)
        return torch.from_numpy(norm_weights).float()

    @staticmethod
    def create_synthetic_fixture(output_dir: str, num_scenes: int = 2, pairs_per_scene: int = 3):
        """Creates synthetic xBD disaster dataset fixture for testing & training loop verification."""
        img_dir = os.path.join(output_dir, "images")
        lbl_dir = os.path.join(output_dir, "labels")
        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(lbl_dir, exist_ok=True)

        disasters = [f"event-{i}" for i in range(num_scenes)]
        for d in disasters:
            for j in range(pairs_per_scene):
                prefix = f"{d}_{j:08d}"
                # Pre disaster (intact)
                pre_img = np.zeros((256, 256, 3), dtype=np.uint8)
                pre_img[:] = (34, 139, 34)  # vegetation
                cv2.rectangle(pre_img, (40, 40), (100, 100), (200, 200, 200), -1)  # building 1
                cv2.rectangle(pre_img, (140, 140), (220, 220), (180, 180, 180), -1) # building 2

                # Post disaster (damaged)
                post_img = pre_img.copy()
                cv2.rectangle(post_img, (40, 40), (100, 100), (100, 100, 100), -1) # minor damage
                cv2.rectangle(post_img, (140, 140), (220, 220), (30, 30, 30), -1)   # destroyed

                cv2.imwrite(os.path.join(img_dir, f"{prefix}_pre_disaster.png"), pre_img)
                cv2.imwrite(os.path.join(img_dir, f"{prefix}_post_disaster.png"), post_img)

                # Post disaster label with building polygons & damage subtypes
                label_data = {
                    "features": {
                        "xy": [
                            {
                                "properties": {"subtype": "minor-damage", "feature_type": "building"},
                                "wkt": "POLYGON ((40 40, 100 40, 100 100, 40 100, 40 40))"
                            },
                            {
                                "properties": {"subtype": "destroyed", "feature_type": "building"},
                                "wkt": "POLYGON ((140 140, 220 140, 220 220, 140 220, 140 140))"
                            }
                        ]
                    }
                }
                with open(os.path.join(lbl_dir, f"{prefix}_post_disaster.json"), "w", encoding="utf-8") as f:
                    json.dump(label_data, f, indent=2)
