import os
import random
import numpy as np
import torch

def set_seed(seed: int = 42) -> None:
    """Set seeds for reproducibility across Python, NumPy and PyTorch.
    Also configures deterministic behavior for CUDA when available.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        # Enforce deterministic cuDNN behavior – may affect performance.
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

