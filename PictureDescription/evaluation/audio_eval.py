"""
Final Diagnostic Suite: Picture Description (Audio + AI)
--------------------------------------------------------
Runs 5 Clinical Scenarios (A-E) through the full audio pipeline.
Validates: ASR -> Segmentation -> Syntax/Spatial Analysis -> Scoring.
"""

import os
import logging
import warnings

# ==========================================
# 1. WARNING SUPPRESSION
# ==========================================
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", message="You are sending unauthenticated requests")
logging.getLogger("transformers").setLevel(logging.ERROR)

import transformers
transformers.logging.set_verbosity_error()

from gtts import gTTS
from pydub import AudioSegment

# Direct import (Assumes running as module or PYTHONPATH is set)
from PictureDescription.service.picture_description_audio_service import PictureDescriptionAudioService

# ==========================================
# 2. SCENARIO DEFINITIONS
# ==========================================
SCENARIOS = {
    "A_Healthy_Control": [
        ("The boy is standing on a stool reaching for cookies from a jar.", 0.5),
        ("The girl is asking him for one.", 0.5),
        ("Water is overflowing from the sink and spilling onto the floor.", 0.5),
        ("The mother is washing dishes and not paying attention.", 0.0)
    ],

    "B_MCI_Anomic": [
        ("A child climbs on a... um... thing.", 3.5),
        ("To grab food while his sister waits.", 1.0),
        ("The sink is running over... and water is everywhere.", 2.0),
        ("Their mother is... uh... busy with dishes.", 0.0)
    ],

    "C_Core_Only_Telegraphic": [
        ("Boy on stool.", 1.0),
        ("Reaching cookies.", 1.0),
        ("Water overflowing.", 1.0),
        ("Mother distracted.", 0.0)
    ],

    "D_Alzheimers_Severe": [
        ("Boy... uh... falling.", 2.0),
        ("Water... um... on floor.", 4.0),
        ("Mother... washing.", 0.0)
    ],

    "E_Off_Topic_Confabulation": [
        ("The family is having a nice dinner.", 1.0),
        ("They are eating soup in the garden.", 0.0)
    ]
}

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def generate_simulation_audio(segments, output_filename):
    combined_audio = AudioSegment.empty()
    if not os.path.exists("temp_chunks"): os.makedirs("temp_chunks")
    print(f"   🔨 Synthesizing {output_filename}...")

    for i, (text, pause_sec) in enumerate(segments):
        chunk_path = f"temp_chunks/chunk_{i}.mp3"
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(chunk_path)
        combined_audio += AudioSegment.from_mp3(chunk_path)
        if pause_sec > 0:
            combined_audio += AudioSegment.silent(duration=pause_sec * 1000)

    combined_audio.export(output_filename, format="mp3")
    for f in os.listdir("temp_chunks"): os.remove(os.path.join("temp_chunks", f))
    os.rmdir("temp_chunks")

def print_ui_report(label, result):
    # --- FIX KEYERROR ---
    # The pipeline returns 'scores' (summary) and 'details' (full dict) at the top level.
    # We access them directly instead of looking for summary/details inside 'scores'.
    s = result["scores"]
    d = result["details"]

    sp = result.get("spatial_stats", {})
    u = result["utterances"]

    syntax = u.get("syntax_stats", {})
    disfluency_pct = u['disfluency_stats'].get('disfluency_score', 0.0)

    print(f"\n{'-'*100}")
    print(f"📄 UI SPEC REPORT: {label}")
    print(f"{'-'*100}")

    print(f"🗣️  ASR Transcript:\n    \"{result['transcript']}\"")

    print(f"\n🏆 FINAL RISK SCORE: {s['final_score']:.2%} (0.00 - 1.00)")

    print("\n📊 SCORE BREAKDOWN:")
    print(f"   1. Memory (Content) : {s['iu_normalized']:.4f} (Weight: 75%)")
    print(f"   2. Fluency (Proc)   : {s['fluency_score']:.4f} (Weight: 15%)")
    print(f"      ↳ Penalty (Text) : -{s.get('penalty_text', 0.0):.4f}")
    print(f"      ↳ Penalty (Audio): -{s.get('penalty_audio', 0.0):.4f}")
    print(f"   3. Spatial (Lang)   : {s['spatial_score']:.4f} (Weight: 10%)")

    print(f"\n🧠 LINGUISTIC MARKERS (Clinical Features):")
    print(f"   🔹 Spatial Density  : {sp.get('spatial_density', 0.0):.2f} (Prepositions/Utt) [Target: >0.20]")
    print(f"   🔹 Syntactic Depth  : {syntax.get('avg_tree_depth', 0.0):.2f} (Tree Height)      [Target: >3.5]")
    print(f"   🔹 Disfluency Rate  : {disfluency_pct:.2%} (Fillers/Total)")

    print(f"\n🧹 PROCESSING CHECK (Raw vs Cleaned):")
    # Handle list or dict structure for utterances depending on segmentation version
    raw = u["raw_utterances"][:3]
    clean = u["cleaned_utterances"][:3]

    has_diff = False
    for r, c in zip(raw, clean):
        # Normalize simple punctuation for comparison
        if r.lower().replace(".","") != c:
            print(f"   Raw: \"{r}\" -> Clean: \"{c}\"")
            has_diff = True
    if not has_diff:
        print("   (No fillers detected/removed in first 3 lines)")

    print(f"\n📋 COMPARISON TABLE (Content Verification)")
    print(f"   {'TYPE':<8} | {'STATUS':<10} | {'EXPECTED CONCEPT':<40} | {'USER RECALL'}")
    print(f"   {'-'*100}")

    iu_table = d["iu_table"]
    sorted_ius = sorted(iu_table.items(), key=lambda x: (x[1]['iu_type'], x[0]))

    for iu_id, row in sorted_ius:
        exp = row['expected_text']
        rec = row['matched_utterance'] or "---"

        # Truncate for display
        if len(exp) > 38: exp = exp[:35] + "..."
        if len(rec) > 38: rec = rec[:35] + "..."

        status = "✅ MATCH" if row['score'] == 1.0 else ("⚠️ PARA" if row['score'] >= 0.5 else "❌ MISS")
        print(f"   {row['iu_type']:<8} | {status:<10} | {exp:<40} | {rec}")

# ==========================================
# 4. EXECUTION
# ==========================================
def run_full_suite():
    # Robust data directory check (relative to execution)
    if os.path.exists("data"):
        data_dir = "data"
    elif os.path.exists("../data"):
        data_dir = "../data"
    else:
        # Assumes running from project root if neither found
        data_dir = "PictureDescription/data"

    if not os.path.exists(data_dir):
        print(f"❌ ERROR: Could not find 'data' directory. Searched in: {data_dir}")
        print("   Make sure you are running from the project root or the evaluation folder.")
        return

    service = PictureDescriptionAudioService(data_dir=data_dir)

    print("\n🚀 RUNNING AUDIO PICTURE DESCRIPTION SUITE (A-E)")
    print("ℹ️  Pause Threshold: 3.0s | ASR Model: Small")

    for label, segments in SCENARIOS.items():
        filename = f"{label}.mp3"
        generate_simulation_audio(segments, filename)

        try:
            result = service.score_description_audio(
                picture_id="cookie_theft",
                audio_path=filename
            )
            print_ui_report(label, result)
        except Exception as e:
            print(f"\n❌ FAILED {label}: {e}")
            import traceback
            traceback.print_exc()

        if os.path.exists(filename): os.remove(filename)
        wav_name = filename.replace(".mp3", ".wav")
        if os.path.exists(wav_name): os.remove(wav_name)

    print("\n✅ SUITE COMPLETE")

if __name__ == "__main__":
    run_full_suite()