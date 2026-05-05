import cv2
import numpy as np
import torch

def preprocess_image(input_data, size=224):
    """
    Standardized preprocessing for the CellDINO model.
    Accepts either a string (file path) or raw bytes.
    """
    if isinstance(input_data, bytes):
        # Handle raw bytes (from FastAPI/invocations)
        nparr = np.frombuffer(input_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    else:
        # Handle file path (from Smoke Tests)
        img = cv2.imread(input_data)

    if img is None:
        return None

    # 2. Resize
    img = cv2.resize(img, (size, size))
    
    # 3. Convert to RGB (Training script used cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # 4. Convert to float and scale 0-1
    img = img.astype(np.float32) / 255.0
    
    # 5. Transpose from HWC to CHW
    img = np.transpose(img, (2, 0, 1))
    
    # 6. Convert to Tensor and add Batch dimension
    input_tensor = torch.from_numpy(img).unsqueeze(0)
    
    return input_tensor