"""
Document Text Extraction, Clause Chunking, and Lightweight Indexing for BharatInsure AI.
Supports PDF (pypdf), DOCX (python-docx), and plain text (TXT).
Extracts text with preserved page numbers, markdown tables, clause headers,
exceptions, and section titles for grounded policy Q&A.
"""

import io
import re
import time
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer

# Regex pattern to identify policy sections, clauses, exclusions, schedules, and definitions
HEADING_REGEX = re.compile(
    r'^(?:'
    r'Section\s+\d+[:\.\-]?\s*.+|'
    r'Clause\s+\d+(?:\.\d+)?[:\.\-]?\s*.+|'
    r'\d+\.\d+(?:\.\d+)?\s+[A-Za-z].+|'
    r'Schedule\s*(?:of\s*Benefits|of\s*Coverage)?[:\.\-]?\s*.+|'
    r'Exclusions?|General\s*Exclusions?|Permanent\s*Exclusions?|'
    r'Conditions?|General\s*Conditions?|Standard\s*Conditions?|'
    r'Definitions?|'
    r'Waiting\s*Periods?|Waiting\s*Period\s*Limitations?|'
    r'Policy\s*Schedule|Benefits\s*Summary'
    r')(?:\s*[:\-])?$',
    re.IGNORECASE
)

# Regex pattern for lines that introduce conditions or exceptions that must NOT be severed
EXCEPTION_PREFIX_REGEX = re.compile(
    r'^(?:Exception[:\s]|Provided\s+that|However[,:\s]|Subject\s+to|Note[:\s]|Special\s+Condition|Unless\s+specifically|Excluding[:\s]|In\s+case\s+of)',
    re.IGNORECASE
)

class DocumentProcessor:
    @staticmethod
    def extract_text_from_file(file_bytes: bytes, filename: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Extract text from PDF, DOCX, or TXT file bytes.
        Returns: (List of page dicts [{"page": int, "text": str}], total_pages)
        """
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            return DocumentProcessor._extract_pdf(file_bytes, filename)
        elif lower_name.endswith(".docx"):
            return DocumentProcessor._extract_docx(file_bytes, filename)
        elif lower_name.endswith(".txt"):
            return DocumentProcessor._extract_txt(file_bytes, filename)
        else:
            raise ValueError(f"Unsupported file format '{filename}'. Please upload a PDF (.pdf), Word (.docx), or plain text (.txt) document.")

    @staticmethod
    def _extract_pdf(file_bytes: bytes, filename: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Extract text page-by-page from PDF preserving accurate page numbers.
        Detects scanned / image-only PDFs with insufficient selectable digital text.
        """
        import pypdf
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Failed to read PDF document: {str(e)}")

        total_pages = len(reader.pages)
        if total_pages == 0:
            raise ValueError("The uploaded PDF has 0 pages.")

        pages_data = []
        total_extracted_chars = 0

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""

            clean_text = page_text.strip()
            total_extracted_chars += len(clean_text)
            if clean_text:
                pages_data.append({"page": page_idx, "text": clean_text})

        # Detect scanned/image-only PDFs (no digital text layer)
        # Never silently treat a failed extraction as successful!
        if total_extracted_chars < 50 or (total_pages > 0 and (total_extracted_chars / total_pages) < 15):
            raise ValueError(
                f"This document appears to be a scanned or image-only PDF with insufficient selectable digital text "
                f"(extracted only {total_extracted_chars} characters across {total_pages} pages). "
                f"Optical Character Recognition (OCR) is not installed in the local environment. "
                f"Please upload a searchable digital text PDF, DOCX, or TXT document."
            )

        return pages_data, total_pages

    @staticmethod
    def _extract_docx(file_bytes: bytes, filename: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Extract text from Microsoft Word (.docx) documents.
        Preserves paragraph headings, tables formatted as markdown, and explicit page breaks.
        """
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Failed to read DOCX document: {str(e)}")

        pages_data: List[Dict[str, Any]] = []
        current_page_num = 1
        current_page_lines: List[str] = []

        def flush_page():
            nonlocal current_page_lines, current_page_num
            page_content = "\n\n".join(current_page_lines).strip()
            if page_content:
                pages_data.append({"page": current_page_num, "text": page_content})
                current_page_num += 1
            current_page_lines = []

        # Iterate through paragraphs and tables in order
        for element in doc.element.body:
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

            if tag == "p":
                # Find matching paragraph
                p_text = element.text.strip() if element.text else ""
                if not p_text:
                    continue

                # Check if paragraph has heading style or bold styling
                is_heading = False
                for p in doc.paragraphs:
                    if p._element == element:
                        style_name = (p.style.name if p.style else "").lower()
                        if "heading" in style_name or "title" in style_name:
                            is_heading = True
                            p_text = f"### {p.text.strip()}"
                        else:
                            p_text = p.text.strip()
                        break

                current_page_lines.append(p_text)

                # Check for explicit hard page break in paragraph XML
                has_page_break = any(
                    br.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type") == "page"
                    for br in element.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}br")
                )
                if has_page_break:
                    flush_page()

            elif tag == "tbl":
                # Format table as Markdown table
                for table in doc.tables:
                    if table._element == element:
                        table_rows = []
                        for r_idx, row in enumerate(table.rows):
                            row_cells = [cell.text.replace("\n", " ").strip() for cell in row.cells]
                            row_line = "| " + " | ".join(row_cells) + " |"
                            table_rows.append(row_line)
                            if r_idx == 0:
                                separator = "| " + " | ".join(["---"] * len(row_cells)) + " |"
                                table_rows.append(separator)
                        if table_rows:
                            current_page_lines.append("\n".join(table_rows))
                        break

        # Flush remaining lines
        flush_page()

        total_extracted_chars = sum(len(p["text"]) for p in pages_data)
        if total_extracted_chars < 20:
            raise ValueError("The uploaded DOCX document is empty or contains no readable text.")

        # If document had no explicit page breaks and text is long, paginate logically every 2200 chars
        if len(pages_data) == 1 and len(pages_data[0]["text"]) > 2500:
            long_text = pages_data[0]["text"]
            chunk_size = 2200
            new_pages = []
            parts = [long_text[i:i + chunk_size] for i in range(0, len(long_text), chunk_size)]
            for idx, part in enumerate(parts, start=1):
                new_pages.append({"page": idx, "text": part.strip()})
            return new_pages, len(new_pages)

        return pages_data, len(pages_data)

    @staticmethod
    def _extract_txt(file_bytes: bytes, filename: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Extract text from plain text (.txt) files.
        Detects explicit page markers if present (e.g. Page 1, Page 2).
        """
        try:
            text = file_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                text = file_bytes.decode("latin-1", errors="replace").strip()
            except Exception as e:
                raise ValueError(f"Failed to decode text file: {str(e)}")

        if len(text) < 15:
            raise ValueError("The uploaded TXT document is empty or has insufficient content.")

        # Check for explicit page delimiter patterns (e.g. "--- Page 2 ---" or "=== Page 2 ===")
        page_pattern = re.compile(r'[-=]{3,}\s*Page\s+(\d+)\s*[-=]{3,}', re.IGNORECASE)
        splits = page_pattern.split(text)

        if len(splits) > 1:
            pages_data = []
            current_page = 1
            idx = 0
            while idx < len(splits):
                raw_seg = splits[idx]
                if raw_seg:
                    segment = raw_seg.strip()
                    if segment.isdigit():
                        current_page = int(segment)
                    elif segment:
                        pages_data.append({"page": current_page, "text": segment})
                        current_page += 1
                idx += 1
            if pages_data:
                return pages_data, len(pages_data)

        # Logical segmentation if long
        chunk_page_size = 2200
        if len(text) > chunk_page_size:
            pages_data = []
            parts = [text[i:i + chunk_page_size] for i in range(0, len(text), chunk_page_size)]
            for idx, part in enumerate(parts, start=1):
                pages_data.append({"page": idx, "text": part.strip()})
            return pages_data, len(pages_data)
        else:
            return [{"page": 1, "text": text}], 1

    @staticmethod
    def _find_heading_in_text(text: str) -> Optional[str]:
        """Detect the first or most prominent section/clause heading in a text snippet."""
        lines = text.split("\n")
        for line in lines:
            line_clean = line.strip().replace("#", "").strip()
            if HEADING_REGEX.match(line_clean):
                return line_clean
        return None

    @staticmethod
    def chunk_document(pages_data: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        """
        Split document text into meaningful clause-aware chunks retaining exact page numbers
        and active section headings.
        Target chunk size: ~1000-1400 characters (~150-250 words) with ~180 char overlap.
        Preserves conditions together with their exceptions.
        """
        chunks: List[Dict[str, Any]] = []
        slug = re.sub(r'[^a-zA-Z0-9]', '_', filename)[:20].lower()
        chunk_idx = 0

        target_chunk_chars = 1100
        overlap_chars = 180

        # Global active section heading tracker across pages
        current_section_heading = "General Policy Overview"

        for page_item in pages_data:
            page_num = page_item["page"]
            text = page_item["text"]

            # First, check if page declares a top heading
            page_heading = DocumentProcessor._find_heading_in_text(text)
            if page_heading:
                current_section_heading = page_heading

            # Split text by paragraphs / clauses
            raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if not raw_paragraphs:
                raw_paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
            if not raw_paragraphs:
                raw_paragraphs = [text]

            # Merge exception paragraphs with preceding conditions so they are never severed!
            cohesive_blocks: List[str] = []
            for p in raw_paragraphs:
                if cohesive_blocks and EXCEPTION_PREFIX_REGEX.match(p):
                    # Attach exception directly to previous condition block
                    cohesive_blocks[-1] = cohesive_blocks[-1] + "\n\n" + p
                else:
                    cohesive_blocks.append(p)

            current_chunk = ""
            chunk_heading = current_section_heading

            for block in cohesive_blocks:
                # Update chunk heading if this block is a new heading
                block_heading = DocumentProcessor._find_heading_in_text(block)
                if block_heading:
                    current_section_heading = block_heading
                    chunk_heading = block_heading

                if len(current_chunk) + len(block) <= target_chunk_chars:
                    current_chunk = (current_chunk + "\n\n" + block).strip() if current_chunk else block
                else:
                    if current_chunk:
                        chunk_idx += 1
                        chunks.append({
                            "document_name": filename,
                            "page": page_num,
                            "chunk_id": f"{slug}_p{page_num}_c{chunk_idx}",
                            "section_heading": chunk_heading,
                            "content": current_chunk
                        })
                        # Overlap: take trailing sentences or characters
                        overlap = current_chunk[-overlap_chars:].strip()
                        current_chunk = (overlap + "\n\n" + block).strip()
                        chunk_heading = current_section_heading
                    else:
                        # Single block exceeds target_chunk_chars: slice with overlap
                        for i in range(0, len(block), target_chunk_chars - overlap_chars):
                            chunk_idx += 1
                            slice_text = block[i:i + target_chunk_chars].strip()
                            if slice_text:
                                chunks.append({
                                    "document_name": filename,
                                    "page": page_num,
                                    "chunk_id": f"{slug}_p{page_num}_c{chunk_idx}",
                                    "section_heading": chunk_heading,
                                    "content": slice_text
                                })
                        current_chunk = ""

            if current_chunk and len(current_chunk.strip()) > 25:
                chunk_idx += 1
                chunks.append({
                    "document_name": filename,
                    "page": page_num,
                    "chunk_id": f"{slug}_p{page_num}_c{chunk_idx}",
                    "section_heading": chunk_heading,
                    "content": current_chunk.strip()
                })

        # Fallback if no chunks were formed
        if not chunks and pages_data:
            chunks.append({
                "document_name": filename,
                "page": 1,
                "chunk_id": f"{slug}_p1_c1",
                "section_heading": "Policy Overview",
                "content": pages_data[0]["text"][:1000]
            })

        return chunks

    @staticmethod
    def process_and_index_document(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Complete processing pipeline:
        Extraction -> Clause-aware Chunking -> Section Weighting -> TF-IDF Vectorization
        """
        pages_data, total_pages = DocumentProcessor.extract_text_from_file(file_bytes, filename)
        chunks = DocumentProcessor.chunk_document(pages_data, filename)

        if not chunks:
            raise ValueError(f"Could not extract meaningful content from '{filename}'.")

        # Multi-field text representation weighting section headings heavily:
        # Heading (x2) + Content (x1)
        weighted_chunk_texts = []
        for c in chunks:
            heading = c.get("section_heading", "")
            content = c.get("content", "")
            weighted = f"{heading} {heading} {content}".lower()
            weighted_chunk_texts.append(weighted)

        # Build TF-IDF vectorizer with (1, 2) word n-grams
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words='english',
            min_df=1
        )
        chunk_vectors = vectorizer.fit_transform(weighted_chunk_texts)

        lower_name = filename.lower()
        file_type = "pdf" if lower_name.endswith(".pdf") else ("docx" if lower_name.endswith(".docx") else "txt")

        return {
            "document_name": filename,
            "file_type": file_type,
            "total_pages": total_pages,
            "total_chunks": len(chunks),
            "chunks": chunks,
            "vectorizer": vectorizer,
            "chunk_vectors": chunk_vectors,
            "uploaded_at": time.time()
        }
