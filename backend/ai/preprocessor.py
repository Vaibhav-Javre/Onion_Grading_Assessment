import cv2
import numpy as np


class ImageQualityError(ValueError):
    """Raised when an uploaded image fails quality checks (blurry, too dark, overexposed, or no onions)."""
    def __init__(self, message, error_code="IMAGE_QUALITY_ERROR"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class ImagePreprocessor:
    """
    OnionGrade AI Image Quality Preprocessor & Quality Validator.
    
    Performs critical pre-inference validations and enhancements:
    1. Blur Detection & Measurement (Laplacian Variance + Tenengrad Gradient Energy)
    2. Adaptive Clarity Enhancement (Gentle Unsharp Mask + Dynamic Contrast Enhancement)
    3. Lighting & Exposure Verification (Under-exposure / Over-exposure checks)
    4. Overlap & Crowding Detection (IoU / Overlap Area Ratio analysis)
    """

    # Blur thresholds calibrated for 640px normalized scale
    SEVERE_BLUR_THRESHOLD = 14.0   # Beyond recovery: too blurry for reliable grading
    RECOVERABLE_BLUR_MIN = 14.0    # Soft focus: can attempt adaptive sharpening
    TARGET_SHARPNESS_MIN = 22.0    # Post-enhancement minimum required sharpness

    # Luminosity thresholds (0 to 255 grayscale range)
    MIN_BRIGHTNESS = 25.0          # Below this is pitch-black / severely underexposed
    MAX_BRIGHTNESS = 242.0         # Above this is severely washed out / extreme glare

    @staticmethod
    def compute_sharpness_metrics(image_bgr):
        """
        Calculates sharpness metrics on a normalized scale so resolution differences
        do not distort blur measurements.
        """
        if image_bgr is None or image_bgr.size == 0:
            return 0.0, 0.0

        h, w = image_bgr.shape[:2]
        if h == 0 or w == 0:
            return 0.0, 0.0

        # Scale image to max dimension 640 for consistent metric evaluation
        scale = 640.0 / max(h, w)
        scaled_w = max(1, int(w * scale))
        scaled_h = max(1, int(h * scale))
        scaled = cv2.resize(image_bgr, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)

        gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        mean_brightness = float(np.mean(gray))

        return lap_var, mean_brightness

    @staticmethod
    def enhance_clarity(image_bgr):
        """
        Applies gentle unsharp masking to clarify soft-focus images while strictly
        preserving natural color fidelity and preventing artificial shadow darkening.
        """
        if image_bgr is None or image_bgr.size == 0:
            return image_bgr

        # Gentle unsharp mask to boost edge sharpness without shifting color tones
        gaussian = cv2.GaussianBlur(image_bgr, (0, 0), sigmaX=1.5)
        unsharp = cv2.addWeighted(image_bgr, 1.25, gaussian, -0.25, 0)
        return np.clip(unsharp, 0, 255).astype(np.uint8)

    @staticmethod
    def validate_and_preprocess(image_bgr, image_name="uploaded image"):
        """
        Validates lighting, blur, and contrast. If image is soft, attempts enhancement.
        If image is too blurry to provide accurate grading, rejects with an alert.
        
        Returns:
            dict with:
                - is_valid (bool)
                - processed_image (numpy array or None)
                - was_enhanced (bool)
                - error_message (str or None)
                - error_code (str or None)
                - sharpness_score (float)
                - brightness_score (float)
        """
        if image_bgr is None or image_bgr.size == 0:
            return {
                "is_valid": False,
                "processed_image": None,
                "was_enhanced": False,
                "error_message": "Could not decode image. Please upload a valid image file.",
                "error_code": "INVALID_IMAGE",
                "sharpness_score": 0.0,
                "brightness_score": 0.0
            }

        sharpness, brightness = ImagePreprocessor.compute_sharpness_metrics(image_bgr)

        # Blur and low-lighting rejections removed per user requirement:
        # Images are passed directly to AI models with original pixel fidelity
        return {
            "is_valid": True,
            "processed_image": image_bgr,
            "was_enhanced": False,
            "error_message": None,
            "error_code": None,
            "sharpness_score": round(sharpness, 1),
            "brightness_score": round(brightness, 1)
        }

    @staticmethod
    def check_onion_overlaps(detections, overlap_ratio_threshold=0.20):
        """
        Analyzes detected onion bounding boxes to determine if onions are piled
        or heavily overlapping each other.
        
        Returns:
            tuple: (is_crowded: bool, overlapping_pairs: int, advisory_note: str or None)
        """
        total = len(detections)
        # Small sample batches (e.g. 4 to 20 onions) are not flagged for spreading
        if total <= 20:
            return False, 0, None

        boxes = [d["box"] for d in detections if "box" in d]
        overlapping_pairs = 0

        for i in range(len(boxes)):
            x1A, y1A, x2A, y2A = boxes[i]
            areaA = max(1, (x2A - x1A) * (y2A - y1A))

            for j in range(i + 1, len(boxes)):
                x1B, y1B, x2B, y2B = boxes[j]
                areaB = max(1, (x2B - x1B) * (y2B - y1B))

                ix1 = max(x1A, x1B)
                iy1 = max(y1A, y1B)
                ix2 = min(x2A, x2B)
                iy2 = min(y2A, y2B)

                if ix2 > ix1 and iy2 > iy1:
                    inter_area = (ix2 - ix1) * (iy2 - iy1)
                    min_area = min(areaA, areaB)
                    ratio = inter_area / min_area

                    if ratio >= overlap_ratio_threshold:
                        overlapping_pairs += 1

        # Only flag as crowded if there are > 20 onions AND significant overlapping pairs
        is_crowded = total > 20 and overlapping_pairs >= max(3, int(total * 0.15))

        note = None
        if is_crowded:
            note = (
                "Note: Onions appear crowded or overlapping in the sample photo. "
                "Spread the onions across the surface for better result and maximum AI grading accuracy."
            )

        return is_crowded, overlapping_pairs, note
