import torch
import torch.nn as nn

class CellDinoClassifier(nn.Module):
    def __init__(self, num_classes=1108):
        super(CellDinoClassifier, self).__init__()
        # Using ViT-Small (vits14) for better speed/memory on single GPU
        self.backbone = torch.hub.load('facebookresearch/dinov2', 'dinov2_vits14')
        # ViT-S/14 has an embedding dimension of 384
        embed_dim = self.backbone.embed_dim 
        
        # Custom Classification Head
        self.head = nn.Sequential(
            nn.Linear(embed_dim, 2048),
            nn.BatchNorm1d(2048),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(2048, num_classes)
        )

    def forward(self, x):
        features = self.backbone(x) # Returns CLS token
        return self.head(features)