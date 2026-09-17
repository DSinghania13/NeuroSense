"""
Picture Description – Consistency Evaluation
-------------------------------------------
Measures cognitive stability across utterances.

Validates:
- Concept persistence
- Redundancy vs fragmentation
- Utterance-to-IU coherence

NOT a clinical diagnosis.
This is method-level stability testing.
"""

import os
import numpy as np
from collections import defaultdict

from PictureDescription.pipeline.picture_description_pipeline import (
    PictureDescriptionPipeline
)


# ======================================================================
# Consistency Evaluator
# ======================================================================

class ConsistencyEvaluator:
    """
    Measures how stably concepts are expressed across utterances.
    """

    def evaluate(self, iu_table, utterances):
        """
        Args:
            iu_table: IU scoring table from IUScorer
            utterances: list of segmented utterances

        Returns:
            dict of stability metrics
        """

        # Collect all matched IU → utterance mappings
        matched = [
            (iu, row["matched_utterance"])
            for iu, row in iu_table.items()
            if row["matched_utterance"] is not None
        ]

        if not matched:
            return {
                "redundancy": 0.0,
                "dispersion": 0.0,
                "repeated_utterances": 0
            }

        utterance_map = defaultdict(list)

        for iu, utt in matched:
            utterance_map[utt].append(iu)

        # 1. Redundancy:
        #    How many IUs are mapped to the same utterance on average
        redundancy = np.mean([len(v) for v in utterance_map.values()])

        # 2. Dispersion:
        #    How spread-out IUs are across utterances
        #    High = concepts distributed across many utterances (healthy)
        dispersion = len(utterance_map) / max(len(matched), 1)

        # 3. Repeated utterances:
        #    Count of utterances that carry multiple IUs
        repeated_utterances = sum(1 for v in utterance_map.values() if len(v) > 1)

        return {
            "redundancy": round(float(redundancy), 3),
            "dispersion": round(float(dispersion), 3),
            "repeated_utterances": repeated_utterances
        }


# ======================================================================
# Evaluation Runner
# ======================================================================

def run_consistency_eval():

    # ------------------------------------------------------------------
    # Robust path resolution
    # ------------------------------------------------------------------
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")

    pipeline = PictureDescriptionPipeline(data_dir=data_dir)
    consistency = ConsistencyEvaluator()

    # ------------------------------------------------------------------
    # Controlled test variants
    # ------------------------------------------------------------------
    variants = {
        "A_full_description": """
        The boy is standing on a stool reaching for cookies from a jar.
        The girl is asking him for one.
        Water is overflowing from the sink and spilling onto the floor.
        The mother is washing dishes and not paying attention.
        """,

        "B_paraphrase_description": """
        A child climbs on a chair to grab cookies while his sister waits.
        The sink is running over and water is on the floor.
        Their mother is busy with dishes and seems distracted.
        """,

        "C_core_only": """
        A boy is standing on a stool reaching for cookies.
        Water is overflowing from the sink.
        The mother is distracted.
        """,

        "D_fragmented": """
        Boy on stool.
        Cookies.
        Water everywhere.
        Mother washing dishes.
        """,

        "E_sparse": """
        There is water on the floor.
        """,

        "F_off_topic": """
        The family is having dinner together in the evening.
        """
    }

    print("\n========== PICTURE DESCRIPTION CONSISTENCY EVALUATION ==========\n")

    for label, description in variants.items():
        print(label)
        print("-" * 72)

        result = pipeline.score_description(
            picture_id="cookie_theft",
            description_text=description
        )

        iu_table = result["details"]["iu_table"]
        utterances = result["utterances"]

        metrics = consistency.evaluate(iu_table, utterances)

        # ------------------------------------------------------------------
        # Raw
        # ------------------------------------------------------------------
        print("\nRAW DESCRIPTION:")
        print(description.strip())

        # ------------------------------------------------------------------
        # Utterances
        # ------------------------------------------------------------------
        print("\nUTTERANCES:")
        if utterances:
            for u in utterances:
                print(f" - {u}")
        else:
            print(" (no utterances detected)")

        # ------------------------------------------------------------------
        # Stability metrics
        # ------------------------------------------------------------------
        print("\nCONSISTENCY METRICS:")
        print(f"  Redundancy          : {metrics['redundancy']}")
        print(f"  Dispersion          : {metrics['dispersion']}")
        print(f"  Repeated Utterances : {metrics['repeated_utterances']}")

        # ------------------------------------------------------------------
        # Cognitive interpretation
        # ------------------------------------------------------------------
        print("\nINTERPRETATION:")
        if metrics["dispersion"] > 0.6 and metrics["redundancy"] < 2:
            print("  Stable concept tracking (Healthy-like)")
        elif metrics["dispersion"] > 0.3:
            print("  Moderate stability (MCI-like)")
        else:
            print("  Poor concept stability (Alzheimer-like)")

        print("\n" + "=" * 72 + "\n")

    print("EXPECTED BEHAVIOR:")
    print("• A > B > C > D > E > F")
    print("• Dispersion drops with cognitive decline")
    print("• Redundancy rises in Alzheimer’s")
    print("• Off-topic collapses all metrics\n")


if __name__ == "__main__":
    run_consistency_eval()