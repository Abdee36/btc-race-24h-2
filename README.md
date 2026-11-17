# btc-race-24h-2

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/Abdee36/btc-race-24h-2/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/Abdee36/btc-race-24h-2/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

A dip-buying BTC trading bot for make.fun's 24-hour live race. It trades Coinbase Wrapped BTC (cbBTC) against USDC on 1-minute on-chain bars: it buys with all cash when the close dips 1.5% below the trailing 360-bar maximum close, and sells the whole position at +1.5% from entry, at a -1.5% stop, or after 240 bars. Long only, one position at a time, fully deterministic. Fitted on the competition's dev window by grid search and verified end to end through the protocol shim: net PnL +$20.84, 6 trades, max drawdown 0.96%.

## Run it

```sh
python3 -P -s main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=7f4bzy0t&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>
