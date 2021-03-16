# !/usr/bin/env python
# -- coding: utf-8 --
# @Time : 2020/8/6 10:24
# @Author : liumin
# @File : cityscapes.py

import os
from glob2 import glob
import numpy as np
from PIL import Image
from torch.utils.data import Dataset
from ..utils import palette

"""
    ADE20K dataset
    http://groups.csail.mit.edu/vision/datasets/ADE20K/
"""

class CityscapesSegmentation(Dataset):
    ignore_index = 255
    def __init__(self, data_cfg, dictionary=None, transform=None, target_transform=None, stage='train'):
        self.data_cfg = data_cfg
        self.dictionary = dictionary
        self.transform = transform
        self.target_transform = target_transform
        self.stage = stage

        self.num_classes = len(self.dictionary)
        self.category = [v for d in self.dictionary for v in d.keys()]
        self.name2id = dict(zip(self.category, range(self.num_classes)))
        self.id2name = {v: k for k, v in self.name2id.items()}
        self.palette = palette.CityScpates_palette

        self.invalid_classes = [0, 1, 2, 3, 4, 5, 6, 9, 10, 14, 15, 16, 18, 29, 30, -1]
        self.valid_classes = [7, 8, 11, 12, 13, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 31, 32, 33]
        self.class_map = dict(zip(self.valid_classes, range(self.num_classes)))

        self._imgs = []
        self._targets = []
        if self.stage == 'infer':
            if data_cfg.INDICES is not None:
                with open(data_cfg.INDICES, 'r') as fd:
                    self._imgs.extend([os.path.join(data_cfg.IMG_DIR, line.strip()) for line in fd])
            else:
                for root, fnames, _ in sorted(os.walk(data_cfg.IMG_DIR)):
                    for fname in sorted(fnames):
                        self._imgs.extend(glob(os.path.join(root, fname, data_cfg.IMG_SUFFIX)))

            if len(self._imgs) == 0:
                raise RuntimeError(
                    "Found 0 images in subfolders of: " + data_cfg.IMG_DIR if data_cfg.INDICES is not None else data_cfg.INDICES + "\n")
        else:
            if data_cfg.INDICES is not None:
                for line in open(data_cfg.INDICES):
                    imgpath, labelpath = line.strip().split(' ')
                    self._imgs.append(os.path.join(data_cfg.IMG_DIR, imgpath))
                    self._targets.append(os.path.join(data_cfg.LABELS.SEG_DIR, labelpath))
            else:
                self._imgs = glob(os.path.join(data_cfg.IMG_DIR, 'leftImg8bit',self.stage,'*',data_cfg.IMG_SUFFIX))
                self._targets = glob(os.path.join(data_cfg.LABELS.SEG_DIR,'gtFine',self.stage,'*', data_cfg.LABELS.SEG_SUFFIX))

            assert len(self._imgs) == len(self._targets), 'len(self._imgs) should be equals to len(self._targets)'
            assert len(self._imgs) > 0, 'Found 0 images in the specified location, pls check it!'

    def __getitem__(self, idx):
        if self.stage == 'infer':
            _img = np.asarray(Image.open(self._imgs[idx]).convert('RGB'), dtype=np.float32)
            img_id = os.path.basename(os.path.basename(self._imgs[idx]))
            sample = {'image': _img, 'mask': None}
            return self.transform(sample), img_id
        else:
            _img, _target = np.asarray(Image.open(self._imgs[idx]).convert('RGB'), dtype=np.float32), np.asarray(
                Image.open(self._targets[idx]), dtype=np.uint8)
            _target = self.encode_map(_target)
            sample = {'image': _img, 'target': _target}
            return self.transform(sample)

    def encode_map(self, mask):
        # This is used to convert tags
        mask_cp = mask.copy()
        # Put all void classes to zero
        for _voidc in self.invalid_classes:
            mask_cp[mask_cp == _voidc] = self.ignore_index
        # index from zero 0:18
        for _validc in self.valid_classes:
            mask_cp[mask_cp == _validc] = self.class_map[_validc]
        return mask_cp

    def __len__(self):
        return len(self._imgs)
