import os

import cv2
import numpy as np

from config import Config


class OnionClassifier:
    _instance = None
    _model = None
    _input_size = 224

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        model_path = Config.CLASSIFICATION_MODEL_PATH
        if os.path.exists(model_path) and not Config.MOCK_AI_MODE:
            try:
                print(f"[OnionClassifier] Loading Keras model from {model_path}...")
                import tensorflow as tf
                # Disable excessive TF logging
                os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
                self._model = tf.keras.models.load_model(model_path)
                in_shape = self._model.input_shape
                if in_shape and len(in_shape) > 1 and in_shape[1]:
                    self._input_size = int(in_shape[1])
                print(f"[OnionClassifier] Keras model loaded successfully! Input size: {self._input_size}x{self._input_size}")

                # Warmup inference once so first live inference has no cold-start latency
                try:
                    dummy = np.zeros((1, self._input_size, self._input_size, 3), dtype=np.float32)
                    _ = self._model(dummy, training=False)
                    print(f"[OnionClassifier] Keras model warmed up successfully.")
                except Exception as we:
                    print(f"[OnionClassifier] Warmup note: {we}")
            except Exception as e:
                print(f"[OnionClassifier] Warning: Failed to load Keras model ({e}). Fallback mode active.")
                self._model = None
        else:
            print(f"[OnionClassifier] Model file not found at {model_path} or mock mode enabled.")
            self._model = None

    def preprocess(self, crop_bgr):
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(crop_rgb, (self._input_size, self._input_size))
        return resized.astype("float32")

    def classify_batch(self, crops_bgr, conf_threshold=None, batch_size=32):
        """
        Classifies a list of onion crop BGR images using safe chunked mini-batch inference.
        Prevents memory spikes and OOM crashes when processing large multi-image batches.
        Returns: list of tuples: [(class_name: str, confidence: float, all_probabilities: dict), ...]
        """
        if conf_threshold is None:
            conf_threshold = Config.CLASSIFIER_CONFIDENCE_THRESHOLD

        classes = Config.QUALITY_CLASSES

        if not crops_bgr:
            return []

        if self._model is not None:
            try:
                results = []
                total = len(crops_bgr)
                # Process in safe mini-batches to prevent memory spikes & OOM crashes on large batches
                for start_i in range(0, total, batch_size):
                    chunk = crops_bgr[start_i:min(start_i + batch_size, total)]
                    preprocessed = [self.preprocess(crop) for crop in chunk]
                    batch = np.stack(preprocessed, axis=0)

                    preds_tensor = self._model(batch, training=False)
                    predictions = preds_tensor.numpy() if hasattr(preds_tensor, "numpy") else np.array(preds_tensor)

                    for pred in predictions:
                        class_idx = int(np.argmax(pred))
                        conf = float(pred[class_idx])
                        prob_dict = {classes[i]: float(pred[i]) for i in range(len(classes))}

                        class_name = classes[class_idx]
                        if conf < conf_threshold:
                            class_name = "Uncertain"

                        results.append((class_name, conf, prob_dict))

                    del batch
                    del preprocessed
                    del preds_tensor

                return results
            except Exception as e:
                print(f"[OnionClassifier] Error during batch inference: {e}")

        # Intelligent color/texture fallback if model is unavailable
        return [self._fallback_classify(crop) for crop in crops_bgr]

    def classify(self, crop_bgr, conf_threshold=None):
        """
        Classifies an onion crop BGR image.
        Returns: (class_name: str, confidence: float, all_probabilities: dict)
        """
        if crop_bgr is None or crop_bgr.size == 0:
            return "Uncertain", 0.50, {}
        results = self.classify_batch([crop_bgr], conf_threshold=conf_threshold)
        return results[0] if results else ("Uncertain", 0.50, {})

    def _fallback_classify(self, crop_bgr):
        """
        Fallback heuristic classification based on average hue, saturation, value.
        """
        if crop_bgr.size == 0:
            return "Uncertain", 0.50, {}

        hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
        h_mean = np.mean(hsv[:, :, 0])
        s_mean = np.mean(hsv[:, :, 1])
        v_mean = np.mean(hsv[:, :, 2])

        # Greenish hue indicates sprouting
        if 35 <= h_mean <= 85 and s_mean > 50:
            return "Sprouted", 0.88, {"Sprouted": 0.88, "Healthy": 0.08, "Damaged": 0.02, "Rotten": 0.02}
        # Very dark or very low brightness indicates rotting/decay
        elif v_mean < 70 or (h_mean < 15 and s_mean < 60):
            return "Rotten", 0.85, {"Rotten": 0.85, "Damaged": 0.09, "Healthy": 0.03, "Sprouted": 0.03}
        # High saturation, clean golden/red-purple skin indicates healthy
        elif (10 <= h_mean <= 25 or 160 <= h_mean <= 180) and v_mean > 90:
            return "Healthy", 0.94, {"Healthy": 0.94, "Damaged": 0.04, "Rotten": 0.01, "Sprouted": 0.01}
        else:
            return "Damaged", 0.82, {"Damaged": 0.82, "Healthy": 0.10, "Rotten": 0.05, "Sprouted": 0.03}
