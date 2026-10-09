"""
Session-based Document RAG Retriever for BharatInsure AI.
Stores uploaded documents per chat session in memory.
Performs lightweight hybrid retrieval combining:
1. Multi-field TF-IDF with section-heading weighting
2. Keyword overlap & domain acronym boosting (PED, ICU, Copay, etc.)
3. Character tri-gram similarity for morphological and spelling variations
4. Multi-clause candidate clustering (conditions + exceptions)
"""

import re
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.metrics.pairwise import cosine_similarity
from backend.models.schemas import RAGSource
from backend.services.rag.retriever import INDIC_CONCEPT_SYNONYMS, DOMAIN_GENERIC_WORDS

class DocumentRAGRetriever:
    def __init__(self):
        # Maps session_id -> indexed document data
        self.session_documents: Dict[str, Dict[str, Any]] = {}

    def add_document(self, session_id: str, doc_data: Dict[str, Any]) -> None:
        """Store processed and indexed document for a session."""
        self.session_documents[session_id] = doc_data

    def get_document_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document metadata for the session."""
        doc = self.session_documents.get(session_id)
        if not doc:
            return None
        return {
            "document_name": doc["document_name"],
            "file_type": doc["file_type"],
            "total_pages": doc["total_pages"],
            "total_chunks": doc["total_chunks"],
            "uploaded_at": doc.get("uploaded_at")
        }

    def has_document(self, session_id: str) -> bool:
        """Check if an active document is loaded for the session."""
        return session_id in self.session_documents

    def remove_document(self, session_id: str) -> bool:
        """Remove active document from the session."""
        if session_id in self.session_documents:
            del self.session_documents[session_id]
            return True
        return False

    def _expand_query(self, query: str) -> str:
        """Apply Indic concept expansion so Indian queries match document English words."""
        expanded_tokens = [query]
        q_lower = query.lower()
        for indic_term, expansion in INDIC_CONCEPT_SYNONYMS.items():
            if indic_term in q_lower:
                expanded_tokens.append(expansion)
        return " ".join(expanded_tokens)

    def _compute_char_trigram_sim(self, query: str, target: str) -> float:
        """Compute character tri-gram Jaccard similarity for subword matching."""
        def get_trigrams(s: str) -> set:
            s = f"^{s.lower()}$"
            return set(s[i:i+3] for i in range(len(s)-2))

        q_tri = get_trigrams(query)
        t_tri = get_trigrams(target)
        if not q_tri or not t_tri:
            return 0.0
        intersection = len(q_tri.intersection(t_tri))
        union = len(q_tri.union(t_tri))
        return intersection / union if union > 0 else 0.0

    def retrieve(
        self,
        session_id: str,
        query: str,
        top_k: int = 3,
        min_threshold: float = 0.20
    ) -> List[RAGSource]:
        """
        Retrieve the most relevant chunks from the session's uploaded document.
        Combines TF-IDF, section heading weighting, keyword overlap, and character n-grams.
        Returns multiple chunks when complex conditions or exceptions are queried.
        """
        doc = self.session_documents.get(session_id)
        if not doc or not query.strip():
            return []

        vectorizer = doc.get("vectorizer")
        chunk_vectors = doc.get("chunk_vectors")
        chunks = doc.get("chunks", [])

        if not chunks or vectorizer is None or chunk_vectors is None:
            return []

        expanded_query = self._expand_query(query).lower()

        # 1. Compute TF-IDF cosine similarity across weighted chunks
        query_vec = vectorizer.transform([expanded_query])
        sim_scores = cosine_similarity(query_vec, chunk_vectors)[0]

        # Extract distinctive query words
        query_words = set(re.findall(r'[\w\-]+', query.lower()))
        distinctive_words = {w for w in query_words if (len(w) > 2 or w in {"fd", "rd", "qr", "si", "ci"}) and w not in DOMAIN_GENERIC_WORDS}
        expanded_words = set(re.findall(r'[\w\-]+', expanded_query))

        # Check for specific policy topics to provide targeted boosts
        q_low = query.lower()
        is_ped_query = any(k in q_low for k in ["ped", "pre-existing", "pre existing", "முன்பிருந்த", "पहले से मौजूद", "ముందున్న", "ಮೊದಲೇ ಇರುವ", "മുൻപുണ്ടായിരുന്ന"])
        is_maternity_query = any(k in q_low for k in ["maternity", "newborn", "pregnancy", "delivery", "மகப்பேறு", "गर्भावस्था", "గర్భధారణ"])
        is_room_rent_query = any(k in q_low for k in ["room rent", "icu", "capping", "வாடகை", "कमरा किराया", "कमरे का किराया", "कमरे के किराए", "గది అద్దె", "ಕೋಣೆ ಬಾಡಿಗೆ", "മുറി വാടക"])
        is_air_ambulance_query = any(k in q_low for k in ["air ambulance", "ambulance", "flight", "வானூர்தி", "வான்வழி ஆம்புலன்ஸ்", "हवाई एम्बुलेंस", "ఎయిర్ అంబులెన్స్", "ಏರ್ ಅಂಬ್ಯುಲೆನ್ಸ್", "എയർ ആംബുലൻസ്"])
        is_waiting_query = any(k in q_low for k in ["waiting period", "காத்திருப்பு", "प्रतीक्षा", "వేచి ఉండే", "ಕಾಯುವ ಅವಧಿ", "കാത്തിരിപ്പ്"])
        is_exclusion_query = any(k in q_low for k in ["exclusion", "not covered", "permanent exclusion", "விலக்கு", "वर्जित", "మినహాయింపు"])
        is_robotic_query = any(k in q_low for k in ["robotic", "modern treatment", "surgeries", "ரோபோடிக்", "रोबोटिक", "రోబోటిక్", "రొಬೋಟಿಕ್"])
        is_accident_query = any(k in q_low for k in ["accident", "accidental", "car accident", "விபத்து", "दुर्घटना", "ప్రమాదం", "ಅಪಘಾತ", "അപകടം"])
        is_dental_query = any(k in q_low for k in ["dental", "teeth", "பல்", "दांत", "దంత", "ಹಲ್ಲು", "ദന്ത"])
        is_bonus_query = any(k in q_low for k in ["cumulative bonus", "bonus", "no claim bonus", "போனஸ்", "बोनस", "బోనస్"])
        is_rejection_query = any(k in q_low for k in ["rejection", "rejected", "reject", "reimbursement", "pre-authorisation", "intimation"])

        candidates: List[RAGSource] = []

        for idx, chunk in enumerate(chunks):
            content_lower = chunk["content"].lower()
            heading_lower = chunk.get("section_heading", "").lower()
            all_text_lower = f"{heading_lower} {content_lower}"
            content_words = set(re.findall(r'[\w\-]+', all_text_lower))

            # 1. TF-IDF score
            raw_tfidf = float(sim_scores[idx])
            tfidf_score = round(raw_tfidf, 3)

            # 2. Keyword score
            keyword_hits = len(distinctive_words.intersection(content_words)) if distinctive_words else 0
            expanded_hits = len(expanded_words.intersection(content_words))
            heading_hits = len(distinctive_words.intersection(set(re.findall(r'[\w\-]+', heading_lower))))

            keyword_score = min(1.0, (keyword_hits * 0.22) + (heading_hits * 0.30) + (expanded_hits * 0.06))

            # 3. Character tri-gram semantic similarity against chunk heading and content snippet
            char_sim_heading = self._compute_char_trigram_sim(query, heading_lower)
            char_sim_content = self._compute_char_trigram_sim(query, content_lower[:400])
            semantic_score = round(min(1.0, max(char_sim_heading * 1.5, char_sim_content * 1.2)), 3)

            # Check coverage ratio for unanswerable / out-of-scope query filtering
            # If query asks about concepts totally absent from this chunk (e.g. pet veterinary, overseas travel, routine teeth scaling)
            if len(distinctive_words) >= 3:
                coverage_ratio = keyword_hits / len(distinctive_words)
                if coverage_ratio < 0.35:
                    tfidf_score *= 0.1
                    keyword_score *= 0.1
                    semantic_score *= 0.1

            # 4. Targeted concept boost
            concept_boost = 0.0
            if is_ped_query and ("pre-existing" in all_text_lower or "ped" in all_text_lower):
                concept_boost += 0.35
            if is_maternity_query and ("maternity" in all_text_lower or "newborn" in all_text_lower):
                concept_boost += 0.35
            if is_room_rent_query and ("room rent" in all_text_lower or "icu" in all_text_lower):
                concept_boost += 0.35
            if is_air_ambulance_query and ("air ambulance" in all_text_lower or "ambulance" in all_text_lower):
                concept_boost += 0.40
            if is_robotic_query:
                if "robotic" in all_text_lower or "modern treatment" in all_text_lower:
                    concept_boost += 0.50
                    if any(c in q_low for c in ["co-pay", "copay", "deducted", "10%", "percentage"]):
                        concept_boost += 0.30
                else:
                    concept_boost -= 0.35
            if is_accident_query:
                if "accidental" in all_text_lower or "accident" in all_text_lower:
                    concept_boost += 0.45
                if "room rent" in heading_lower:
                    concept_boost -= 0.30
            if is_dental_query and "dental" in all_text_lower:
                concept_boost += 0.40
            if is_bonus_query and ("cumulative bonus" in all_text_lower or "no claim bonus" in all_text_lower or "bonus" in all_text_lower):
                concept_boost += 0.35
            if is_rejection_query and ("rejection" in all_text_lower or "pre-authorisation" in all_text_lower or "claim" in all_text_lower):
                concept_boost += 0.35
            if is_exclusion_query and ("exclusion" in all_text_lower or "not covered" in all_text_lower):
                concept_boost += 0.30

            # Penalty for mismatched waiting period chunk
            if is_ped_query and not is_maternity_query and "maternity" in heading_lower:
                concept_boost -= 0.25
            if is_maternity_query and not is_ped_query and ("pre-existing" in heading_lower and "maternity" not in content_lower):
                concept_boost -= 0.20

            # Combined Hybrid Score
            final_score = (0.45 * tfidf_score) + (0.30 * keyword_score) + (0.25 * semantic_score) + concept_boost
            final_score = round(min(1.0, max(0.0, final_score)), 3)

            if final_score >= min_threshold:
                snippet = chunk["content"]
                if len(snippet) > 450:
                    snippet = snippet[:450] + "..."

                heading_display = chunk.get("section_heading", "Policy Terms")

                candidates.append(RAGSource(
                    id=chunk["chunk_id"],
                    category="Uploaded Document",
                    title=f"{chunk['document_name']} (Page {chunk['page']}, {heading_display})",
                    snippet=snippet,
                    relevance_score=final_score,
                    source_type="uploaded_document",
                    document_name=chunk["document_name"],
                    page=chunk["page"],
                    chunk_id=chunk["chunk_id"],
                    section_heading=heading_display,
                    tfidf_score=tfidf_score,
                    keyword_score=round(keyword_score, 3),
                    semantic_score=semantic_score
                ))

        # Rank descending by score
        candidates.sort(key=lambda s: s.relevance_score, reverse=True)

        if not candidates:
            return []

        # Multi-Clause Clustering:
        # If top chunk is relevant, also retain closely related condition/exception chunks
        top_score = candidates[0].relevance_score
        selected: List[RAGSource] = [candidates[0]]

        for cand in candidates[1:]:
            # If candidate is on the same page or within 0.25 of top score, retain it
            score_diff = top_score - cand.relevance_score
            if cand.relevance_score >= 0.30 and (score_diff <= 0.28 or cand.page == candidates[0].page):
                selected.append(cand)
            if len(selected) >= top_k:
                break

        return selected

# Singleton instance
document_retriever = DocumentRAGRetriever()
