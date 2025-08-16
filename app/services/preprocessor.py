import logging
import re
from typing import Dict, List, Tuple

try:
    import nltk
    from nltk import pos_tag
except Exception:  # Avoid hard crash if nltk is unavailable or data missing
    nltk = None
    pos_tag = None

from langdetect import detect_langs

# Try to load spaCy lazily and tolerate absence
try:
    import spacy  # type: ignore
    _spacy_nlp = None
    def get_spacy():
        global _spacy_nlp
        if _spacy_nlp is None:
            try:
                _spacy_nlp = spacy.load("en_core_web_sm")
            except Exception:
                _spacy_nlp = None
        return _spacy_nlp
except Exception:
    spacy = None  # type: ignore
    def get_spacy():  # type: ignore
        return None

# Setup
logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Remove extra spaces and normalize text"""
    return re.sub(r'\s+', ' ', text.strip())


def extract_keywords(text: str) -> List[str]:
    """Extract nouns and verbs using POS tagging when available; fallback to simple heuristic."""
    try:
        words = text.split()
        if pos_tag is not None:
            try:
                tags = pos_tag(words)
                return [word.lower() for word, tag in tags if tag.startswith("NN") or tag.startswith("VB")]
            except Exception as e:
                logger.warning(f"POS tagging failed, falling back: {e}")
        # Fallback: keep alpha tokens longer than 3 chars
        return [w.lower() for w in words if len(w) > 3 and w.isalpha()]
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        return []


def extract_entities(text: str) -> List[Dict]:
    """Extract named entities with spaCy when available; otherwise empty."""
    nlp = get_spacy()
    if not nlp:
        return []
    try:
        doc = nlp(text)
        return [
            {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char, "confidence": 1.0}
            for ent in doc.ents
        ]
    except Exception:
        return []


def detect_language(text: str) -> Tuple[str, float]:
    """Detect language using langdetect"""
    try:
        langs = detect_langs(text)
        best = langs[0]
        return best.lang, best.prob
    except Exception:
        return "unknown", 0.0


def generate_paraphrases(text: str) -> List[str]:
    """Placeholder for paraphrasing (currently disabled)"""
    return []  # Replace with actual logic if needed


def preprocess_claim(text: str) -> Dict:
    """Main pipeline to preprocess the input claim"""
    cleaned = clean_text(text)
    lang, confidence = detect_language(cleaned)
    logger.info(f"🗣️ Language: {lang} ({confidence:.2f})")

    keywords = extract_keywords(cleaned)
    logger.info(f"📦 Keywords: {keywords}")

    entities = extract_entities(cleaned)
    logger.info(f"🏷️ Entities: {[e['text'] for e in entities]}")

    paraphrases = generate_paraphrases(cleaned)
    word_count = len(text.split())
    sentence_count = len(re.findall(r'[.!?]', cleaned))

    return {
        "original_text": text,
        "cleaned_text": cleaned,
        "detected_language": lang,
        "language_confidence": confidence,
        "entities": entities,
        "keywords": keywords,
        "intent": "general_claim",
        "paraphrases": paraphrases,
        "word_count": word_count,
        "sentence_count": sentence_count
    }
