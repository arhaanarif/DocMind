import fitz
import os
from typing import Dict, Any


class PDFAnalyzer:
    def __init__(self, sample_pages: int = 5):
        self.text_threshold = 50  # Characters to consider as having text
        self.text_density_threshold = 0.1  # Characters per page ratio
        self.sample_pages = sample_pages

    def detect_pdf_type(self, pdf_path: str) -> Dict[str, Any]:
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"File not found: {pdf_path}")

            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            pages_to_sample = min(self.sample_pages, total_pages)

            total_text_chars = 0
            pages_with_text = 0
            pages_with_images = 0

            sample_indices = list(range(pages_to_sample))
            if total_pages > self.sample_pages:
                # Optionally sample a middle and end page for diversity
                sample_indices += [total_pages // 2, total_pages - 1]
                sample_indices = list(set(sample_indices))

            for page_num in sample_indices:
                page = doc[page_num]
                page_text = page.get_text().strip()
                if len(page_text) > self.text_threshold:
                    pages_with_text += 1
                    total_text_chars += len(page_text)

                if len(page.get_images(full=True)) > 0:
                    pages_with_images += 1

            doc.close()

            pages_sampled = len(sample_indices)
            text_density = total_text_chars / pages_sampled if pages_sampled > 0 else 0
            text_page_ratio = pages_with_text / pages_sampled if pages_sampled > 0 else 0
            image_page_ratio = pages_with_images / pages_sampled if pages_sampled > 0 else 0

            # Decision heuristics
            is_digital = (
                text_density > self.text_density_threshold * 1000
                and text_page_ratio > 0.6
            )

            if image_page_ratio > 0.8 and pages_with_text == 0:
                likely_scanned = True
            else:
                likely_scanned = not is_digital

            return {
                "pdf_type": "digital" if not likely_scanned else "scanned",
                "confidence": round(min(text_page_ratio * 100 + (image_page_ratio * -50), 95), 2),
                "total_pages": total_pages,
                "pages_sampled": pages_sampled,
                "pages_with_text": pages_with_text,
                "pages_with_images": pages_with_images,
                "avg_text_density": round(text_density, 2),
                "text_page_ratio": round(text_page_ratio, 2),
                "image_page_ratio": round(image_page_ratio, 2),
            }

        except Exception as e:
            return {
                "pdf_type": "unknown",
                "confidence": 0,
                "error": str(e)
            }

