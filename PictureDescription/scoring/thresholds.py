"""
IU Scoring Thresholds
--------------------
Hybrid thresholds for Picture Description & Story Recall scoring.

Includes:
- SBERT semantic gates
- Cross-Encoder NLI entailment thresholds
- Disfluency normalization
- Spatial language thresholds
- Syntactic complexity thresholds

ALL thresholds live here.
NO clinical logic lives in scorers.
"""

class IUThresholds:
    """
    Thresholds for hybrid IU + language scoring.
    """

    def __init__(
        self,

        # ==================================================
        # SBERT (Semantic Evidence)
        # ==================================================
        sbert_gate: float = 0.35,      # minimum similarity to consider IU
        sbert_strong: float = 0.60,    # strong semantic evidence
        sbert_weak: float = 0.45,      # weak but meaningful evidence

        # ==================================================
        # Cross-Encoder NLI (Logical Evidence)
        # ==================================================
        entailment_strong: float = 0.75,   # full IU credit
        entailment_weak: float = 0.50,     # partial IU credit

        # ==================================================
        # Disfluency (Fluency)
        # ==================================================
        max_disfluency_penalty: float = 0.50,
        # example: fillers / total_words capped at 0.5

        # ==================================================
        # Spatial Language (NEW)
        # ==================================================
        # Normalized over utterances
        spatial_low: float = 0.05,     # AD-like: almost no relations
        spatial_normal: float = 0.20,  # Healthy: relational descriptions

        # ==================================================
        # Syntactic Complexity (NEW)
        # ==================================================
        syntax_depth_low: float = 2.0,     # Flat S–V–O (AD)
        syntax_depth_normal: float = 4.0   # Embedded clauses (Healthy)
    ):
        # ---- SBERT ----
        self.sbert_gate = sbert_gate
        self.sbert_strong = sbert_strong
        self.sbert_weak = sbert_weak

        # ---- NLI ----
        self.entailment_strong = entailment_strong
        self.entailment_weak = entailment_weak

        # ---- Disfluency ----
        self.max_disfluency_penalty = max_disfluency_penalty

        # ---- Spatial ----
        self.spatial_low = spatial_low
        self.spatial_normal = spatial_normal

        # ---- Syntax ----
        self.syntax_depth_low = syntax_depth_low
        self.syntax_depth_normal = syntax_depth_normal