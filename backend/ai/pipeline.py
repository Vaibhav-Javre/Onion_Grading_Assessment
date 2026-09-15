import os
import time
import uuid
from collections import Counter

import cv2
import numpy as np

from backend.ai.classifier import OnionClassifier
from backend.ai.detector import OnionDetector
from config import Config

# High-contrast color palette (BGR format for OpenCV)
CLASS_COLORS_BGR = {
    "Healthy": (50, 180, 50),     # Vibrant Green
    "Damaged": (20, 140, 230),    # Amber / Warm Gold
    "Rotten": (30, 30, 220),      # Crimson Red
    "Sprouted": (10, 90, 240),    # Deep Orange
    "Uncertain": (130, 120, 100)  # Slate Gray
}

def evaluate_onion_image(image_path, yolo_conf=None, classifier_conf=None):
    """
    Orchestrates complete onion quality evaluation:
    1. Reads input image
    2. Runs YOLO11 detector for onion bounding boxes
    3. Crops each detection and classifies into [Healthy, Damaged, Rotten, Sprouted]
    4. Annotates image with professional bounding boxes and class tags
    5. Computes official procurement grading:
       - Grade A = Healthy
       - URS = Damaged
       - Rejected = Rotten + Sprouted
    6. Generates detailed structured results and official text summary
    
    NOTE: Size estimation is intentionally excluded per project specification.
    """
    pipeline_start = time.perf_counter()
    if yolo_conf is None:
        yolo_conf = Config.YOLO_CONFIDENCE_THRESHOLD
    if classifier_conf is None:
        classifier_conf = Config.CLASSIFIER_CONFIDENCE_THRESHOLD

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image at path: {image_path}")

    _h, w = image.shape[:2]
    annotated_image = image.copy()

    detector = OnionDetector()
    classifier = OnionClassifier()

    # Step 1: Run YOLO11 detection as currently
    yolo_start = time.perf_counter()
    raw_detections = detector.detect(image, conf_threshold=yolo_conf)
    yolo_time = time.perf_counter() - yolo_start

    # Step 2: Extract and store ALL detected onion crops
    valid_detections = []
    crops = []
    for det in raw_detections:
        x1, y1, x2, y2 = det["box"]
        crop = image[y1:y2, x1:x2]
        if crop is not None and crop.size > 0:
            valid_detections.append(det)
            crops.append(crop)

    # Steps 3, 4, 5: Preprocess, stack into NumPy batch, and run classifier ONCE
    cls_start = time.perf_counter()
    classification_results = classifier.classify_batch(crops, conf_threshold=classifier_conf)
    cls_time = time.perf_counter() - cls_start

    items = []
    class_counts = Counter()

    # Step 6: Map each prediction back to its corresponding onion detection
    for idx, (det, (class_name, cls_conf, _prob_dict)) in enumerate(zip(valid_detections, classification_results), start=1):
        x1, y1, x2, y2 = det["box"]
        class_counts[class_name] += 1

        # Save item details
        items.append({
            "onion_number": idx,
            "class_name": class_name,
            "classification_confidence": cls_conf,
            "detection_confidence": det["confidence"],
            "bounding_box": [x1, y1, x2, y2]
        })

        # Step 7: Draw bounding box & tag
        color = CLASS_COLORS_BGR.get(class_name, (50, 180, 50))
        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 3)

        # Label badge
        label = f"#{idx} {class_name} {int(cls_conf * 100)}%"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        thickness = 2
        (tw, th), _baseline = cv2.getTextSize(label, font, font_scale, thickness)

        badge_y1 = max(0, y1 - th - 10)
        badge_y2 = y1
        badge_x2 = min(w, x1 + tw + 10)

        # Draw filled background badge for contrast
        cv2.rectangle(annotated_image, (x1, badge_y1), (badge_x2, badge_y2), color, -1)
        # Text in white
        cv2.putText(
            annotated_image,
            label,
            (x1 + 5, badge_y2 - 5),
            font,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA
        )

    # FUTURE_EXTENSION_POINT_SIZE_ESTIMATION:
    # Reserved hook for future segmentation & physical diameter measurement.
    # Currently disabled per Project Requirement #31.

    total_onions = len(items)
    healthy_count = class_counts.get("Healthy", 0)
    damaged_count = class_counts.get("Damaged", 0)
    rotten_count = class_counts.get("Rotten", 0)
    sprouted_count = class_counts.get("Sprouted", 0)
    uncertain_count = class_counts.get("Uncertain", 0)

    # Percentages
    healthy_pct = round((healthy_count / total_onions * 100) if total_onions else 0, 1)
    damaged_pct = round((damaged_count / total_onions * 100) if total_onions else 0, 1)
    rotten_pct = round((rotten_count / total_onions * 100) if total_onions else 0, 1)
    sprouted_pct = round((sprouted_count / total_onions * 100) if total_onions else 0, 1)
    uncertain_pct = round((uncertain_count / total_onions * 100) if total_onions else 0, 1)

    # Grading mapping:
    # Grade A: Healthy onions
    # URS: Damaged onions
    # Rejected: Rotten + Sprouted onions
    grade_a = healthy_count
    urs = damaged_count
    rejected = rotten_count + sprouted_count

    grade_a_pct = round((grade_a / total_onions * 100) if total_onions else 0, 1)
    urs_pct = round((urs / total_onions * 100) if total_onions else 0, 1)
    rejected_pct = round((rejected / total_onions * 100) if total_onions else 0, 1)

    # Overall Quality Assessment result headline
    if total_onions == 0:
        overall_result = "No Onions Detected"
    elif grade_a_pct >= 75:
        overall_result = "Grade A - Premium Quality"
    elif (grade_a_pct + urs_pct) >= 70:
        overall_result = "URS Standard - Commercial Quality"
    else:
        overall_result = "High Rejection - Substandard Batch"

    # Official Quality Summary text
    quality_summary = (
        f"The AI system detected {total_onions} onions. "
        f"{healthy_count} onions were classified as Healthy ({healthy_pct}%), "
        f"{damaged_count} as Damaged ({damaged_pct}%), "
        f"{rotten_count} as Rotten ({rotten_pct}%) and "
        f"{sprouted_count} as Sprouted ({sprouted_pct}%). "
        f"Based on official procurement grading standards, "
        f"{grade_a} onions were categorized as Grade A, "
        f"{urs} as URS and {rejected} as Rejected."
    )

    # Save annotated output image
    os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
    out_filename = f"annotated_{uuid.uuid4().hex}.jpg"
    out_path = os.path.join(Config.OUTPUT_FOLDER, out_filename)
    cv2.imwrite(out_path, annotated_image)

    total_pipeline_time = time.perf_counter() - pipeline_start
    print(
        f"[AI Pipeline Timing] Single Image ({total_onions} onions) | "
        f"YOLO: {yolo_time:.3f}s | Classifier: {cls_time:.3f}s | "
        f"Total Pipeline: {total_pipeline_time:.3f}s"
    )

    return {
        "total_onions": total_onions,
        "classes": {
            "Healthy": {"count": healthy_count, "percentage": healthy_pct},
            "Damaged": {"count": damaged_count, "percentage": damaged_pct},
            "Rotten": {"count": rotten_count, "percentage": rotten_pct},
            "Sprouted": {"count": sprouted_count, "percentage": sprouted_pct},
            "Uncertain": {"count": uncertain_count, "percentage": uncertain_pct}
        },
        "grades": {
            "Grade A": {"count": grade_a, "percentage": grade_a_pct},
            "URS": {"count": urs, "percentage": urs_pct},
            "Rejected": {"count": rejected, "percentage": rejected_pct}
        },
        "overall_result": overall_result,
        "quality_summary": quality_summary,
        "annotated_image_filename": out_filename,
        "annotated_image_path": out_path,
        "detections": items
    }


def create_annotated_collage(annotated_paths, max_cols=3, target_w=640, target_h=480):
    """
    Creates a composite multi-angle visual collage image from a list of annotated image paths.
    """
    if not annotated_paths:
        return None
    if len(annotated_paths) == 1:
        return annotated_paths[0]

    n = len(annotated_paths)
    cols = min(n, max_cols)
    rows = (n + cols - 1) // cols

    cell_w, cell_h = target_w, target_h
    collage = np.zeros((rows * cell_h, cols * cell_w, 3), dtype=np.uint8)

    for idx, path in enumerate(annotated_paths):
        r = idx // cols
        c = idx % cols
        img = cv2.imread(path)
        if img is None:
            continue
        resized = cv2.resize(img, (cell_w, cell_h))
        # Draw header badge
        badge_text = f"Sample / Angle #{idx + 1}"
        cv2.rectangle(resized, (0, 0), (220, 32), (15, 81, 50), -1)
        cv2.putText(
            resized, badge_text, (10, 22),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA
        )

        y_start = r * cell_h
        x_start = c * cell_w
        collage[y_start:y_start + cell_h, x_start:x_start + cell_w] = resized

    os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
    collage_filename = f"annotated_collage_{uuid.uuid4().hex}.jpg"
    collage_path = os.path.join(Config.OUTPUT_FOLDER, collage_filename)
    cv2.imwrite(collage_path, collage)
    return collage_path


def evaluate_multiple_onion_images(image_paths, yolo_conf=None, classifier_conf=None):
    """
    Evaluates 1 to any number of onion images (from different angles or sample batches):
    1. Runs YOLO detection separately on each image.
    2. Collects ALL onion crops from all images first.
    3. Runs classifier.classify_batch(all_crops) ONLY ONCE (Global Batch Classification).
    4. Maps predictions back to their correct image and detection.
    5. Produces per-image results, consolidated grading summary, and annotated overview collage.
    """
    if not image_paths:
        raise ValueError("At least one image path must be provided for evaluation.")

    pipeline_start = time.perf_counter()
    if yolo_conf is None:
        yolo_conf = Config.YOLO_CONFIDENCE_THRESHOLD
    if classifier_conf is None:
        classifier_conf = Config.CLASSIFIER_CONFIDENCE_THRESHOLD

    detector = OnionDetector()
    classifier = OnionClassifier()

    parsed_images = []
    all_crops = []

    # Step 1: Run YOLO detection separately on each image and collect crops
    yolo_start = time.perf_counter()
    for order_idx, img_path in enumerate(image_paths, start=1):
        image = cv2.imread(img_path)
        if image is None:
            raise ValueError(f"Could not read image at path: {img_path}")

        raw_detections = detector.detect(image, conf_threshold=yolo_conf)

        valid_detections = []
        start_crop_idx = len(all_crops)
        for det in raw_detections:
            x1, y1, x2, y2 = det["box"]
            crop = image[y1:y2, x1:x2]
            if crop is not None and crop.size > 0:
                valid_detections.append(det)
                all_crops.append(crop)
        end_crop_idx = len(all_crops)

        parsed_images.append({
            "order_idx": order_idx,
            "img_path": img_path,
            "image": image,
            "valid_detections": valid_detections,
            "crop_slice": (start_crop_idx, end_crop_idx)
        })
    yolo_time = time.perf_counter() - yolo_start

    # Step 2: Global batch classification ONLY ONCE across all collected crops
    cls_start = time.perf_counter()
    all_predictions = classifier.classify_batch(all_crops, conf_threshold=classifier_conf)
    cls_time = time.perf_counter() - cls_start

    # Step 3: Map predictions back to their correct image/detection and annotate
    per_image_results = []
    all_detections = []
    total_class_counts = Counter()
    global_onion_idx = 1

    for item in parsed_images:
        order_idx = item["order_idx"]
        img_path = item["img_path"]
        image = item["image"]
        valid_detections = item["valid_detections"]
        start_idx, end_idx = item["crop_slice"]
        img_predictions = all_predictions[start_idx:end_idx]

        _h, w = image.shape[:2]
        annotated_image = image.copy()

        items = []
        class_counts = Counter()
        tagged_detections = []

        for local_idx, (det, (class_name, cls_conf, _prob_dict)) in enumerate(zip(valid_detections, img_predictions), start=1):
            x1, y1, x2, y2 = det["box"]
            class_counts[class_name] += 1
            total_class_counts[class_name] += 1

            # Save item details (both for local image and tagged global detections)
            det_info = {
                "onion_number": local_idx,
                "class_name": class_name,
                "classification_confidence": cls_conf,
                "detection_confidence": det["confidence"],
                "bounding_box": [x1, y1, x2, y2]
            }
            items.append(det_info)

            det_copy = dict(det_info)
            det_copy["image_order"] = order_idx
            det_copy["onion_number"] = global_onion_idx
            global_onion_idx += 1
            tagged_detections.append(det_copy)
            all_detections.append(det_copy)

            # Draw bounding box & tag
            color = CLASS_COLORS_BGR.get(class_name, (50, 180, 50))
            cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 3)

            # Label badge
            label = f"#{local_idx} {class_name} {int(cls_conf * 100)}%"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.55
            thickness = 2
            (tw, th), _baseline = cv2.getTextSize(label, font, font_scale, thickness)

            badge_y1 = max(0, y1 - th - 10)
            badge_y2 = y1
            badge_x2 = min(w, x1 + tw + 10)

            # Draw filled background badge for contrast
            cv2.rectangle(annotated_image, (x1, badge_y1), (badge_x2, badge_y2), color, -1)
            # Text in white
            cv2.putText(
                annotated_image,
                label,
                (x1 + 5, badge_y2 - 5),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA
            )

        # Save annotated output image
        os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
        out_filename = f"annotated_{uuid.uuid4().hex}.jpg"
        out_path = os.path.join(Config.OUTPUT_FOLDER, out_filename)
        cv2.imwrite(out_path, annotated_image)

        # Compute per-image metrics
        total_onions_img = len(items)
        h_cnt = class_counts.get("Healthy", 0)
        d_cnt = class_counts.get("Damaged", 0)
        r_cnt = class_counts.get("Rotten", 0)
        s_cnt = class_counts.get("Sprouted", 0)
        u_cnt = class_counts.get("Uncertain", 0)

        h_pct = round((h_cnt / total_onions_img * 100) if total_onions_img else 0, 1)
        d_pct = round((d_cnt / total_onions_img * 100) if total_onions_img else 0, 1)
        r_pct = round((r_cnt / total_onions_img * 100) if total_onions_img else 0, 1)
        s_pct = round((s_cnt / total_onions_img * 100) if total_onions_img else 0, 1)
        u_pct = round((u_cnt / total_onions_img * 100) if total_onions_img else 0, 1)

        g_a = h_cnt
        u_rs = d_cnt
        rej = r_cnt + s_cnt

        g_a_pct = round((g_a / total_onions_img * 100) if total_onions_img else 0, 1)
        u_rs_pct = round((u_rs / total_onions_img * 100) if total_onions_img else 0, 1)
        rej_pct = round((rej / total_onions_img * 100) if total_onions_img else 0, 1)

        per_image_results.append({
            "image_order": order_idx,
            "original_image_path": img_path,
            "original_filename": os.path.basename(img_path),
            "annotated_image_path": out_path,
            "annotated_image_filename": out_filename,
            "annotated_url": f"/outputs/{out_filename}",
            "total_onions": total_onions_img,
            "classes": {
                "Healthy": {"count": h_cnt, "percentage": h_pct},
                "Damaged": {"count": d_cnt, "percentage": d_pct},
                "Rotten": {"count": r_cnt, "percentage": r_pct},
                "Sprouted": {"count": s_cnt, "percentage": s_pct},
                "Uncertain": {"count": u_cnt, "percentage": u_pct}
            },
            "grades": {
                "Grade A": {"count": g_a, "percentage": g_a_pct},
                "URS": {"count": u_rs, "percentage": u_rs_pct},
                "Rejected": {"count": rej, "percentage": rej_pct}
            },
            "detections": tagged_detections
        })

    total_images = len(image_paths)
    total_onions = len(all_detections)
    healthy_count = total_class_counts.get("Healthy", 0)
    damaged_count = total_class_counts.get("Damaged", 0)
    rotten_count = total_class_counts.get("Rotten", 0)
    sprouted_count = total_class_counts.get("Sprouted", 0)
    uncertain_count = total_class_counts.get("Uncertain", 0)

    # Aggregated percentages
    healthy_pct = round((healthy_count / total_onions * 100) if total_onions else 0, 1)
    damaged_pct = round((damaged_count / total_onions * 100) if total_onions else 0, 1)
    rotten_pct = round((rotten_count / total_onions * 100) if total_onions else 0, 1)
    sprouted_pct = round((sprouted_count / total_onions * 100) if total_onions else 0, 1)
    uncertain_pct = round((uncertain_count / total_onions * 100) if total_onions else 0, 1)

    # Aggregated Grading mapping
    # Uncertain remains separate and is not assigned to any grade
    grade_a = healthy_count
    urs = damaged_count
    rejected = rotten_count + sprouted_count

    grade_a_pct = round((grade_a / total_onions * 100) if total_onions else 0, 1)
    urs_pct = round((urs / total_onions * 100) if total_onions else 0, 1)
    rejected_pct = round((rejected / total_onions * 100) if total_onions else 0, 1)

    if total_onions == 0:
        overall_result = "No Onions Detected"
    elif grade_a_pct >= 75:
        overall_result = "Grade A - Premium Quality"
    elif (grade_a_pct + urs_pct) >= 70:
        overall_result = "URS Standard - Commercial Quality"
    else:
        overall_result = "High Rejection - Substandard Batch"

    if total_images == 1:
        quality_summary = (
            f"The AI system detected {total_onions} onions. "
            f"{healthy_count} onions were classified as Healthy ({healthy_pct}%), "
            f"{damaged_count} as Damaged ({damaged_pct}%), "
            f"{rotten_count} as Rotten ({rotten_pct}%) and "
            f"{sprouted_count} as Sprouted ({sprouted_pct}%). "
            f"Based on official procurement grading standards, "
            f"{grade_a} onions were categorized as Grade A, "
            f"{urs} as URS and {rejected} as Rejected."
        )
    else:
        quality_summary = (
            f"The AI system evaluated {total_images} sample images/angles across the batch and detected a total of {total_onions} onions. "
            f"Across all evaluated perspectives, {healthy_count} onions were classified as Healthy ({healthy_pct}%), "
            f"{damaged_count} as Damaged ({damaged_pct}%), "
            f"{rotten_count} as Rotten ({rotten_pct}%) and "
            f"{sprouted_count} as Sprouted ({sprouted_pct}%). "
            f"Based on official procurement grading standards, "
            f"{grade_a} onions were categorized as Grade A, "
            f"{urs} as URS and {rejected} as Rejected."
        )

    # Create collage for primary display if multiple images, else use the single annotated image
    annotated_paths = [img["annotated_image_path"] for img in per_image_results]
    if total_images > 1:
        primary_annotated_path = create_annotated_collage(annotated_paths)
    else:
        primary_annotated_path = annotated_paths[0]

    total_pipeline_time = time.perf_counter() - pipeline_start
    print(
        f"[AI Pipeline Timing] Images: {total_images} | Total Onions: {total_onions} | "
        f"YOLO Total: {yolo_time:.3f}s | Global Classifier Batch: {cls_time:.3f}s | "
        f"Total Pipeline: {total_pipeline_time:.3f}s"
    )

    return {
        "total_images": total_images,
        "total_onions": total_onions,
        "classes": {
            "Healthy": {"count": healthy_count, "percentage": healthy_pct},
            "Damaged": {"count": damaged_count, "percentage": damaged_pct},
            "Rotten": {"count": rotten_count, "percentage": rotten_pct},
            "Sprouted": {"count": sprouted_count, "percentage": sprouted_pct},
            "Uncertain": {"count": uncertain_count, "percentage": uncertain_pct}
        },
        "grades": {
            "Grade A": {"count": grade_a, "percentage": grade_a_pct},
            "URS": {"count": urs, "percentage": urs_pct},
            "Rejected": {"count": rejected, "percentage": rejected_pct}
        },
        "overall_result": overall_result,
        "quality_summary": quality_summary,
        "primary_original_image_path": image_paths[0],
        "primary_annotated_image_path": primary_annotated_path,
        "primary_annotated_image_filename": os.path.basename(primary_annotated_path),
        "per_image_results": per_image_results,
        "detections": all_detections
    }
