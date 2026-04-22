import torch
import os
import sys
from PIL import Image
from torchvision import transforms
# Replace with your actual model class/loading logic
from src.model_definition import CellDinoClassifier 

def run_smoke_test():
    print("--- Starting Model Smoke Test ---")
    
    # 1. Configuration
    # Get the directory where main.py is located (/app/src)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    GOLD_DATA_DIR = "tests/gold_set/"
    MODEL_WEIGHTS = os.path.join(BASE_DIR, "..", "weights/dino_best_model_last.pth")
    ACCURACY_THRESHOLD = 0.80  # We expect 80% accuracy on this simple set, really is 0.53 max
    
    # 2. Setup Model
    device = torch.device("cpu") # Use CPU for CI/CD runners
    model = CellDinoClassifier(num_classes=1108)
    model.load_state_dict(torch.load(MODEL_WEIGHTS, map_location=device))
    model.to(device)
    model.eval()

    # 3. Simple Preprocessing
    preprocess = transforms.Compose([
        transforms.Resize(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # 4. Evaluation Loop
    correct = 0
    total = 0
    
    # folders named by class: tests/gold_set/class_A/img1.png
    for label in os.listdir(GOLD_DATA_DIR):
        label_dir = os.path.join(GOLD_DATA_DIR, label)
        if not os.path.isdir(label_dir): continue
            
        for img_name in os.listdir(label_dir):
            img_path = os.path.join(label_dir, img_name)
            img = Image.open(img_path).convert('RGB')
            input_tensor = preprocess(img).unsqueeze(0)

            with torch.no_grad():
                output = model(input_tensor)
                prediction = torch.argmax(output, dim=1).item()
                
            # Logic to map 'prediction' index back to 'label' string
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