"""
Free Speech Diagnostic Suite (Audio + Behavior + Stats)
------------------------------------------------------
Simulates multiple cognitive speech scenarios,
runs NeuroSpeech pipeline, and prints UI-style reports.
"""

import os

# --- Suppress tokenizer warnings ---
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from gtts import gTTS
from pydub import AudioSegment

from FreeSpeech.service.free_speech_audio_service import FreeSpeechAudioService


# ==========================================
# 1. SCENARIO DEFINITIONS
# ==========================================
SCENARIOS = {
    "A_Healthy_Speech": [
        ("Yesterday I went to the market and bought fresh vegetables and fruits.", 0.2),
        ("Then I returned home and prepared lunch for my family.", 0.2),
        ("Later in the evening I went for a walk and met some friends.", 0.2),
        ("We talked for a while about different things and shared some ideas. After that I came back home, had dinner, and spent some time watching television before going to sleep.", 0.0)
    ],
    "B_MCI_Speech": [
        ("I went somewhere yesterday, maybe a market or some place like that.", 1.0),
        ("I bought some things, I think vegetables and maybe something else.", 1.0),
        ("Then I came back home and did some work, but I don't remember clearly.", 1.0),
        ("After that I was just sitting and doing things and not much happened really.", 0.0)
    ],
    # 🚨 Padded to beat Whisper's deduplication filter
    "C_Repetition_Loop": [
        ("Today started off normally, but then I went to the store to buy some apples.", 0.5),
        ("I went to the store to buy some apples. I went to the store to buy some apples.", 0.5),
        ("Then I went again and again and again. I kept going to the store over and over.", 0.5),
        ("I kept repeating the exact same thing every single time. I just went there again and again and again to look around before finally going home to rest.", 0.0)
    ],
    # 🔥 UPDATED: Added direct "Filler + Noun" patterns to test Anomia flags
    "D_Filler_Heavy": [
        ("Yesterday morning I woke up early and decided to go to the market. I wanted to buy, um, apples.", 0.5),
        ("Then I came back to the house and looked in the, ah, kitchen.", 0.5),
        ("I was thinking really hard and I realized, uh, memory is just not working properly.", 0.5),
        ("Then I stayed home and did not do much after that, just watched television for the rest of the entire day.", 0.0)
    ],
    "E_Topic_Drift": [
        ("I went to the market to buy vegetables and fruits.", 0.5),
        ("The sky is very blue and birds are flying everywhere.", 0.5),
        ("I like watching television and eating food at night.", 0.5),
        ("Sometimes people go to the gym and exercise regularly.", 0.5),
        ("My friend likes music and plays guitar every day.", 0.5),
        ("I once saw a movie about space and planets and it was interesting.", 0.0)
    ]
}


# ==========================================
# 2. AUDIO GENERATOR
# ==========================================
def generate_simulation_audio(segments, output_filename):
    combined_audio = AudioSegment.empty()

    if not os.path.exists("temp_chunks"):
        os.makedirs("temp_chunks")

    print(f"   🔨 Synthesizing {output_filename}...")

    for i, (text, pause_sec) in enumerate(segments):
        chunk_path = f"temp_chunks/chunk_{i}.mp3"

        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(chunk_path)

        combined_audio += AudioSegment.from_mp3(chunk_path)

        if pause_sec > 0:
            combined_audio += AudioSegment.silent(duration=pause_sec * 1000)

    combined_audio.export(output_filename, format="mp3")

    # cleanup temp
    for f in os.listdir("temp_chunks"):
        os.remove(os.path.join("temp_chunks", f))
    os.rmdir("temp_chunks")


# ==========================================
# 3. REPORTING ENGINE
# ==========================================
def print_ui_report(label, result):

    summary = result["final_score"]["summary"]
    details = result["final_score"].get("details", {})
    features = result["features"]

    print(f"\n{'='*80}")
    print(f"▶️  REPORT: {label}")
    print(f"{'='*80}")

    print(f"\n🗣️ TRANSCRIPT:\n  \"{result['transcript']}\"")

    # -----------------------------
    # FINAL SCORE
    # -----------------------------
    print(f"\n📊 COGNITIVE SCORE")
    print(f"  Score        : {summary.get('cognitive_score')}")
    print(f"  Risk Level   : {summary.get('risk_level')}")
    print(f"  Confidence   : {summary.get('confidence')}")
    print(f"  Explanation  : {summary.get('explanation')}")

    # 🚨 STOP EARLY IF INVALID
    if summary.get("risk_level") == "invalid":
        print("\n⛔ Sample too small — skipping feature breakdown.")
        return

    # -----------------------------
    # FEATURES
    # -----------------------------
    print(f"\n🧠 FEATURE BREAKDOWN")

    for key, value in features.items():
        print(f"\n  🔹 {key}:")
        print(f"     {value}")

    # -----------------------------
    # NORMALIZED SCORES & CONTRIBUTIONS
    # -----------------------------
    print(f"\n📈 NORMALIZED FEATURE SCORES & CONTRIBUTIONS")

    # The actual payload from FreeSpeechPipeline -> Scorer
    details_dict = result.get("final_score", {}).get("details", {})
    normalized = details_dict.get("normalized_points", {})
    contributions = details_dict.get("feature_contribution", {})

    print(f"  [DEBUG] Raw Contributions Dict: {contributions}")

    for k, v in normalized.items():
        contrib = contributions.get(k, 0.0)
        print(f"  {k:<12}: {v:<5} (Contributed {contrib} pts)")

    # -----------------------------
    # INTERPRETATION
    # -----------------------------
    print(f"\n🧾 INTERPRETATION")

    risk = summary.get("risk_level")

    if risk == "healthy":
        print("  ✔ Speech is coherent, fluent, and information-rich.")
    elif risk == "mci":
        print("  ⚠ Mild irregularities detected — possible early cognitive decline.")
    else:
        print("  🚨 Significant impairment detected in speech patterns.")


def print_detailed_table(result):

    print(f"\n📊 DETAILED FEATURE TABLE (UI READY)")
    print("-" * 100)

    headers = f"{'FEATURE':<15} {'NORMALIZED':<12} {'CONTRIBUTION':<15} {'RAW VALUE'}"
    print(headers)
    print("-" * 100)

    details = result.get("final_score", {}).get("details", {})
    normalized = details.get("normalized_points", {})
    contributions = details.get("feature_contribution", {})
    raw = details.get("raw_metrics", {})

    for feature in normalized.keys():

        norm_val = normalized.get(feature, "-")
        contrib_val = contributions.get(feature, "-")

        raw_val = "-"

        if feature == "idea":
            raw_val = raw.get("idea_density", {}).get("idea_density")

        elif feature == "coherence":
            raw_val = raw.get("coherence", {}).get("coherence_score")

        elif feature == "repetition":
            raw_val = raw.get("repetition", {}).get("repetition_ratio")

        elif feature == "fluency":
            raw_val = raw.get("fluency", {}).get("wpm")

        elif feature == "ttr":
            raw_val = raw.get("lexical_diversity", {}).get("primary_score")

        elif feature == "syntax":
            raw_val = raw.get("syntax", {}).get("avg_dependency_depth")

        elif feature == "perplexity":
            raw_val = raw.get("perplexity", {}).get("perplexity")

        print(f"{feature:<15} {norm_val:<12} {contrib_val:<15} {raw_val}")

    # =========================================================
    # 🔥 EVIDENCE PANEL
    # =========================================================
    print(f"\n🧠 FEATURE EVIDENCE (WHY THIS SCORE HAPPENED)")
    print("-" * 100)

    features = result.get("features", {})

    # -----------------------------
    # DISFLUENCY
    # -----------------------------
    dis = features.get("disfluency", {})
    print("\n🔹 Disfluency Evidence:")
    print(f"   Fillers Detected     : {dis.get('filler_count')}")
    print(f"   Repetition Count     : {dis.get('repetition_count')}")
    print(f"   Pause Count          : {dis.get('pause_count')}")
    print(f"   Disfluency Score     : {dis.get('disfluency_score')}")

    # -----------------------------
    # REPETITION
    # -----------------------------
    rep = features.get("repetition", {})
    rep_ev = rep.get("evidence", {})
    print("\n🔹 Repetition Evidence:")
    print(f"   Repeated Words       : {rep_ev.get('repeated_words')}")
    print(f"   Repeated Phrases     : {rep_ev.get('repeated_phrases')}")
    print(f"   Repetition Ratio     : {rep.get('repetition_ratio')}")

    # -----------------------------
    # IDEA DENSITY (🔥 UPDATED WITH ANOMIA)
    # -----------------------------
    idea = features.get("idea_density", {})
    idea_ev = idea.get("evidence", {})
    print("\n🔹 Idea Density Evidence:")
    print(f"   Content Words        : {idea.get('content_words')}")
    print(f"   Vague Words Count    : {idea.get('vague_words_count')}")
    print(f"   Vague Words Used     : {idea_ev.get('vague_words')}")
    print(f"   Anomia Count         : {idea.get('anomia_flags')}")
    print(f"   Anomia Instances     : {idea_ev.get('anomia_instances')}")

    # -----------------------------
    # LEXICAL DIVERSITY
    # -----------------------------
    ttr = features.get("lexical_diversity", {})
    print("\n🔹 Lexical Diversity Evidence:")
    print(f"   Total Words          : {ttr.get('raw_stats', {}).get('total_words')}")
    print(f"   Unique Words         : {ttr.get('raw_stats', {}).get('unique_lemmas')}")

    # -----------------------------
    # SYNTAX
    # -----------------------------
    syn = features.get("syntax", {})
    syn_ev = syn.get("evidence", {})
    print("\n🔹 Syntax Evidence:")
    print(f"   Clause Length        : {syn.get('mean_clause_length')}")
    print(f"   Dependency Depth     : {syn.get('avg_dependency_depth')}")
    print(f"   Subordination Ratio  : {syn.get('subordination_ratio')}")

    # -----------------------------
    # COHERENCE
    # -----------------------------
    coh = features.get("coherence", {})
    print("\n🔹 Coherence Evidence:")
    print(f"   Coherence Score      : {coh.get('coherence_score')}")
    print(f"   Sentence Count       : {coh.get('num_sentences')}")

    # -----------------------------
    # FLUENCY
    # -----------------------------
    flu = features.get("fluency", {})
    flu_ev = flu.get("evidence", {})
    print("\n🔹 Fluency Evidence:")
    print(f"   WPM                  : {flu.get('wpm')}")
    print(f"   Speed Category       : {flu.get('speech_speed')}")
    print(f"   Flags                : {flu_ev.get('flags')}")

    # -----------------------------
    # PERPLEXITY
    # -----------------------------
    perp = features.get("perplexity", {})
    print("\n🔹 Perplexity Evidence:")
    print(f"   Perplexity Score     : {perp.get('perplexity')}")
    print(f"   Reliability          : {perp.get('is_reliable')}")


# ==========================================
# 4. MAIN EXECUTION
# ==========================================
def run_full_suite():

    service = FreeSpeechAudioService()

    print("\n🚀 STARTING FREE SPEECH DIAGNOSTIC SUITE")

    for label, segments in SCENARIOS.items():

        filename = f"{label}.mp3"

        # 1. Generate audio
        generate_simulation_audio(segments, filename)

        # 2. Analyze
        result = service.analyze_audio(filename)

        # 3. Report
        print_ui_report(label, result)
        print_detailed_table(result)

        # 4. Cleanup
        if os.path.exists(filename):
            os.remove(filename)

        wav_name = filename.replace(".mp3", ".wav")
        if os.path.exists(wav_name):
            os.remove(wav_name)

    print("\n✅ SUITE COMPLETE")


# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == "__main__":
    run_full_suite()