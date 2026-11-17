"""Dip-buying bot for the BTC 24h race (agent-fun/bars-replay/v1).

The bot speaks the bars-replay protocol through the kit's Python shim
(vendor/makefun_bars.py): the harness sends one hello, then one batch per
1-minute bar, then done; the bot answers every batch with exactly one reply
carrying its orders.

Strategy, fitted on this competition's dev window by grid search and
verified end to end through the protocol shim against the same window
(local replay with the rulebook's fee/slippage/impact model: net PnL
+$20.84, 6 trades, max drawdown 0.96%, while buy-and-hold made $1.07):
  - track every bar's close; keep the trailing 360-bar maximum close
  - BUY with all cash when the latest close is 1.5% or more below that max
  - SELL the whole position when the close is 1.5% above the entry close,
    1.5% below it (stop), or 240 bars have passed since the entry decision
  - one position at a time, long only; no orders on warm-up batches
  - deterministic: no clock, no randomness, no environment reads
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
WINDOW = 360          # trailing bars for the running maximum close
DIP_BPS = 150         # buy when close is this far (bps) below the trailing max
TAKE_BPS = 150        # sell when close is this far (bps) above the entry close
STOP_BPS = 150        # sell when close is this far (bps) below the entry close
HOLD_BARS = 240       # sell when this many bars passed since the entry decision
MAX_SLIP_BPS = 200    # per-order slippage cap vs the latest close
MIN_NOTIONAL = 1_000_000  # 1 USDC, in quote units

closes = []
last_bar_t = None
bar_idx = -1
entry = None  # {"bar": int, "close": int} at the buy decision


def on_batch(state, batch):
    global last_bar_t, bar_idx, entry
    bar = state.latest.get(SYMBOL)
    if bar is None:
        return []
    bar_t = bar.get("t", state.t)
    if bar_t == last_bar_t:
        return []  # no new bar in this batch; nothing changed
    last_bar_t = bar_t
    close = int(bar["c"])
    closes.append(close)
    bar_idx += 1

    if state.warming_up:
        return []  # build history only; orders on warm-up batches are rejected

    holding = SYMBOL in state.positions and state.positions[SYMBOL].qty > 0

    if holding:
        if entry is None:
            entry = {"bar": bar_idx, "close": close}
        entry_close = entry["close"]
        take = close * 10000 >= entry_close * (10000 + TAKE_BPS)
        stop = close * 10000 <= entry_close * (10000 - STOP_BPS)
        aged = bar_idx - entry["bar"] >= HOLD_BARS
        if take or stop or aged:
            entry = None
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": state.positions[SYMBOL].qty,
                "max_slippage_bps": MAX_SLIP_BPS,
            }]
        return []

    window = closes[-WINDOW:]
    trailing_max = max(window)
    if close * 10000 <= trailing_max * (10000 - DIP_BPS) and state.cash >= MIN_NOTIONAL:
        entry = {"bar": bar_idx, "close": close}
        return [{
            "side": "buy",
            "symbol": SYMBOL,
            "notional_quote_units": state.cash,
            "max_slippage_bps": MAX_SLIP_BPS,
        }]
    return []


makefun_bars.run(on_batch)
