"""
Free Speech Pipeline
----------------------------------------------
End-to-end pipeline for free speech cognitive assessment.
"""

from typing import Dict, Any

from ..preprocessing.text_cleaning import clean_text
from ..preprocessing.disfluency_stats import extract_disfluency
from ..preprocessing.clause_segmenter import segment_clauses
from ..scoring.fluency_stats import compute_fluency
from ..scoring.repetition_stats import compute_repetition
from ..scoring.idea_density import compute_idea_density
from ..scoring.lexical_stats import compute_lexical_diversity
from ..scoring.syntactic_stats import compute_syntactic_stats
from ..scoring.coherence_stats import compute_coherence
from ..scoring.perplexity import compute_perplexity

from ..qc.data_quality import DataQuality
from ..scoring.scorer import FinalScorer


class FreeSpeechPipeline:
    """
    Full cognitive speech analysis pipeline
    """

    def __init__(self):
        self.qc = DataQuality()
        self.scorer = FinalScorer()

    # --------------------------------------------------
    def analyze(
        self,
        raw_text: str,
        duration_sec: float
    ) -> Dict[str, Any]:

        # -----------------------------
        # 1. CLEANING
        # -----------------------------
        cleaned = clean_text(raw_text)

        # -----------------------------
        # 2. DISFLUENCY (RAW SIGNAL)
        # -----------------------------
        disfluency = extract_disfluency(cleaned)

        # -----------------------------
        # 3. CLAUSE SEGMENTATION
        # -----------------------------
        clauses = segment_clauses(cleaned)

        # -----------------------------
        # 4. DATA QUALITY (QC)
        # -----------------------------
        qc_result = self.qc.evaluate(
            total_words=disfluency["clean_word_count"],
            clause_count=clauses["clause_count"],
            duration_sec=duration_sec
        )

        # -----------------------------
        # 5. CONDITIONAL FEATURES
        # -----------------------------
        if qc_result["is_valid"]:
            repetition = compute_repetition(cleaned)
            idea = compute_idea_density(cleaned, disfluency)
            ttr = compute_lexical_diversity(cleaned)
            syntax = compute_syntactic_stats(cleaned, clauses)
            coherence = compute_coherence(clauses["clauses"])
        else:
            repetition = None  # <--- Added None fallback
            idea = None
            ttr = None
            syntax = None
            coherence = None

        # -----------------------------
        # 6. FLUENCY (WPM + SPEED)
        # -----------------------------
        fluency = compute_fluency(disfluency, duration_sec)

        # -----------------------------
        # 7. PERPLEXITY (fallback always)
        # -----------------------------
        if qc_result["is_valid"]:
            perplexity = compute_perplexity(raw_text)
        else:
            perplexity = {
                "perplexity": 0.0,
                "perplexity_level": "impaired",
                "is_reliable": False,
                "evidence": {}
            }

        # -----------------------------
        # 8. FINAL SCORING
        # -----------------------------
        final_scores = self.scorer.score(
            disfluency=disfluency,
            repetition=repetition,
            idea=idea,
            ttr=ttr,
            syntax=syntax,
            coherence=coherence,
            perplexity=perplexity,
            fluency=fluency,
            duration_sec=duration_sec,
            qc=qc_result
        )

        # -----------------------------
        # 9. OUTPUT
        # -----------------------------
        return {
            "cleaned_text": cleaned,
            "qc": qc_result,

            "features": {
                "disfluency": disfluency,
                "repetition": repetition,
                "idea_density": idea,
                "lexical_diversity": ttr,
                "syntax": syntax,
                "coherence": coherence,
                "perplexity": perplexity,
                "fluency": fluency
            },

            "final_score": final_scores
        }