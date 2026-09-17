"""
Perplexity (Language Model Coherence)
-------------------------------------
Measures how "surprising" or "confusing" speech is.

Clinical Insight:
- High perplexity → incoherent / disorganized speech
"""

from typing import Dict, List
import torch
from transformers import AutoModelForCausalLM, GPT2Tokenizer
from .thresholds import Thresholds

print("Loading GPT-2 Tokenizer...")
_tokenizer = GPT2Tokenizer.from_pretrained("gpt2", use_fast=False)

print("Loading GPT-2 Model...")
_model = AutoModelForCausalLM.from_pretrained("gpt2")

_tokenizer.pad_token = _tokenizer.eos_token

_device = (
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)

_model = _model.to(_device)
_model.eval()

print("GPT-2 successfully loaded into memory.")


def compute_perplexity(raw_text: str) -> Dict:

    # -----------------------------
    # SAFETY
    # -----------------------------
    if not raw_text or len(raw_text.split()) < 5:
        return _empty_response()

    sentences = _split_sentences(raw_text)

    try:
        encodings = _tokenizer(
            raw_text,
            return_tensors="pt",
            truncation=True,
            max_length=_model.config.n_positions
        )

        encodings = {k: v.to(_device) for k, v in encodings.items()}
        input_ids = encodings["input_ids"]

        with torch.no_grad():
            outputs = _model(input_ids, labels=input_ids)
            loss = outputs.loss

        perplexity = torch.exp(loss).item()

    except Exception:
        return _empty_response()

    # -----------------------------
    # SENTENCE-LEVEL ANALYSIS
    # -----------------------------
    sentence_scores = []
    high_confusion = []

    for sent in sentences:
        if len(sent.split()) < 3:
            continue

        try:
            enc = _tokenizer(sent, return_tensors="pt").to(_device)
            with torch.no_grad():
                out = _model(enc["input_ids"], labels=enc["input_ids"])
                sent_ppl = torch.exp(out.loss).item()

            sentence_scores.append({
                "text": sent,
                "perplexity": round(sent_ppl, 2)
            })

            if sent_ppl > Thresholds.perplexity["borderline"]:
                high_confusion.append(sent)

        except:
            continue

    # -----------------------------
    # CLINICAL LEVEL
    # -----------------------------
    if perplexity < Thresholds.perplexity["healthy"]:
        level = "healthy"
    elif perplexity <= Thresholds.perplexity["borderline"]:
        level = "borderline"
    else:
        level = "impaired"

    # -----------------------------
    # RELIABILITY
    # -----------------------------
    token_count = input_ids.shape[1]
    is_reliable = token_count >= 20

    # -----------------------------
    # PATTERN DETECTION
    # -----------------------------
    if perplexity > 40:
        pattern = "severely_disorganized"
    elif perplexity > 25:
        pattern = "semantic_confusion"
    elif perplexity > 15:
        pattern = "mild_incoherence"
    else:
        pattern = "normal_language"

    # -----------------------------
    # OUTPUT
    # -----------------------------
    return {
        "perplexity": round(perplexity, 4),
        "perplexity_level": level,
        "is_reliable": is_reliable,

        "evidence": {
            "sentence_scores": sentence_scores[:5],
            "confusing_sentences": high_confusion[:3],
            "pattern": pattern,
            "token_count": token_count
        }
    }


def _split_sentences(text: str) -> List[str]:
    return [s.strip() for s in text.split(".") if s.strip()]


def _empty_response():
    return {
        "perplexity": 0.0,
        "perplexity_level": "impaired",
        "is_reliable": False,
        "evidence": {}
    }