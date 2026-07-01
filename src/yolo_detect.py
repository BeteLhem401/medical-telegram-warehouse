import csv
from pathlib import Path
from ultralytics import YOLO

IMAGES_DIR = Path("data/raw/images")
OUTPUT_CSV = Path("data/processed/yolo_detections.csv")

PRODUCT_CLASSES = {"bottle", "cup", "vase", "wine glass", "cell phone", "book"}
PERSON_CLASS = "person"

def classify_image(detected_classes):
    has_person = PERSON_CLASS in detected_classes
    has_product = bool(detected_classes & PRODUCT_CLASSES)
    if has_person and has_product:
        return "promotional"
    if has_product and not has_person:
        return "product_display"
    if has_person and not has_product:
        return "lifestyle"
    return "other"

def main():
    model = YOLO("yolov8n.pt")
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    image_paths = list(IMAGES_DIR.rglob("*.jpg")) + list(IMAGES_DIR.rglob("*.jpeg")) + list(IMAGES_DIR.rglob("*.png"))

    rows = []
    for img_path in image_paths:
        channel_name = img_path.parent.name
        message_id = img_path.stem

        results = model(str(img_path), verbose=False)
        result = results[0]
        detected_classes = set()

        detections_for_image = []
        for box in result.boxes:
            class_name = model.names[int(box.cls)]
            confidence = float(box.conf)
            detected_classes.add(class_name)
            detections_for_image.append((class_name, confidence))

        category = classify_image(detected_classes)

        if detections_for_image:
            for class_name, confidence in detections_for_image:
                rows.append({
                    "message_id": message_id,
                    "channel_name": channel_name,
                    "detected_class": class_name,
                    "confidence_score": round(confidence, 4),
                    "image_category": category
                })
        else:
            rows.append({
                "message_id": message_id,
                "channel_name": channel_name,
                "detected_class": "none",
                "confidence_score": 0.0,
                "image_category": "other"
            })

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["message_id", "channel_name", "detected_class", "confidence_score", "image_category"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Detected {len(rows)} objects across {len(image_paths)} images")
    print(f"Saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()