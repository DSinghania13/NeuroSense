"""
Picture Description – Behavioral Evaluation
-------------------------------------------
Full diagnostic evaluation of Picture Description scoring (Text Only).

Validates:
- IU semantic detection (Visual vs Inferred)
- Spatial Language analysis (Prepositions)
- Syntactic Complexity (Tree Depth)
- Utterance Segmentation & Disfluency Cleaning

NOT a clinical diagnosis. Method-level validation.
"""

import os
import logging
import warnings

# ==========================================
# 🚫 WARNING SUPPRESSION
# ==========================================
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", message="You are sending unauthenticated requests")
logging.getLogger("transformers").setLevel(logging.ERROR)

import transformers
transformers.logging.set_verbosity_error()

from PictureDescription.pipeline.picture_description_pipeline import PictureDescriptionPipeline

def print_ui_report(label, result, raw_text):
    s = result["scores"]
    d = result["details"]
    sp = result["spatial_stats"]
    u = result["utterances"]

    # Extract Syntax Stats
    syntax = u.get("syntax_stats", {})

    print(f"\n{'='*100}")
    print(f"▶️  REPORT: {label}")
    print(f"{'='*100}")

    # --- 1. TRAFFIC LIGHT SCORES ---
    print(f"\n📊 CLINICAL METRICS")
    print(f"  Final Risk Score : {s['final_score']:.4f}  (1.0=Healthy, 0.0=Severe)")
    print(f"  Content (IU)     : {s['iu_normalized']:.4f}  (Weighted: 75%)")
    print(f"  Fluency (Proc)   : {s['fluency_score']:.4f}  (Weighted: 15%)")
    print(f"  Spatial (Lang)   : {s['spatial_score']:.4f}  (Weighted: 10%)")

    # --- 2. LINGUISTIC MARKERS ---
    print(f"\n🧠 LINGUISTIC MARKERS")
    print(f"  Spatial Density  : {sp.get('spatial_density', 0.0):.2f} (Prepositions/Utt)")
    print(f"  Syntactic Depth  : {syntax.get('avg_tree_depth', 0.0):.2f} (Avg Tree Height)")
    print(f"  Disfluency       : {u['disfluency_stats'].get('disfluency_score', 0.0):.2%} (Fillers/Total)")

    # --- 3. UTTERANCE SEGMENTATION (New Section) ---
    print(f"\n🗣️  UTTERANCE SEGMENTATION (Raw vs. Cleaned)")
    print(f"  {'-'*100}")

    raw_utts = u["raw_utterances"]
    clean_utts = u["cleaned_utterances"]

    for i, (raw, clean) in enumerate(zip(raw_utts, clean_utts)):
        print(f"  {i+1}. Raw   : \"{raw}\"")
        if raw.lower() != clean:
            print(f"     Clean : \"{clean}\"  <-- (Fillers removed)")
        else:
            print(f"     Clean : [Unchanged]")

    # --- 4. IU TRACE TABLE ---
    print(f"\n📋 CONCEPTUAL TRACE (Content)")
    header = f"  {'ID':<5} | {'TYPE':<7} | {'MATCH':<10} | {'SCORE':<5} | {'EXPECTED (Template)':<30} | {'USER MATCH'}"
    print(header)
    print(f"  {'-'*100}")

    iu_table = d["iu_table"]
    sorted_ius = sorted(iu_table.items(), key=lambda x: (x[1]['iu_type'], x[0]))

    for iu_id, row in sorted_ius:
        exp = row['expected_text']
        rec = row['matched_utterance'] or "---"

        if len(exp) > 28: exp = exp[:25] + "..."
        if len(rec) > 35: rec = rec[:32] + "..."

        if row['score'] == 1.0:
            status = "✅ MATCH"
        elif row['score'] >= 0.5:
            status = "⚠️ PARA"
        else:
            status = "❌ MISS"

        print(f"  {iu_id:<5} | {row['iu_type']:<7} | {status:<10} | {row['score']:<5} | {exp:<30} | {rec}")

    # --- 5. SUMMARY ---
    missed_core = d["conceptual_summary"]["core"]["missed"]
    print(f"\n📉 MISSED CORE CONCEPTS: {len(missed_core)}")
    if missed_core:
        print(f"   {missed_core}")


def run_behavior_eval():
    if not os.path.exists("../data"):
        data_dir = "data" if os.path.exists("data") else "../data"
    else:
        data_dir = "../data"

    try:
        pipeline = PictureDescriptionPipeline(data_dir=data_dir)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return

    # ------------------------------------------------------------------
    # SCENARIOS
    # ------------------------------------------------------------------
    variants = {
        "A_Full_Description": """
        The boy is standing on a stool reaching for cookies from a jar.
        The girl is asking him for one.
        Water is overflowing from the sink and spilling onto the floor.
        The mother is washing dishes and not paying attention.
        """,

        "B_Paraphrase_Description": """
        A child climbs on a chair to grab cookies while his sister waits.
        The sink is running over and water is on the floor.
        Their mother is busy with dishes and seems distracted.
        """,

        "C_Core_Only": """
        A boy is standing on a stool reaching for cookies.
        Water is overflowing from the sink.
        The mother is distracted.
        """,

        "D_Fragmented_Disfluent": """
        Boy on... uh... stool.
        Cookies.
        Water... um... everywhere.
        Mother washing dishes.
        """,

        "E_Sparse": """
        There is water on the floor.
        """,

        "F_Off_Topic": """
        The family is having dinner together in the evening.
        """
    }

    print("\n========== PICTURE DESCRIPTION BEHAVIOR EVALUATION ==========\n")

    for label, description in variants.items():
        try:
            result = pipeline.score_description(
                picture_id="cookie_theft",
                description_text=description
            )
            print_ui_report(label, result, description)
        except Exception as e:
            print(f"❌ FAILED on {label}: {e}")

    print("\n✅ EVALUATION COMPLETE")
    print("EXPECTED TREND: A > B > C > D > E > F")

if __name__ == "__main__":
    run_behavior_eval()