import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any
import logging
import os
from backend.api.config import Settings

class GrobidClient:
    """
    Simplified GROBID client for extracting academic metadata from PDFs.
    Uses processFulltextDocument to extract title, author, abstract, and references.
    """
    def __init__(self):
        self.settings = Settings()
        self.base_url = f"http://{self.settings.GROBID_HOST}:{self.settings.GROBID_PORT}"
        self.timeout = 60

    def is_available(self) -> bool:
        """Check if GROBID service is running."""
        try:
            response = requests.get(f"{self.base_url}/api/isalive", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"GROBID service unavailable: {e}")
            return False

    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract academic metadata from PDF using GROBID's processFulltextDocument.
        
        Args:
            pdf_path (str): Path to PDF file
            
        Returns:
            Dict[str, Any]: Metadata with title, author, abstract, references, appears_academic
        """
        try:
            if not self.is_available():
                return {"error": "GROBID service not available", "success": False, "source": "grobid"}

            with open(pdf_path, 'rb') as pdf_file:
                response = requests.post(
                    f"{self.base_url}/api/processFulltextDocument",
                    files={'input': pdf_file},
                    timeout=self.timeout
                )

            if response.status_code != 200:
                logging.warning(f"GROBID processing failed: {response.status_code}")
                return {"error": f"GROBID failed with status {response.status_code}", "success": False, "source": "grobid"}

            metadata = self._parse_xml(response.text)
            metadata["source"] = "grobid"
            metadata["success"] = True
            logging.info(f"GROBID processing completed for {pdf_path}")
            return metadata

        except Exception as e:
            logging.error(f"Error processing PDF with GROBID: {e}")
            return {"error": str(e), "success": False, "source": "grobid"}

    def _parse_xml(self, xml_content: str) -> Dict[str, Any]:
        """Parse TEI XML to extract title, author, abstract, references, and academic status."""
        try:
            root = ET.fromstring(xml_content)
            ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
            metadata = {}

            # Extract title
            title_elem = root.find('.//tei:titleStmt/tei:title', ns)
            if title_elem is not None and title_elem.text:
                metadata['title'] = title_elem.text.strip()

            # Extract first author
            author_elem = root.find('.//tei:sourceDesc//tei:author', ns)
            if author_elem is not None:
                forename = author_elem.find('.//tei:forename', ns)
                surname = author_elem.find('.//tei:surname', ns)
                if surname is not None:
                    metadata['author'] = f"{forename.text if forename is not None else ''} {surname.text}".strip()

            # Extract abstract
            abstract_elem = root.find('.//tei:abstract/tei:div/tei:p', ns)
            if abstract_elem is not None and abstract_elem.text:
                metadata['abstract'] = abstract_elem.text.strip()

            # Extract references
            references = []
            ref_elems = root.findall('.//tei:listBibl/tei:biblStruct', ns)
            for ref in ref_elems:
                ref_info = {}
                title_elem = ref.find('.//tei:title[@level="a"]', ns)
                if title_elem is not None and title_elem.text:
                    ref_info['title'] = title_elem.text.strip()
                if ref_info:
                    references.append(ref_info)
            metadata['references'] = references
            metadata['reference_count'] = len(references)

            # Determine academic status
            academic_indicators = [
                bool(metadata.get('abstract')),
                bool(metadata.get('author')),
                bool(metadata.get('references')),
                metadata.get('reference_count', 0) > 3
            ]
            metadata['appears_academic'] = sum(academic_indicators) >= 2

            return metadata

        except Exception as e:
            logging.error(f"Error parsing XML: {e}")
            return {}