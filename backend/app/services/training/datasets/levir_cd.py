import os
import glob
import cv2
import numpy as np
import torch
from typing import Dict, Any, List, Tuple, Optional
from .base import BaseAerialDataset
from ..utils.licensing import DATASET_LICENSES

class LevirCDDataset(BaseAerialDataset):
    """
    LEVIR-CD Building Change Detection Dataset.
    Features:
    - Bi-temporal image pairing (A = T0, B = T1).
    - Binary change masks (0 = Unchanged, 1 = Changed building).
    - Standard train/val/test splits.
    - Synchronized dual-temporal geometric augmentations.
    """

    CLASS_NAMES = ["No Change", "Building Change"]

    def __init__(
        self,
        root_dir: str,
        split: str = "train",  # "train", "val", "test"
        target_size: Tuple[int, int] = (256, 256),
        transform: bool = True
    ):
        super().__init__(is_train=(split == "train" and transform), target_size=target_size)
        self.root_dir = root_dir
        self.split = split
        self.pairs: List[Dict[str, str]] = []

        self._discover_pairs()

    def _discover_pairs(self):
        """Discovers bi-temporal images A, B and label masks."""
        split_dir = os.path.join(self.root_dir, self.split)
        if not os.path.isdir(split_dir):
            split_dir = self.root_dir

        dir_a = os.path.join(split_dir, "A")
        dir_b = os.path.join(split_dir, "B")
        dir_label = os.path.join(split_dir, "label")

        if os.path.isdir(dir_a) and os.path.isdir(dir_b):
            a_files = sorted(glob.glob(os.path.join(dir_a, "*.png")) + glob.glob(os.path.join(dir_a, "*.jpg")))
            for a_path in a_files:
                bname = os.path.basename(a_path)
                b_path = os.path.join(dir_b, bname)
                lbl_path = os.path.join(dir_label, bname) if os.path.isdir(dir_label) else None

                if os.path.isfile(b_path):
                    self.pairs.append({
                        "a_path": a_path,
                        "b_path": b_path,
                        "label_path": lbl_path if (lbl_path and os.path.isfile(lbl_path)) else None
                    })

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        pair = self.pairs[idx]
        img_a = cv2.imread(pair["a_path"])
        img_b = cv2.imread(pair["b_path"])

        if img_a is None or img_b is None:
            raise ValueError(f"Could not load change detection pair: {pair['a_path']}")

        if pair["label_path"] and os.path.isfile(pair["label_path"]):
            mask = cv2.imread(pair["label_path"], cv2.IMREAD_GRAYSCALE)
            if mask is None:
                mask = np.zeros(img_a.shape[:2], dtype=np.uint8)
        else:
            mask = np.zeros(img_a.shape[:2], dtype=np.uint8)

        # Binary normalization: >0 is 1
        mask = (mask > 127).astype(np.uint8)

        # Synchronized geometric augmentations
        if self.is_train and np.random.rand() > 0.5:
            img_a = cv2.flip(img_a, 1)
            img_b = cv2.flip(img_b, 1)
            mask = cv2.flip(mask, 1)

        if self.is_train and np.random.rand() > 0.5:
            img_a = cv2.flip(img_a, 0)
            img_b = cv2.flip(img_b, 0)
            mask = cv2.flip(mask, 0)

        # Resize to target size
        if img_a.shape[:2] != self.target_size:
            img_a = cv2.resize(img_a, self.target_size, interpolation=cv2.INTER_LINEAR)
        if img_b.shape[:2] != self.target_size:
            img_b = cv2.resize(img_b, self.target_size, interpolation=cv2.INTER_LINEAR)
        if mask.shape[:2] != self.target_size:
            mask = cv2.resize(mask, self.target_size, interpolation=cv2.INTER_NEAREST)

        return {
            "image_a": self.to_tensor(img_a),
            "image_b": self.to_tensor(img_b),
            "mask": torch.from_numpy(mask).long()
        }

    @staticmethod
    def create_synthetic_fixture(output_dir: str, num_samples: int = 4):
        """Creates synthetic LEVIR-CD fixture for test validation."""
        for split in ["train", "val"]:
            dir_a = os.path.join(output_dir, split, "A")
            dir_b = os.path.join(output_dir, split, "B")
            dir_label = os.path.join(output_dir, split, "label")
            os.makedirs(dir_a, exist_ok=True)
            os.makedirs(dir_b, exist_ok=True)
            os.makedirs(dir_label, exist_ok=True)

            for i in range(num_samples):
                # T0: Bare land / farmland
                img_a = np.zeros((256, 256, 3), dtype=np.uint8)
                img_a[:] = (40, 120, 40)

                # T1: New building constructed
                img_b = img_a.copy()
                cv2.rectangle(img_b, (50, 50), (150, 150), (180, 180, 180), -1)

                # Label mask: 255 at building position
                mask = np.zeros((256, 256), dtype=np.uint8)
                mask[50:150, 50:150] = 255

                fname = f"sample_{i:04d}.png"
                cv2.imwrite(os.path.join(dir_a, fname), img_a)
                cv2.imwrite(os.path.join(dir_b, fname), img_b)
                cv2.imwrite(os.path.join(dir_label, fname), mask)
