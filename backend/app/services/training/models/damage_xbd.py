import torch
import torch.nn as nn
import torch.nn.functional as F

class SiameseDamageModel(nn.Module):
    """
    Dual-stream Siamese architecture for xBD building damage assessment.
    Encodes Pre and Post disaster aerial imagery with shared weights,
    computes absolute temporal feature discrepancy, and predicts 4 damage levels.
    """
    def __init__(self, num_damage_classes: int = 4, in_channels: int = 3):
        super().__init__()
        self.num_damage_classes = num_damage_classes

        # Shared feature branch
        self.branch = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
        )

        # Cross-temporal fusion head
        # Channels: post_feat (128) + diff (128) = 256
        self.head = nn.Sequential(
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, num_damage_classes, kernel_size=3, padding=1)
        )

    def forward(self, pre_x, post_x):
        input_size = post_x.shape[-2:]
        pre_f = self.branch(pre_x)
        post_f = self.branch(post_x)
        
        diff = torch.abs(post_f - pre_f)
        fused = torch.cat([post_f, diff], dim=1)
        
        logits = self.head(fused)
        return F.interpolate(logits, size=input_size, mode='bilinear', align_corners=False)
