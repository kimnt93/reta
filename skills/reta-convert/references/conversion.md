# Exact conversion requirements

SMA regime compares current final close to its trailing SMA with a symmetric
basis-point band. Equality is flat. Channel breakout compares current close
to previous-bar channels and retains state until exit/reversal. Z-score
reversion uses a trailing population standard deviation, explicit entry/exit
thresholds and neutral constant windows. See the kernel for precise semantics.

A conversion that changes the indicator, threshold, next-bar timing or sizing
is not equivalent. Ask for an explicit changed objective or implement a new
typed family with independent examples. Never describe generic Pine/MQL/AFL
parsing as available: source understanding belongs to the current harness,
while the emitted spec must exactly match supported deterministic semantics.

Generated positions are absolute net integer targets. Flat and unchanged
positions are included after warmup. Rows record decision_ts and effective_ts;
execution is no earlier than the next scheduled opening. Future prices or
labels cannot influence earlier decisions. No broker execution is included.
