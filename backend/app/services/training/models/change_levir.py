import torch
import torch.nn as nn
import torch.nn.functional as F

class BiTemporalChangeDetectionModel(nn.Module):
    """
    Bi-temporal Siamese Change Detection Model for LEVIR-CD.
    Extracts multi-scale features from T0 and T1, computes distance embeddings,
    and classifies pixels as Changed (1) or Unchanged (0).
    """
    def __init__(self, in_channels: int = 3, num_classes: int = 2):
        super().__init__()
        self.num_classes = num_classes

        # Shared feature encoder
        self.encoder = nn.Sequential(
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

        # Difference attention & decoder
        self.decoder = nn.Sequential(
            nn.Conv2d(256, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, num_classes, kernel_size=3, padding=1),
        )

    def forward(self, img_t0, img_t1):
        input_size = img_t1.shape[-2:]
        f0 = self.encoder(img_t0)
        f1 = self.encoder(img_t1)

        diff = torch.abs(f1 - f0)
        fused = torch.cat([diff, f1], dim=1)

        logits = self.decoder(fused)
        return F.interpolate(logits, size=input_size, mode='bilinear', align_corners=False)
