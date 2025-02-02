# !/usr/bin/env python
# -- coding: utf-8 --
# @Time : 2020/11/6 18:16
# @Author : liumin
# @File : mobilenet_v2.py

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils import model_zoo
from torchvision.models.mobilenet import mobilenet_v2
from torchvision.models.mobilenetv2 import model_urls

"""
    MobileNetV2: Inverted Residuals and Linear Bottlenecks
    https://arxiv.org/abs/1801.04381
"""


class MobileNetV2(nn.Module):

    def __init__(self, subtype='mobilenet_v2', out_stages=[3, 5, 7], output_stride=16, classifier=False, num_classes=1000, pretrained = False, backbone_path=None):
        super(MobileNetV2, self).__init__()
        self.subtype = subtype
        self.out_stages = out_stages
        self.output_stride = output_stride  # 8, 16, 32
        self.classifier = classifier
        self.num_classes = num_classes
        self.pretrained = pretrained
        self.backbone_path = backbone_path


        if self.subtype == 'mobilenet_v2':
            features = mobilenet_v2(self.pretrained).features
            self.out_channels = [32, 16, 24, 32, 64, 96, 160, 320]
        else:
            raise NotImplementedError

        self.out_channels = [self.out_channels[ost] for ost in self.out_stages]

        self.stem = nn.Sequential(list(features.children())[0]) # x2
        self.stage1 = nn.Sequential(list(features.children())[1])
        self.stage2 = nn.Sequential(*list(features.children())[2:4])
        self.stage3 = nn.Sequential(*list(features.children())[4:7])
        self.stage4 = nn.Sequential(*list(features.children())[7:11])
        self.stage5 = nn.Sequential(*list(features.children())[11:14])
        self.stage6 = nn.Sequential(*list(features.children())[14:17])
        self.stage7 = nn.Sequential(list(features.children())[17])
        if self.classifier:
            self.last_conv = nn.Sequential(list(features.children())[18])
            self.fc = mobilenet_v2(self.pretrained).classifier
            self.fc[1] = nn.Linear(self.fc[1].in_features, self.num_classes)
            self.out_channels = self.num_classes

        if self.pretrained:
            self.load_pretrained_weights()
        else:
            self.init_weights()

    def init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.normal_(m.weight, std=0.001)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0.0001)
                m.momentum = 0.1
                m.eps = 1e-05
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)


    def forward(self, x):
        x = self.stem(x)
        output = []
        for i in range(1, 8):
            stage = getattr(self, 'stage{}'.format(i))
            x = stage(x)
            if i in self.out_stages and not self.classifier:
                output.append(x)
        if self.classifier:
            x = self.last_conv(x)
            x = F.adaptive_avg_pool2d(x, 1).reshape(x.shape[0], -1)
            x = self.fc(x)
            return x
        return output if len(self.out_stages) > 1 else output[0]


    def freeze_bn(self):
        for layer in self.modules():
            if isinstance(layer, nn.BatchNorm2d):
                layer.eval()

    def load_pretrained_weights(self):
        url = model_urls[self.subtype]
        if url is not None:
            pretrained_state_dict = model_zoo.load_url(url)
            print('=> loading pretrained model {}'.format(url))
            self.load_state_dict(pretrained_state_dict, strict=False)
        elif self.backbone_path is not None:
            print('=> loading pretrained model {}'.format(self.backbone_path))
            self.load_state_dict(torch.load(self.backbone_path))


if __name__=="__main__":
    model =MobileNetV2('mobilenet_v2')
    print(model)

    input = torch.randn(1, 3, 224, 224)
    out = model(input)
    for o in out:
        print(o.shape)