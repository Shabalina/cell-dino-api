import torch
import os
import sys
import cv2
import numpy as np

# Replace with your actual model class/loading logic
from src.model_definition import CellDinoClassifier 
from src.image_processing import preprocess_image

# weights_filename = "dino_best_model_last"
weights_filename = "best_model_pytorch-training-2026-02-12-18-05-51-293"

def run_smoke_test():
    print("--- Starting Model Smoke Test ---")
    
    # Configuration
    # Get the directory where main.py is located (/app/src)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    GOLD_DATA_DIR = "tests/gold_set/"
    MODEL_WEIGHTS = os.path.join(BASE_DIR, "..", f"weights/{weights_filename}.pth")
    ACCURACY_THRESHOLD = 0.40  # Best validation accuracy was 0.53, 0.40 is a reasonable threshold for a smoke test
    
    # Setup Model
    device = torch.device("cpu") # Use CPU for CI/CD runners
    model = CellDinoClassifier(num_classes=1108)
    print("MODEL SET UP")
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

            input_tensor = preprocess_image(img_path)
            if input_tensor is None:
                continue

            input_tensor = input_tensor.to(device)

            with torch.no_grad():
                logits = model(input_tensor)
                # Matching FastAPI logic: Softmax then Argmax
                probabilities = torch.nn.functional.softmax(logits, dim=1)
                conf, pred = torch.max(probabilities, 1)
                
            # Logic to map 'prediction' index back to 'label' string
            print (f"Predicted: {pred.item()}, Confidence: {conf.item():.2f}, True Label: {label}, Image: {img_name}")
            if str(pred.item()) == str(label):
                correct += 1
            total += 1

    accuracy = correct / total if total > 0 else 0
    print(f"Smoke Test Accuracy: {accuracy:.2%}")
    print(f"Correct guesses: {correct} from {total} samples.")

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