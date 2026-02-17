If you've spent any time in Solana DeFi, you've seen the APRs. Pools showing 200%, 500%, sometimes 1000%+ annual returns. Most of it is bait. But underneath the noise, there's a real mechanism generating real yield: **liquidity provider fees**.

I built an open-source bot that autonomously finds, evaluates, and provides liquidity to Raydium pools on Solana, then actively manages those positions to extract trading fees while defending against rug pulls, impermanent loss, and the general chaos of meme token markets.

This post breaks down how Raydium liquidity pools actually work, why LP fee farming is interesting, and the technical details of building a bot that does it autonomously.

## What Is Raydium?

[Raydium](https://raydium.io/) is an automated market maker (AMM) built on Solana. It's one of the largest decentralized exchanges on the network, handling billions in monthly trading volume.

Unlike a traditional exchange with an order book (buyers and sellers placing limit orders), an AMM uses **liquidity pools**, smart contracts that hold reserves of two tokens and allow anyone to trade between them algorithmically. There's no counterparty on the other side of your trade. You're trading against a pool of tokens governed by a mathematical formula.

Raydium started as a standard constant-product AMM (like Uniswap V2), but has evolved with concentrated liquidity features (similar to Uniswap V3). The bot focuses on Raydium's standard V4 AMM pools, which are the most common, especially for newer tokens and meme coins.

### Solana's Advantage

Why Solana? Two reasons that matter for LP bots:

1. **Speed**: ~400ms block times mean positions can be entered and exited quickly. On Ethereum, you'd be waiting 12+ seconds per block and paying $5-50 in gas per transaction.
2. **Cost**: Solana transactions cost fractions of a cent. This makes it economically viable to enter and exit small positions ($10-50) that would be eaten alive by Ethereum gas fees.

These properties make high-frequency LP management practical in a way that isn't really possible on other chains.

## How Liquidity Pools Work

This is the core concept you need to understand. A liquidity pool is deceptively simple.

### The Basic Mechanism

A Raydium pool holds reserves of two tokens, say, SOL and $HACHI (a meme token). The pool maintains a **constant product** relationship:

$$x \times y = k$$

Where $x$ is the reserve of token A, $y$ is the reserve of token B, and $k$ is a constant.

When a trader wants to buy $HACHI with SOL, they deposit SOL into the pool and withdraw $HACHI. The pool's SOL reserves increase, $HACHI reserves decrease, and the price shifts accordingly. The constant $k$ stays (approximately) the same.

**The price of a token in the pool is simply the ratio of reserves:**

$$\text{price} = \frac{\text{reserve}_A}{\text{reserve}_B}$$

This means the pool self-adjusts. If $HACHI's price on other exchanges rises, arbitrageurs will buy $HACHI from this pool (it's now cheap relative to market) until the pool price matches. This arbitrage flow is what keeps AMM prices aligned with the broader market.

### Becoming a Liquidity Provider

Anyone can deposit tokens into a pool. When you **add liquidity**, you deposit both tokens in proportion to the current reserve ratio. In return, you receive **LP tokens**, a receipt that represents your share of the pool.

**Example:**

- Pool has 100 SOL and 1,000,000 $HACHI
- You deposit 1 SOL and 10,000 $HACHI (1% of the pool)
- You receive LP tokens representing 1% of the pool
- Any future trades through this pool → you earn 1% of the fees

When you **remove liquidity**, you burn your LP tokens and receive back your proportional share of both tokens in the pool. But here's the thing, the amounts you get back may be different from what you put in, because trades have shifted the reserve ratios. This is where impermanent loss comes in (more on that later).

### Where Do LP Fees Come From?

Every trade through a Raydium pool pays a fee, typically 0.25% of the trade amount. This fee is split:

- **0.22%** goes to liquidity providers (added back to the pool reserves)
- **0.03%** goes to Raydium's protocol treasury

These fees accumulate automatically. Your LP tokens don't just represent a share of the reserves, they represent a share of the reserves *plus all accumulated fees*. So your LP position grows in value over time, proportional to trading volume.

**This is the yield.** It's not inflationary token rewards. It's not ponzi mechanics. It's a direct cut of every trade that flows through the pool. The more trading volume a pool sees, the more fees LPs earn.

For a pool doing $500K in daily volume with $100K in TVL (total value locked), LPs collectively earn:

$$\$500{,}000 \times 0.0022 = \$1{,}100 \text{ per day}$$

That's $1,100 per day split among $100K of liquidity = **1.1% daily return = ~400% APR**.

These numbers are real. The catch is that pools with these metrics are usually meme tokens that can lose 50% of their value overnight. That's where the bot comes in.

## The Problem: Why Manual LP Is Painful

If the yield is so good, why doesn't everyone do it? Because manual LP management on meme token pools is a nightmare:

1. **Discovery**: There are 1000+ active WSOL pools on Raydium at any given time. Finding the ones with good yield-to-risk ratio requires scanning hundreds of pools.

2. **Safety analysis**: Most high-APR pools are traps. The token creator holds 50% of supply, or the LP tokens aren't burned (meaning they can rug-pull the liquidity), or the token has a mint authority that can print infinite tokens.

3. **Timing**: Meme token pools have a lifecycle. Volume surges when the token launches, plateaus, then dies. The best LP returns come from entering during the volume surge and exiting before the crash.

4. **Risk management**: Even in "safe" pools, impermanent loss can wipe out your fee earnings if the token price moves too far. You need to monitor continuously and exit when conditions deteriorate.

5. **Operational overhead**: Adding liquidity, monitoring positions, removing liquidity, swapping tokens back to SOL, closing token accounts, reclaiming rent, each trade requires multiple blockchain transactions.

The bot automates all of this.

## Architecture: Python + Node.js Hybrid

The bot uses a hybrid architecture that was driven by a practical constraint: the Raydium SDK is JavaScript-only, but Python is far better for data analysis and orchestration.

```
┌─────────────────────────────────────────┐
│           Python Bot (main.py)          │
│                                         │
│  Pool Discovery → Safety Analysis →     │
│  Scoring → Position Management →        │
│  Risk Monitoring → Exit Logic           │
├─────────────────────────────────────────┤
│           IPC (subprocess + JSON)       │
├─────────────────────────────────────────┤
│       Node.js Bridge (bridge.js)        │
│                                         │
│  @raydium-io/raydium-sdk-v2             │
│  Add Liquidity / Remove Liquidity       │
│  Token Swaps / Balance Queries          │
├─────────────────────────────────────────┤
│            Solana Blockchain            │
│                                         │
│  RPC: Wallet balance, LP token lookup   │
│  Transactions: LP add/remove, swaps     │
└─────────────────────────────────────────┘
```

**Python** handles everything analytical: API calls to Raydium and RugCheck, pool filtering and scoring, position tracking, P&L calculation, impermanent loss monitoring, exit condition evaluation.

**Node.js** handles everything transactional: constructing Raydium SDK transactions, signing with the wallet keypair, submitting to the Solana network.

Communication between them is dead simple, Python spawns a Node.js subprocess, passes a JSON command, and reads the JSON response. No WebSocket servers, no message queues, no complexity.

## Pool Discovery and Filtering

The bot starts by fetching all active WSOL pools from Raydium's V3 API. On a typical scan, that's ~1,100 pools. Only WSOL pairs are considered because SOL is the base asset, the bot holds SOL, provides it as liquidity, and wants it back when exiting.

### The Filtering Pipeline

From 1,100 pools, the bot typically narrows down to 2-5 candidates through progressive filtering:

**Stage 1 — Basic metrics** (eliminates ~95% of pools):

- TVL ≥ $5,000 (pools with less liquidity have extreme slippage)
- Volume/TVL ratio ≥ 0.5 (pool must have trading activity relative to its size)
- 24h APR ≥ 100% (not worth the risk for lower yields on meme tokens)
- LP burn ≥ 50% (more than half of LP tokens must be permanently destroyed)

**Stage 2 — RugCheck token safety** (eliminates most remaining pools):

- Query RugCheck API for the non-WSOL token's safety report
- Reject any token with "danger" level risk flags
- Reject if risk score > 50 (scale: 0 = safest, 100 = riskiest)
- Reject if top 10 holders own > 35% of token supply
- Reject if any single holder owns > 15%
- Reject if token has fewer than 100 holders
- Reject if token has freeze authority (creator can freeze your tokens)
- Reject if token has mint authority (infinite supply possible)
- Reject if metadata is mutable (token name/symbol can be changed)

**Stage 3 — On-chain LP lock analysis** (the most sophisticated check):

- Query Solana RPC for the actual LP token distribution
- Classify each LP holder as burned, protocol-locked, contract-locked, or unlocked
- Reject if effective safe LP percentage < 50%
- Reject if any single wallet can pull > 25% of pool liquidity

This three-layer approach is necessary because each layer catches things the others miss. The Raydium API might report 95% LP burn, but the remaining 5% could be held by a single wallet that can rug-pull it. RugCheck might give a token a clean score, but the LP distribution could be dangerous. You need all three.

After filtering, the surviving pools are typically well-established meme tokens with genuine trading activity, locked liquidity, and distributed token ownership. Not safe investments by any means, but the best risk/reward available.

## Pool Scoring: Predicted Net Return Model

Pools that survive safety filtering get scored on a 0-100 scale. The scoring is specifically designed for LP fee farming, and anchored on a single question: **after accounting for volatility costs and slippage, will this position make money over 7 days?**

### The Key Insight

**As an LP, you earn fees from trading volume but lose money to volatility.**

Every time arbitrageurs rebalance the pool against external price movements, LPs pay a cost. This cost is formally known as **LVR (Loss-Versus-Rebalancing)**, from the paper by [Milionis et al. (2022)](https://arxiv.org/abs/2208.06046). For a constant-product AMM like Raydium V4:

$$\text{LVR rate} = \frac{\sigma^2}{8} \text{ per unit time}$$

where σ is the asset's volatility. This is the "Black-Scholes formula for AMMs" — a clean, continuous-time result that tells you exactly how much being an LP costs as a function of volatility.

The ideal pool for an LP: **high fee yield, low volatility, deep liquidity**. That combination maximizes fee income and minimizes the volatility drag.

### The Prediction Model

Before scoring, the bot builds a full P&L prediction for each pool over the configured hold period (default 7 days):

**Step 1 — Daily yield:**

$$y = \frac{r_f}{365}$$

where $r_f$ is the pool's fee APR. If the pool also has reward emissions, those are added on top.

**Step 2 — Sustainability adjustment:**

$$s = \min\!\left(1,\; \frac{\bar{f}_7}{f_1}\right)$$

where $\bar{f}_7$ is the 7-day average daily fees and $f_1$ is today's fees. If today's fees are 3× the weekly average, they're probably not sustainable. The sustainability multiplier caps the yield at the weekly average rate.

**Step 3 — Volatility estimation via multi-period Parkinson (1980):**

The bot fetches $n$ daily OHLCV candles from GeckoTerminal's free API and computes the Parkinson estimator for each day independently, then averages:

$$\hat{\sigma} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} \frac{(\ln H_i/L_i)^2}{4 \ln 2}}$$

This multi-period approach is strictly better than using a single 7-day high-low window. A single aggregate window captures the extreme high and low across *different days*, which systematically overestimates daily volatility. Averaging independent daily estimates removes this upward bias.

Falls back to single-window Parkinson from Raydium API aggregates if candles are unavailable.

**Step 4 — LVR cost:**

$$\ell = \frac{\sigma^2}{8}, \qquad \mathcal{L} = \ell \cdot T$$

where $\ell$ is the daily LVR cost (fraction of position lost per day), $\mathcal{L}$ is the total LVR cost over the hold period, and $T$ is the hold period in days.

**Step 5 — Slippage (one-time cost):**

The bot models round-trip slippage for the specific position size using the CPMM price impact formula:

$$\delta = \frac{\phi}{2} + \frac{P}{2L}, \qquad \Delta = 2\delta$$

where $\phi$ is the swap fee rate, $P$ is the position size, and $L$ is pool TVL (all in SOL).

**Step 6 — Net return:**

$$R = s \cdot y \cdot T \;-\; \frac{\sigma^2}{8}\,T \;-\; \Delta$$

This single number captures everything: yield, sustainability, volatility cost, and trading friction.

### Scoring Breakdown (0-100)

**Predicted Net Return (75 pts):**

The model's net return as a fraction of a generous target. A net return of 0.5% per day over the hold period earns full marks:

$$S = \min\!\left(75,\; \frac{R}{0.5\% \times T} \times 75\right)$$

**Pool Depth (10 pts):**

Can you enter and exit without meaningful slippage? $50K TVL = full marks.

**Data Quality (15 pts):**

How much do we trust the prediction inputs?

- +5 pts: Real price range data (vs default σ assumption)
- +5 pts: feeAPR available (vs total-APR fallback that includes rewards)
- +5 pts: 7-day fee data available (vs assuming 50% sustainability)

### Gate: Minimum Predicted Net APR

After scoring, pools must also pass a profitability gate: the annualized net return (after LVR and slippage) must exceed 30%. This prevents the bot from entering pools where fees barely cover costs.

In practice, this gate is the real filter. Meme tokens with 100%+ fee APR often have volatilities so high that the LVR cost eats all the yield. A pool with 100% fee APR and 15% daily σ has an LVR cost of ~102% APR — it's actually net-negative for LPs despite looking lucrative on paper.

## Volatility: The Real Cost of Being an LP

Most LP education focuses on **impermanent loss** — the difference between holding tokens vs providing liquidity. While IL is real (and the bot still tracks it as an exit trigger), it's actually the wrong framing for understanding LP costs.

The better framework is **LVR (Loss-Versus-Rebalancing)**, introduced by [Milionis, Moallemi, Roughgarden, and Zhang (2022)](https://arxiv.org/abs/2208.06046). LVR reframes the LP's cost not as a one-time loss at withdrawal, but as a **continuous, ongoing cost** paid to arbitrageurs every moment the external price moves.

### Why LVR Instead of IL?

IL has a problem: it depends on what the price does *at the moment you exit*. If the price returns to your entry, IL is zero. This makes it seem like timing matters, and that IL is somehow "impermanent" — a framing that has confused thousands of LPs into thinking they just need to "wait it out."

LVR tells a different story. Every time the price moves, arbitrageurs trade against the pool at stale prices. The pool systematically sells low and buys high compared to the external market. This cost accrues continuously regardless of whether the price eventually returns.

For a constant-product AMM:
$$\text{LVR rate} = \frac{\sigma^2}{8}$$

This is the fraction of pool value lost to arbitrageurs per unit time, where σ is the asset's volatility. It's elegant, it's continuous, and it scales linearly with time and quadratically with volatility.

### Measuring Volatility: The Parkinson Estimator

The LVR formula needs σ. The bot estimates it using the **multi-period Parkinson (1980) high-low volatility estimator**, averaging 7 daily candles fetched from GeckoTerminal's free API:

$$\hat{\sigma} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} \frac{(\ln H_i/L_i)^2}{4 \ln 2}}$$

Each day's high and low gives an independent variance estimate. Averaging them produces a much better σ estimate than using a single multi-day window, because an aggregate 7-day high-low captures the *extreme* range across different days — systematically overestimating daily volatility.

If daily candles aren't available (GeckoTerminal doesn't have the pool, or the pool is too new), the bot falls back to the single-window Parkinson from Raydium API aggregates, then to 24h data. Why this estimator?

1. **Efficiency**: It's 5-8x more statistically efficient than close-to-close returns for estimating true variance
2. **Theoretical alignment**: Both Parkinson and the LVR derivation assume geometric Brownian motion — the same price process
3. **Multi-period averaging**: Using n independent daily estimates removes the upward bias of a single N-day window
4. **Crypto-native**: In 24/7 crypto markets, there are no overnight gaps (the main weakness of Parkinson in traditional markets), so the estimator is essentially unbiased
5. **Free data**: GeckoTerminal provides daily OHLCV for any Solana pool at no cost (30 calls/min rate limit)

### What This Looks Like in Practice

Here's a real example from a production run:

| Pool | Fee APR | Daily σ (7×1d) | LVR APR (σ²/8 × 365) | Net APR |
|---|---|---|---|---|
| WSOL/pippin ($16M TVL) | 101% | 14.4% | 95% | **~6%** |
| monk/WSOL ($117K TVL) | 422% | 47.1% | 1013% | **-930%** |
| WSOL/MUSHU ($356K TVL) | 1353% | 112.7% | 5799% | **-5305%** |

The σ values come from averaging 7 independent daily Parkinson estimates (candle data from GeckoTerminal). This is significantly more accurate than using the single 7-day aggregate high-low, which overestimates σ because the extremes typically occur on different days.

Pippin — one of the most established meme tokens on Solana — barely breaks even. Its fee APR almost exactly equals its LVR cost. The high-APR pools are catastrophically worse: their volatilities are so extreme that the LVR cost is multiples of the fee income.

This is the central insight: **most "high APR" pools are net-negative for LPs once you account for the true cost of volatility**.

### How the Bot Manages Risk

1. **LVR-aware entry**: The prediction model rejects pools where estimated LVR exceeds fee yield. This filters out the majority of attractive-looking pools.
2. **IL threshold exit**: If realized impermanent loss exceeds 5%, the position is closed immediately as a safety valve.
3. **7-day hold with 24h re-evaluation**: Positions run for up to 7 days to amortize entry/exit slippage, but every 24 hours the bot re-runs the full safety pipeline. If a pool's fundamentals have deteriorated, the position is closed early.
4. **Stop-loss**: If total P&L drops below -15%, the position exits regardless.

## Position Management: Entry to Exit

### Entry

When the bot identifies a pool worth entering:

1. Calculate position size (equal split across available slots, capped at maximum)
2. Wrap SOL → WSOL (Raydium requires wrapped SOL)
3. Send `addLiquidity` command to the Node.js bridge
4. Bridge constructs and signs the Raydium SDK transaction
5. Transaction is submitted to Solana
6. Bot receives back the LP token mint address and amount
7. Position is registered in the position manager with entry price, timestamp, and size

The bot enforces a 24-hour cooldown before re-entering any pool it previously exited at a loss. This prevents the common trap of repeatedly entering the same deteriorating pool.

### Monitoring

Every 10 seconds, the bot:

- Queries the current pool reserves to calculate the latest price
- Computes P&L as the percentage change from entry price
- Calculates impermanent loss using the standard IL formula
- Estimates current position value in SOL
- Checks all exit conditions

Every 24 hours, positions undergo a **full safety re-evaluation**: the bot re-runs the RugCheck, LP lock analysis, and pool quality checks. If the pool would no longer pass the safety pipeline (e.g., holder concentration increased, LP tokens unlocked), the position is closed with a "Safety Re-eval" exit reason. This catches slow-developing risks that the per-second monitors wouldn't flag.

### Exit Conditions

Six independent exit triggers (first to fire wins):

| Trigger | Threshold | Rationale |
|---|---|---|
| Stop Loss | P&L ≤ -15% | Cut losses on crashed tokens |
| Take Profit | P&L ≥ +10% | Lock in gains |
| Max Hold Time | ≥ 7 days (168h) | Limit exposure duration |
| Impermanent Loss | IL ≥ 5% | Price divergence too large |
| Safety Re-eval | Fails safety pipeline | Fundamentals deteriorated |
| Ghost Detection | LP balance = 0 | Pool was rugged/exploited |

### Exit Execution

When an exit triggers:

1. Send `removeLiquidity` command to bridge (burns LP tokens, receives both tokens back)
2. Swap the non-SOL token back to SOL via Raydium (3x retry with exponential backoff for RPC failures)
3. Close the token account to reclaim ~0.002 SOL rent
4. Record the complete trade in `trade_history.jsonl` (entry/exit prices, P&L, fees, IL, hold time, exit reason)
5. Update cooldown if exited at a loss
6. Refresh wallet balance

## The Safety Stack: Three Layers of Rug Protection

Rug pulls are the #1 risk in meme token LP. Here's how the bot defends against them.

### Layer 1: LP Burn Percentage (Raydium V3 API)

When someone creates a Raydium pool, they receive LP tokens representing their initial liquidity. If they **burn** those tokens (send them to a dead address), they can never withdraw that liquidity. It's locked forever.

The Raydium V3 API provides a `burnPercent` field that shows what percentage of initial LP tokens were burned. The bot requires ≥ 50% (configurable).

**What this catches**: Pool creators who retain all LP tokens and can drain the entire pool at any time.

**What this misses**: The remaining unburned LP tokens could still be dangerous depending on who holds them.

### Layer 2: On-Chain LP Lock Analysis

This is the most technically interesting part of the bot. After confirming the API burn percentage, the bot queries Solana directly to see where the *remaining* LP tokens are held.

The `LiquidityLockAnalyzer` makes three RPC calls:

1. `getTokenSupply(lpMint)` — total LP supply
2. `getTokenLargestAccounts(lpMint)` — top ~20 LP holders
3. `getMultipleAccounts(holders)` — who owns each holder account

Then it classifies each holder into one of four categories:

- **Burned**: Sent to `1111...1111` (the Solana null address) or the common incinerator address. Gone forever.
- **Protocol-locked**: Held by Raydium's LP authority (`5Q544f...`). Part of the protocol's initial lock. Can't be withdrawn by anyone.
- **Contract-locked**: Held by a PDA (program-derived address) owned by a known time-lock contract: Streamflow, Jupiter Lock, Fluxbeam Locker, or Raydium LP Lock. These tokens are locked for a set period and can't be withdrawn early.
- **Unlocked**: Held by a regular wallet. The owner can remove this liquidity at any time.

The bot then combines the API burn percentage with the on-chain analysis:

```
effective_safe_pct = burn_percent + (safe_on_chain_pct × remaining_fraction)
```

**Example**: Pool has 95% burn. Of the remaining 5%, analysis shows 80% is in a Streamflow time-lock. So:

- Effective safe = 95% + (80% × 5%) = 99%
- Maximum any single wallet can pull = 20% of 5% = 1% of total liquidity

That's a safe pool. Compare to a pool with 60% burn where a single wallet holds 70% of the remaining LP, they could pull 70% × 40% = 28% of total liquidity in one transaction.

### Layer 3: RugCheck Token Analysis

The first two layers analyze LP token safety. Layer 3 analyzes the *token itself*:

- **Holder concentration**: If 10 wallets hold 35%+ of the token, they can coordinate a dump
- **Freeze authority**: Token creator can freeze all transfers (your LP position becomes untouchable)
- **Mint authority**: Creator can mint infinite tokens, diluting the pool
- **Copycat detection**: Impersonation tokens trying to mimic real projects
- **Risk scoring**: 0-100 composite score incorporating all factors

These three layers catch different attack vectors. I've seen pools that pass layers 1 and 2 but fail layer 3 (token has mint authority), and pools that pass layer 3 but fail layer 2 (single wallet holds most LP). You need all three.

## Real-World Performance

I've been running the bot live on Solana mainnet with real capital. Here are the numbers from 24 closed trades:

| Metric | Value |
|---|---|
| Total Trades | 24 |
| Win / Loss / Neutral | 9 / 4 / 11 |
| Total Capital Deployed | 5.21 SOL (~$443) |
| Net P&L | +0.227 SOL (+$19.28) |
| Fees Earned | +0.239 SOL (+$20.30) |
| ROI | +4.35% |

**Breakdown by exit reason:**

- Take Profit exits: 5 trades, +0.473 SOL — the big winners
- Stop Loss exits: 2 trades, -0.235 SOL — expensive but necessary
- Ghost cleanup: 11 trades, -0.019 SOL — remnants from early bugs
- Manual close: 6 trades, +0.008 SOL — neutral

The take profit hits at +94%, +94%, +25%, +24%, and +24% on $HACHI, MUSHU, and BABYAGI pools more than compensated for the stop loss hits at -42% and -35% on $HACHI and SpaceX.

**Key observation**: Fees earned (0.239 SOL) almost exactly equal net P&L (0.227 SOL). This means the strategy is working as designed — fee income is the primary return driver, with IL and stop losses as friction.

## Lessons Learned

### What Worked

1. **Strict safety filtering is worth the missed opportunities.** Of ~1,100 pools scanned, only 2-5 pass all three safety layers. That's frustrating when you see high APRs on rejected pools, but the pools that pass are genuinely safer. Zero rug pulls on entered positions.

2. **Volume/TVL ratio is the single best metric for LP returns.** High volume relative to pool size means outsized fees per unit of capital. This is more predictive than raw APR.

3. **7-day hold with 24-hour re-evaluation is the sweet spot for meme tokens.** Short hold periods (24h) can't recover entry/exit slippage — a round-trip through a Raydium pool costs at least 0.25% in swap fees, and breaking even on that in 24h requires very high net APR. But holding indefinitely is dangerous. The 7-day hold amortizes slippage while the 24h safety re-evaluation catches deteriorating conditions before they become catastrophic.

### What Didn't

1. **Ghost positions were the biggest headache.** Early versions would lose track of positions when the bridge failed mid-transaction. LP tokens existed on-chain but the bot didn't know about them. Required building LP recovery logic that scans the wallet for orphaned Raydium LP tokens on every startup.

2. **RPC reliability matters more than you think.** Free Solana RPC endpoints frequently timeout. Missing an exit due to an RPC failure while the token dumps 40% is expensive. The bot now retries all critical operations 3x with exponential backoff, and I'd strongly recommend a paid RPC provider.

3. **Balance tracking is surprisingly hard.** SOL wraps to WSOL, WSOL goes into LP, LP gets removed into SOL + token, token gets swapped to SOL, SOL gets unwrapped. Tracking "available capital" through this chain of transformations required careful accounting at every step.

## The Code

The bot is fully open-source:

**[github.com/karlokr/raydium-lp-bot](https://github.com/karlokr/raydium-lp-bot)**

It's around 4,000 lines across Python and JavaScript. The main components:

- `bot/main.py` — Orchestration loop (~1,100 lines). Pool scanning, position monitoring, exit logic, startup cleanup.
- `bot/raydium_client.py` — API client (~360 lines). Raydium V3 API + GeckoTerminal OHLCV candles for multi-period Parkinson σ.
- `bot/analysis/pool_analyzer.py` — Scoring & prediction model (~530 lines). Multi-period Parkinson volatility estimation, LVR cost model, net return prediction, position-aware slippage.
- `bot/analysis/pool_quality.py` — Safety filtering (~260 lines). Three-layer risk assessment.
- `bot/safety/liquidity_lock.py` — On-chain LP analysis (~350 lines). The RPC-based holder classification.
- `bot/safety/rugcheck.py` — RugCheck API integration. Token safety scoring.
- `bot/trading/executor.py` — Transaction execution (~400 lines). Python ↔ Node.js bridge communication.
- `bridge/raydium_sdk_bridge.js` — Raydium SDK wrapper (~1,350 lines). Liquidity add/remove, swaps, balance queries.

### Running It

```bash
git clone https://github.com/karlokr/raydium-lp-bot.git
cd raydium-lp-bot
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
npm install

# Configure .env with wallet key + RPC URL
cp .env.example .env

# Start in paper trading mode (no real transactions)
python run.py
```

**Critical**: Use a dedicated wallet funded with SOL only. Never your main wallet. Start with 0.5-1 SOL.

## What's Next

The current bot is profitable but conservative. Some directions I'm exploring:

- **Concentrated liquidity**: Raydium's CLMM pools offer higher fee yields for tighter price ranges. The LVR cost is higher inside tight ranges (higher marginal liquidity), but the fee concentration can more than compensate.
- **Dynamic exit thresholds**: Adjusting stop-loss and take-profit based on pool volatility rather than using fixed percentages. A pool with 5% daily σ should have wider stops than one with 50%.
- **Multi-pool correlation**: If $HACHI volume is surging because of a broader meme coin trend, other similar tokens might follow.
- **Real-time alert system**: Discord/Telegram notifications when positions are entered, exited, or when interesting pools appear.

The core thesis remains: in a market full of speculation, the boring strategy of providing liquidity and earning fees quietly outperforms — as long as you can measure the true cost of volatility and avoid pools where it exceeds the yield.

*This is an experimental project. It trades real money and can lose everything. Not financial advice. Review the code and understand the risks before running it.*