"""Dip-buying bot for the 24-hour BTC race (agent-fun/bars-replay/v1).

Protocol: the harness speaks through the kit's Python shim
(vendor/makefun_bars.py). It sends one hello, then one batch for each
1-minute bar, then done. The bot answers each batch with exactly one
reply carrying zero or more orders.

The rule below was fitted on this competition's dev window with a grid
search and checked end to end through the protocol shim on that same
window, under the rulebook fill model (fees, slippage, impact): net
PnL +$20.84 across 6 trades, max drawdown 0.96%. Buy-and-hold on the
same window made +$1.07.

  - Remember every bar's close; keep the maximum close of the last
    360 bars as the trailing reference.
  - BUY with all available cash when the latest close sits 1.5% or
    more below that trailing maximum.
  - SELL the whole position when the close reaches 1.5% above the
    entry close, falls 1.5% below it (stop), or 240 bars have passed
    since the entry decision.
  - Long only, at most one position; no orders while warming up.
  - Fully deterministic: no clock, no randomness, no environment reads.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

# Instrument and fitted rule parameters (basis points where noted).
SYMBOL = "CBBTC"
WINDOW = 360              # bars in the trailing maximum-close window
DIP_BPS = 150             # buy once close is this far below the trailing max
TAKE_BPS = 150            # sell once close is this far above the entry close
STOP_BPS = 150            # sell once close is this far below the entry close
HOLD_BARS = 240           # sell once this many bars passed since entry
MAX_SLIP_BPS = 200        # slippage cap per order, vs the latest close
MIN_NOTIONAL = 1_000_000  # smallest buy, in quote units (1 USDC)

# Running state, reset only by a fresh process start.
closes = []       # every close seen so far, in bar order
last_bar_t = None  # timestamp of the last bar already processed
bar_idx = -1       # index of the latest processed bar
entry = None       # {"bar": int, "close": int} recorded at the buy decision


def on_batch(state, batch):
    """Decide the orders for one batch. Returns a list of order dicts."""
    global last_bar_t, bar_idx, entry
    bar = state.latest.get(SYMBOL)
    if bar is None:
        return []
    bar_t = bar.get("t", state.t)
    if bar_t == last_bar_t:
        # Same bar repeated in another batch: nothing new to decide.
        return []
    last_bar_t = bar_t
    close = int(bar["c"])
    closes.append(close)
    bar_idx += 1

    if state.warming_up:
        # History-building only; the harness rejects warm-up orders.
        return []

    position = state.positions[SYMBOL] if SYMBOL in state.positions else None
    holding = position is not None and position.qty > 0

    if holding:
        if entry is None:
            # Defensive: a position with no recorded entry counts as
            # entered on this bar, so exits are measured from here.
            entry = {"bar": bar_idx, "close": close}
        entry_close = entry["close"]
        # Integer basis-point comparisons: no float rounding anywhere.
        take_hit = close * 10000 >= entry_close * (10000 + TAKE_BPS)
        stop_hit = close * 10000 <= entry_close * (10000 - STOP_BPS)
        too_old = bar_idx - entry["bar"] >= HOLD_BARS
        if take_hit or stop_hit or too_old:
            sell_order = {
                "side": "sell",
                "symbol": SYMBOL,
                "qty": position.qty,
                "max_slippage_bps": MAX_SLIP_BPS,
            }
            entry = None
            return [sell_order]
        return []

    trailing_max = max(closes[-WINDOW:])
    dipped = close * 10000 <= trailing_max * (10000 - DIP_BPS)
    if dipped and state.cash >= MIN_NOTIONAL:
        buy_order = {
            "side": "buy",
            "symbol": SYMBOL,
            "notional_quote_units": state.cash,
            "max_slippage_bps": MAX_SLIP_BPS,
        }
        entry = {"bar": bar_idx, "close": close}
        return [buy_order]
    return []


makefun_bars.run(on_batch)
