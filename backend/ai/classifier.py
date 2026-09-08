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
            cls._instance = super(OnionClassifier, cls).__new__(cls)
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
            except Exception as e:
                print(f"[OnionClassifier] Warning: Failed to load Keras model ({e}). Fallback mode active.")
                self._model = None
        else:
            print(f"[OnionClassifier] Model file not found at {model_path} or mock mode enabled.")
            self._model = None

    def classify(self, crop_bgr, conf_threshold=None):
        """
        Classifies an onion crop BGR image.
        Returns: (class_name: str, confidence: float, all_probabilities: dict)
        """
        if conf_threshold is None:
            conf_threshold = Config.CLASSIFIER_CONFIDENCE_THRESHOLD

        classes = Config.QUALITY_CLASSES

        if self._model is not None and crop_bgr.size > 0:
            try:
                crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
                resized = cv2.resize(crop_rgb, (self._input_size, self._input_size))
                img_float = resized.astype("float32")
                input_tensor = np.expand_dims(img_float, axis=0)

                predictions = self._model.predict(input_tensor, verbose=0)[0]
                class_idx = int(np.argmax(predictions))
                conf = float(predictions[class_idx])

                prob_dict = {classes[i]: float(predictions[i]) for i in range(len(classes))}

                class_name = classes[class_idx]
                if conf < conf_threshold:
                    class_name = "Uncertain"

                return class_name, conf, prob_dict
            except Exception as e:
                print(f"[OnionClassifier] Error during inference: {e}")

        # Intelligent color/texture fallback if model is unavailable
        return self._fallback_classify(crop_bgr)

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
