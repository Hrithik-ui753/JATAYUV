import os
import random
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
from typing import Tuple, Dict, Any, List, Optional

class BaseAerialDataset(Dataset):
    """Abstract base dataset for aerial imagery with standard augmentations."""

    def __init__(self, is_train: bool = True, target_size: Tuple[int, int] = (256, 256)):
        self.is_train = is_train
        self.target_size = target_size

    def apply_augmentations(
        self,
        img: np.ndarray,
        mask: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Applies spatial and photometric data augmentations for aerial views."""
        # Random horizontal flip
        if self.is_train and random.random() > 0.5:
            img = cv2.flip(img, 1)
            if mask is not None:
                mask = cv2.flip(mask, 1)

        # Random vertical flip
        if self.is_train and random.random() > 0.5:
            img = cv2.flip(img, 0)
            if mask is not None:
                mask = cv2.flip(mask, 0)

        # Random 90-degree rotation (aerial invariance)
        if self.is_train and random.random() > 0.5:
            rot_k = random.choice([1, 2, 3])
            img = np.ascontiguousarray(np.rot90(img, k=rot_k))
            if mask is not None:
                mask = np.ascontiguousarray(np.rot90(mask, k=rot_k))

        # Resize to target dimension
        if img.shape[:2] != self.target_size:
            img = cv2.resize(img, self.target_size, interpolation=cv2.INTER_LINEAR)
        if mask is not None and mask.shape[:2] != self.target_size:
            mask = cv2.resize(mask, self.target_size, interpolation=cv2.INTER_NEAREST)

        return img, mask

    @staticmethod
    def to_tensor(img: np.ndarray) -> torch.Tensor:
        """Converts BGR uint8 image to normalized RGB PyTorch Tensor [C, H, W]."""
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        # ImageNet mean & std normalization
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        norm_img = (rgb - mean) / std
        return torch.from_numpy(norm_img).permute(2, 0, 1).float()
