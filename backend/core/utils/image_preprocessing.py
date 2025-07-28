from PIL import Image, ImageEnhance, ImageFilter
import logging


class OCRImagePreprocessor:
    """
    Simple image preprocessing for improved OCR performance.
    Clean implementation focused on core functionality.
    """
    def __init__(self):
        self.default_contrast = 1.3
        self.default_sharpness = 1.2

    def _ensure_grayscale(self, image: Image.Image) -> Image.Image:
        """Convert image to grayscale if not already."""
        if image.mode != 'L':
            return image.convert('L')
        return image

    def preprocess_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Basic preprocessing to improve OCR accuracy.
        """
        try:
            image = self._ensure_grayscale(image)

            # Enhance contrast
            contrast_enhancer = ImageEnhance.Contrast(image)
            image = contrast_enhancer.enhance(self.default_contrast)

            # Sharpen image
            sharpness_enhancer = ImageEnhance.Sharpness(image)
            image = sharpness_enhancer.enhance(self.default_sharpness)

            # Reduce noise
            image = image.filter(ImageFilter.MedianFilter(size=3))

            return image

        except Exception as e:
            logging.error(f"[OCR Preprocessor] Error during preprocess_for_ocr: {e}")
            return image

    def preprocess_quick(self, image: Image.Image) -> Image.Image:
        """
        Quick preprocessing for basic OCR improvement.
        """
        try:
            image = self._ensure_grayscale(image)

            contrast_enhancer = ImageEnhance.Contrast(image)
            image = contrast_enhancer.enhance(1.2)

            return image

        except Exception as e:
            logging.error(f"[OCR Preprocessor] Error during preprocess_quick: {e}")
            return image

    def get_preprocessing_info(self) -> dict:
        """
        Get information about available preprocessing capabilities.
        """
        return {
            "available_methods": ["preprocess_for_ocr", "preprocess_quick"],
            "features": [
                "Grayscale conversion",
                "Contrast enhancement",
                "Image sharpening",
                "Noise reduction (median filter)"
            ],
            "default_settings": {
                "contrast_factor": self.default_contrast,
                "sharpness_factor": self.default_sharpness
            }
        }
