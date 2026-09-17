"""
Consistency Evaluation for Story Recall
---------------------------------------
Evaluates METHOD stability across semantically equivalent recalls.

This is NOT clinical accuracy testing.
This verifies:
- IU detection stability
- Paraphrase robustness
- Core IU preservation
- G-Match consistency
"""

from statistics import mean, stdev
from StoryRecall.pipeline.story_recall_pipeline import StoryRecallPipeline


def run_consistency_eval():
    pipeline = StoryRecallPipeline(data_dir="../data")

    # IMPORTANT:
    # All variants MUST contain all 15 IUs.
    recall_variants = {
        "Variant_A_Canonical": """
        Last Monday morning Ravi went to the local market near his house to buy groceries.
        He bought vegetables, bread, and milk.
        While returning he met his neighbor and talked about the weather for a few minutes.
        After returning home he prepared breakfast, ate his meal, and left for work.
        """,

        "Variant_B_Lexical_Paraphrase": """
        On Monday morning Ravi visited a nearby market close to his home to purchase groceries.
        He picked up vegetables along with bread and milk.
        On the way back he ran into his neighbor and discussed the weather briefly.
        After getting home he made breakfast, ate, and then went to work.
        """,

        "Variant_C_Syntactic_Paraphrase": """
        Ravi, on Monday morning, went near his house to a local market.
        Groceries such as vegetables, milk, and bread were bought by him.
        While returning, a short conversation about the weather occurred with his neighbor.
        At home, breakfast was prepared, eaten, and he left for work.
        """,

        "Variant_D_Compressed_But_Complete": """
        Ravi went to a nearby market on Monday morning to buy groceries.
        He bought vegetables, bread, and milk, talked with a neighbor about the weather,
        returned home, prepared breakfast, ate, and left for work.
        """
    }

    final_scores = []
    core_recalls = []
    context_recalls = []
    gmatches = []

    print("\n========== STORY RECALL CONSISTENCY EVALUATION ==========\n")

    for label, recall_text in recall_variants.items():
        result = pipeline.score_recall(
            story_id="1",
            recall_text=recall_text
        )

        scores = result["scores"]
        summary = scores["summary"]

        final_scores.append(summary["final_score"])
        core_recalls.append(summary["core_recall"])
        context_recalls.append(summary["context_recall"])
        gmatches.append(summary["gmatch"])

        print(f"{label}")
        print(f"  Final Score    : {summary['final_score']:.4f}")
        print(f"  Core Recall    : {summary['core_recall']:.4f}")
        print(f"  Context Recall : {summary['context_recall']:.4f}")
        print(f"  G-Match        : {summary['gmatch']:.4f}")

        # IU-level diagnostics
        print("  IU Breakdown:")
        for iu, info in scores.get("iu_details", {}).items():
            status = (
                "exact" if info["score"] == 1
                else "partial" if info["score"] == 0.5
                else "miss"
            )
            print(
                f"    {iu}: {status} "
                f"(sim={info['similarity']:.2f})"
            )

        print("-" * 55)

    print("\nSTATISTICAL SUMMARY")
    print(f"  Mean Final Score : {mean(final_scores):.4f}")
    print(f"  Std Deviation    : {stdev(final_scores):.4f}")
    print(f"  Core Recall Avg  : {mean(core_recalls):.4f}")
    print(f"  Context Recall Avg : {mean(context_recalls):.4f}")
    print(f"  G-Match Avg      : {mean(gmatches):.4f}")

    print("\nEXPECTED BEHAVIOR")
    print("• Very low variance")
    print("• Core recall ≈ 1.0 across variants")
    print("• Context recall slightly lower")
    print("• No collapse under paraphrasing")
    print("\n===============================================\n")


if __name__ == "__main__":
    run_consistency_eval()