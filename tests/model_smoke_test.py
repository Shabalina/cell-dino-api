import torch
import os
import sys
import cv2
import numpy as np

# Replace with your actual model class/loading logic
from src.model_definition import CellDinoClassifier 

def run_smoke_test():
    print("--- Starting Model Smoke Test ---")
    
    # Configuration
    # Get the directory where main.py is located (/app/src)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    GOLD_DATA_DIR = "tests/gold_set/"
    MODEL_WEIGHTS = os.path.join(BASE_DIR, "..", "weights/dino_best_model_last.pth")
    ACCURACY_THRESHOLD = 0.80  # We expect 80% accuracy on this simple set, really is 0.53 max
    
    # Setup Model
    device = torch.device("cpu") # Use CPU for CI/CD runners
    model = CellDinoClassifier(num_classes=1108)
    model.load_state_dict(torch.load(MODEL_WEIGHTS, map_location=device))
    model.to(device)
    model.eval()

    # Evaluation Loop
    correct = 0
    total = 0
    
    # folders named by class: tests/gold_set/class_A/img1.png
    for label in os.listdir(GOLD_DATA_DIR):
        label_dir = os.path.join(GOLD_DATA_DIR, label)
        if not os.path.isdir(label_dir): continue
            
        for img_name in os.listdir(label_dir):
            # Image preprocessing
            img_path = os.path.join(label_dir, img_name)
            # 1. Read with OpenCV
            img = cv2.imread(img_path)
            if img is None:
                print(f"Could not read {img_path}")
                continue
            # 2. Resize
            img = cv2.resize(img, (224, 224))
            # 3. Convert to float and scale 0-1
            img = img.astype(np.float32) / 255.0
            # 4. Transpose from HWC (224,224,3) to CHW (3,224,224)
            img = np.transpose(img, (2, 0, 1))
            # 5. Convert to Tensor and add Batch dimension
            input_tensor = torch.from_numpy(img).unsqueeze(0).to(device)

            with torch.no_grad():
                logits = model(input_tensor)
                # Matching FastAPI logic: Softmax then Argmax
                probabilities = torch.nn.functional.softmax(logits, dim=1)
                prediction = torch.argmax(probabilities, dim=1).item()
                
            # Logic to map 'prediction' index back to 'label' string
            print (f"Predicted: {prediction}, True Label: {label}")
            if check_prediction(prediction, label):
                correct += 1
            total += 1

    accuracy = correct / total if total > 0 else 0
    print(f"Smoke Test Accuracy: {accuracy:.2%}")

    if accuracy < ACCURACY_THRESHOLD:
        print(f"FAILED: Accuracy {accuracy:.2%} is below threshold {ACCURACY_THRESHOLD}")
        sys.exit(1) # This kills the GitHub Action
    
    print("PASSED: Model performance is acceptable.")
    sys.exit(0)

def check_prediction(pred_index, true_label):
    # Map your model's output index to your folder labels
    class_map = {0: "Normal", 1: "Abnormal"} 
    return class_map.get(pred_index) == true_label

if __name__ == "__main__":
    run_smoke_test()