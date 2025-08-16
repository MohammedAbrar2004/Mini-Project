import logging
from typing import List, Tuple
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Try to load an NLI cross-encoder for entailment/contradiction
try:
    from sentence_transformers import CrossEncoder  # type: ignore
    nli_model = CrossEncoder('cross-encoder/nli-deberta-v3-base')
    NLI_AVAILABLE = True
except Exception as e:
    logger.warning(f"NLI CrossEncoder unavailable, using heuristic stance detection. Reason: {e}")
    nli_model = None
    NLI_AVAILABLE = False

NEGATION_TOKENS = {"not", "no", "never", "without", "false", "deny", "denies", "refute", "refutes", "debunk", "myth"}


def _has_negation(text: str) -> bool:
    words = {w.strip('.,!?;:"\'').lower() for w in text.split()}
    return any(tok in words for tok in NEGATION_TOKENS)


def _classify_stance(claim: str, text: str) -> float:
    """
    Return stance score in [-1, 1]: >0 support, <0 contradict, ~0 neutral.
    Prefer NLI if available; otherwise use negation-aware heuristic with similarity.
    """
    if NLI_AVAILABLE and nli_model is not None:
        try:
            scores = nli_model.predict([(claim, text)])  # shape: [3] for NLI
            # Heuristic: map indices by typical order [contradiction, entailment, neutral]
            if len(scores.shape) == 1 and scores.shape[0] == 3:
                c, e, n = float(scores[0]), float(scores[1]), float(scores[2])
            else:
                # Fallback: treat scalar/regression as support probability
                c, e, n = 0.0, float(scores[0]) if hasattr(scores, '__len__') else float(scores), 0.0
            if e >= c and e >= n:
                return min(1.0, e)
            if c >= e and c >= n:
                return max(-1.0, -c)
            return 0.0
        except Exception as e:
            logger.warning(f"NLI prediction failed, using heuristic: {e}")

    # Heuristic fallback: combine cosine similarity and negation mismatch
    claim_neg = _has_negation(claim)
    text_neg = _has_negation(text)
    # Similarity for direction scaling
    # encode short text to avoid heavy compute
    claim_emb = model.encode(claim[:512], convert_to_tensor=True)
    text_emb = model.encode(text[:1024], convert_to_tensor=True)
    sim = float(util.cos_sim(claim_emb, text_emb)[0])  # [-1, 1] but generally [0,1]

    if claim_neg != text_neg:
        # Strong contradiction when negation polarity differs and content is similar
        return -min(1.0, max(0.0, sim))
    # Otherwise treat as supporting if reasonably similar
    if sim > 0.6:
        return min(1.0, sim)
    if sim < 0.4:
        return -min(1.0, 0.5 * (0.4 - sim))  # slight contradiction tendency when far
    return 0.0


def _is_duplicate(title_a: str, title_b: str) -> bool:
    from difflib import SequenceMatcher
    return SequenceMatcher(a=title_a.lower(), b=title_b.lower()).ratio() >= 0.92


def match_articles(claim: str, articles: List[dict]) -> Tuple[List[dict], List[dict]]:
    if not articles:
        logger.warning("No articles provided to match.")
        return [], []

    seen_titles: List[str] = []
    support: List[dict] = []
    contradict: List[dict] = []

    for article in articles:
        content = article.get('content', article.get('snippet', '')) or ''
        title = article.get('title', '') or ''
        text = f"{title} {content}".strip()
        if not text:
            continue

        # Deduplicate near-identical titles
        if any(_is_duplicate(title, t) for t in seen_titles):
            continue

        stance_score = _classify_stance(claim, text)

        # Compute similarity for reference and weighting
        claim_embedding = model.encode(claim[:512], convert_to_tensor=True)
        embedding = model.encode(text[:1024], convert_to_tensor=True)
        sim_score = float(util.cos_sim(claim_embedding, embedding)[0])

        article["similarity_score"] = round(sim_score, 4)
        article["stance_score"] = round(stance_score, 4)

        logger.info(f"[MATCHER] '{title[:50]}...' → sim: {sim_score:.4f}, stance: {stance_score:.3f}")

        if stance_score > 0.2:
            support.append(article)
            seen_titles.append(title)
        elif stance_score < -0.2:
            contradict.append(article)
            seen_titles.append(title)
        else:
            # Keep neutral only if very similar to help later decisions
            if sim_score >= 0.7:
                support.append(article)
                seen_titles.append(title)

    if not support and not contradict:
        logger.warning("[MATCHER] No strong matches — returning top-N closest articles instead")
        # Sort by similarity and return a few as supporting context
        articles.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)
        return articles[:5], []

    return support, contradict
