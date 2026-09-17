"""
G-Match Scoring
---------------
Evaluates recall order with primacy sensitivity.
"""

def compute_gmatch(canonical_order, recalled_order):
    if not recalled_order:
        return {
            "canonical_order": canonical_order,
            "recalled_order": [],
            "order_score": 0.0,
            "primacy_penalty": 1.0,
            "penalty": 1.0
        }

    # ---------- Order penalty ----------
    mismatches = sum(
        1 for i, iu in enumerate(recalled_order)
        if i >= len(canonical_order) or iu != canonical_order[i]
    )
    order_penalty = mismatches / len(canonical_order)

    # ---------- Primacy penalty ----------
    primacy_cutoff = max(1, len(canonical_order) // 3)
    primacy_block = canonical_order[:primacy_cutoff]
    primacy_missed = sum(1 for iu in primacy_block if iu not in recalled_order)

    primacy_penalty = primacy_missed / len(primacy_block)

    # ---------- Final ----------
    total_penalty = 0.7 * primacy_penalty + 0.3 * order_penalty

    return {
        "canonical_order": canonical_order,
        "recalled_order": recalled_order,
        "order_score": round(1 - order_penalty, 4),
        "primacy_penalty": round(primacy_penalty, 4),
        "penalty": round(total_penalty, 4)
    }