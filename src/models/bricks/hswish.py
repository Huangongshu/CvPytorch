# Copyright (c) OpenMMLab. All rights reserved.
import torch
import torch.nn as nn


from .registry import ACTIVATION_LAYERS
from .wrappers import TORCH_VERSION



class HSwish(nn.Module):
    """Hard Swish Module.

    This module applies the hard swish function:

    .. math::
        Hswish(x) = x * ReLU6(x + 3) / 6

    Args:
        inplace (bool): can optionally do the operation in-place.
            Default: False.

    Returns:
        Tensor: The output tensor.
    """

    def __init__(self, inplace: bool = False):
        super().__init__()
        self.act = nn.ReLU6(inplace)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x * self.act(x + 3) / 6



ACTIVATION_LAYERS.register_module(module=nn.Hardswish, name='HSwish')
