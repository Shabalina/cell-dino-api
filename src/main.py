from fastapi import FastAPI, Request, Response, status
import torch
import cv2
import numpy as np
import os
from model_definition import CellDinoClassifier
from image_processing import preprocess_image

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

# 1. THE HEALTH CHECK (Required by SageMaker)
@app.get("/ping")
async def ping():
    # Return 200 OK if model is loaded
    if model is not None:
        return {"version": "2.0.0-new-preprocessing", "status": "Healthy"}
    return Response(content="error", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

# 2. THE INFERENCE POINT (Required by SageMaker)
@app.post("/invocations")
async def invocations(request: Request):
    # 1. Read the raw bytes directly from the request body
    contents = await request.body()

    if not contents:
        return Response(content="No data received", status_code=status.HTTP_400_BAD_REQUEST)
    
    # 2. Preprocess (Use the bytes directly)
    # try:
    #     nparr = np.frombuffer(contents, np.uint8)
    #     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
    #     if img is None:
    #         raise ValueError("Could not decode image")
    
    #     # Image preprocessing
    #     img = cv2.resize(img, (224, 224))
    #     img = img.astype(np.float32) / 255.0
    #     img = np.transpose(img, (2, 0, 1))
    #     input_tensor = torch.from_numpy(img).unsqueeze(0).to(device)

    # except Exception as e:
    #     return Response(content=f"Preprocessing error: {str(e)}", status_code=status.HTTP_400_BAD_REQUEST)
    
    # Image preprocessing
    input_tensor = preprocess_image(contents)
    if input_tensor is None:
        return Response(content="Preprocessing error: Could not decode image", status_code=400)

    # Move to device (GPU/CPU)
    input_tensor = input_tensor.to(device)
    
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