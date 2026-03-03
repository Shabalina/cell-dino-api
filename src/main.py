from fastapi import FastAPI, UploadFile, File, Response, status
import torch
import cv2
import numpy as np
import os
from model_definition import CellDinoClassifier

# Get the directory where main.py is located (/app/src)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Cell-DINO siRNA Predictor")

# Global variables to hold the model
device = torch.device("cpu")
model = None

@app.on_event("startup")
def load_model():
    global model
    # Initialize architecture
    model = CellDinoClassifier(num_classes=1108) 
    # Load weights
    weights_path = os.path.join(BASE_DIR, "..", "weights", "dino_best_model_last.pth")
    state_dict = torch.load(weights_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    print("Model loaded and ready for SageMaker")

def preprocess(image_bytes):
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Image preprocessing
    img = cv2.resize(img, (224, 224))
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    img_tensor = torch.from_numpy(img).unsqueeze(0)
    return img_tensor

# 1. THE HEALTH CHECK (Required by SageMaker)
@app.get("/ping")
async def ping():
    # Return 200 OK if model is loaded
    if model is not None:
        return Response(content="ok", status_code=status.HTTP_200_OK)
    return Response(content="error", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

# 2. THE INFERENCE POINT (Required by SageMaker)
@app.post("/invocations")
async def invocations(file: UploadFile = File(...)):
    # 1. Read uploaded image
    contents = await file.read()
    
    # 2. Preprocess
    input_tensor = preprocess(contents).to(device)
    
    # 3. Inference
    with torch.no_grad():
        logits = model(input_tensor)
        probabilities = torch.nn.functional.softmax(logits, dim=1)
        conf, pred = torch.max(probabilities, 1)
        
    # 4. Return JSON
    return {
        "sirna_id": int(pred.item()),
        "confidence": float(conf.item()),
        "status": "success"
    }