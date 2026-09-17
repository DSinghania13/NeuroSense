"""
Consistency Evaluation for Memory Session
-----------------------------------------
Evaluates pipeline stability across semantically equivalent memory sessions.

This verifies:
- Semantic extraction stability across different phrasing styles.
- Forgetting rate consistency when the underlying semantic drop is identical.
- Robustness against conversational padding and terse speech.
"""

from statistics import mean, stdev
from EpisodicMemory.pipeline.episodic_memory_pipeline import MemoryQAPipeline

def run_session_consistency_eval():
    pipeline = MemoryQAPipeline(data_dir="../data")

    # IMPORTANT:
    # All variants represent the EXACT same clinical semantic decay.
    # The immediate text captures the full story, the delayed text drops one semantic node.
    # The scoring engine should produce near-identical forgetting rates for all of them.
    session_variants = {
        "Variant_A_Canonical": {
            "immediate": "Ravi went to the market to buy groceries. He bought vegetables, bread, and milk. He met a neighbor, went home, and made breakfast.",
            "delayed": "Ravi went to the market to buy groceries. He bought vegetables, bread, and milk. He went home and made breakfast." # Missing neighbor node
        },

        "Variant_B_Lexical_Paraphrase": {
            "immediate": "Ravi visited a nearby bazaar to purchase supplies. He picked up veggies, a loaf of bread, and milk. He ran into his neighbor, returned to his house, and prepared his morning meal.",
            "delayed": "Ravi visited a nearby bazaar to purchase supplies. He picked up veggies, a loaf of bread, and milk. He returned to his house, and prepared his morning meal." # Missing neighbor node
        },

        "Variant_C_Fragmented_Terse": {
            "immediate": "Market. Groceries. Vegetables, bread, milk. Met neighbor. Went home. Breakfast.",
            "delayed": "Market. Groceries. Vegetables, bread, milk. Went home. Breakfast." # Missing neighbor node
        },

        "Variant_D_Conversational_Padding": {
            "immediate": "Well, let me think. I remember Ravi went to the market for groceries. Yes, he bought vegetables, bread, and some milk. Oh, and he met a neighbor before going home to make breakfast.",
            "delayed": "Let's see. Ravi went to the market to get groceries. He bought vegetables, bread, and milk. Then I believe he went home and made some breakfast." # Missing neighbor node
        }
    }

    immediate_scores = []
    delayed_scores = []
    forgetting_rates = []

    print("\n========== MEMORY SESSION CONSISTENCY EVALUATION ==========\n")

    for label, texts in session_variants.items():
        # Using your exact pipeline signature (omitting optional segments)
        result = pipeline.score_memory_session(
            story_id="1",
            immediate_text=texts["immediate"],
            delayed_text=texts["delayed"]
        )

        # Assuming the pipeline returns the same dict structure as your audio wrapper
        analysis = result.get("memory_analysis", result) # Fallback in case pipeline returns flat dict

        imm_score = analysis.get('immediate_score', 0.0)
        del_score = analysis.get('delayed_score', 0.0)
        forgetting = analysis.get('forgetting_rate', 0.0)

        immediate_scores.append(imm_score)
        delayed_scores.append(del_score)
        forgetting_rates.append(forgetting)

        print(f"{label}")
        print(f"  Immediate Text : '{texts['immediate'][:50]}...'")
        print(f"  Delayed Text   : '{texts['delayed'][:50]}...'")
        print(f"  Immediate Score: {imm_score:.4f}")
        print(f"  Delayed Score  : {del_score:.4f}")
        print(f"  Forgetting Rate: {forgetting:.4f}")
        print("-" * 60)

    print("\nSTATISTICAL SUMMARY")
    print(f"  Immediate Score Mean : {mean(immediate_scores):.4f} (Std: {stdev(immediate_scores):.4f})")
    print(f"  Delayed Score Mean   : {mean(delayed_scores):.4f} (Std: {stdev(delayed_scores):.4f})")
    print(f"  Forgetting Rate Mean : {mean(forgetting_rates):.4f} (Std: {stdev(forgetting_rates):.4f})")

    print("\nEXPECTED BEHAVIOR")
    print("• Very low standard deviation across all metrics.")
    print("• The pipeline should easily map the Paraphrase (B) to Canonical (A).")
    print("• Terse (C) shouldn't artificially inflate the forgetting rate.")
    print("• Padding (D) shouldn't artificially deflate the scores due to word count.")
    print("\n===========================================================\n")


if __name__ == "__main__":
    run_session_consistency_eval()