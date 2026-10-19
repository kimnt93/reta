# 03 — Source discovery, access audit, and collection

## 1. Evidence status and source selection

Do not interpret the prior conversation's marketplace list as verified free
bulk access. Its rankings were subjective. This planning pass checked the
primary pages linked below without creating accounts, subscribing, placing
trades, or bypassing restrictions. No complete strategy ledger was acquired.

Evidence labels used here:

- **Observed page**: page content or redirect actually read in this analysis.
- **Documented**: official documentation describes a capability; a particular
  free account/profile/export has not been tested.
- **Lead only**: present in the supplied discussion; not independently checked
  for historical access in this planning pass.

A source is approved per strategy, access mode, scope, and collection method,
not once for the entire platform. Being free to browse does not establish
export permission, complete data, or a public historical-data API.

## 2. Concrete observations from this planning pass

| Source | Checked evidence | Consequence |
| --- | --- | --- |
| cTrader Copy | [Official strategy-page guide](https://help.ctrader.com/ctrader-copy/account-and-strategy-page/) documents Positions and History tabs; History is closing deals | Strong audit candidate, not proof of freely exportable complete executions |
| cTrader Copy | [Official copying guide](https://help.ctrader.com/ctrader-copy/) documents equity-to-equity sizing, price differences, balance-driven resizing, and stock/share copying exclusion | Provider and follower histories are distinct; do not infer provider risk rules from a follower's scaled quantities |
| MQL5 Signals | [Forex listing](https://www.mql5.com/en/signals/mt4/forex) and [sample signal 2327790](https://www.mql5.com/en/signals/2327790) show statistics and paid copying; sample page asks login/registration for real-time trades | Public statistics observed; free-login detailed history, fields, and export still need testing |
| Chợ Bot | [Homepage](https://chobot.vn/) exposes bot rankings and order-book links; ranking explanation says LN12 is derived from backtests | Public ranking data is not evidence of live fills |
| Chợ Bot | [Sample orders route](https://chobot.vn/bot/4f5f5eef-bd56-4886-be28-efabcbfe5289/orders) redirected to a login URL | Guest trade history not available at that sampled route; free-login depth/permission unverified |
| Bybit Copy | [Official performance guide](https://www.bybit.com/en/help-center/article/How-to-Understand-Master-Trader-Performance) documents current/past trade fields, including quantity and entry/exit times/prices, for USDT perpetuals | Documentation evidence only; geography, profile visibility, lookback and free extraction remain unverified |
| Collective2 | [Official site](https://trade.collective2.com/) describes go-forward records, subscriber weighted-average fill re-marking, and simulated fills when subscriber fills are absent | Preserve `model_account` provenance and revisions; not every displayed trade is one real brokerage account |
| TradingView | [Official export help](https://www.tradingview.com/support/solutions/43000613680-how-to-export-strategy-data/) documents separate CSV exports for trade lists and performance summaries | Export capability documented; free-plan eligibility not established here; trade-list and summary exports are different datasets |

These observations are planning evidence, not permanent source-access grants.
Implementation must retain its own checked-at timestamps, terms references,
and artifacts because sites and entitlements change.

## 3. Complete candidate inventory from the discussion

Market labels are discovery targets from the discussion, not a guarantee
that a particular profile exposes that market or that residents may use it.
**No row below is certified as a free complete ledger.**

| Candidate / official entry | Evidence useful to audit | Status here / next action |
| --- | --- | --- |
| [cTrader Copy](https://ctrader.com/copy) | Provider closing deals, open positions, instrument/quantity semantics | Documented; audit guest/free-login strategy pages first |
| [MQL5 Signals](https://www.mql5.com/en/signals) | Forex/CFD signal-account histories | Observed listing/profile; audit detailed history after free login |
| [Collective2](https://trade.collective2.com/) | US equities, futures, options, forex signals/model records | Observed official explanation; inspect permitted history/export and re-marks |
| [Myfxbook](https://www.myfxbook.com/) | Public forex/CFD account histories | Lead only; find disclosed history, not private performance-only accounts |
| [FX Blue](https://www.fxblue.com/) | Published account reports | Lead only; test privacy/delay, start state and export rights |
| [Bybit Copy](https://www.bybit.com/copyTrade/) | USDT perpetual position histories | Documented; audit actual profiles and regional access |
| [OKX Copy](https://www.okx.com/copy-trading) | Crypto spot/futures strategy records | Lead only; audit fields, lookback and permission |
| [Binance Copy](https://www.binance.com/en/copy-trading) | Crypto portfolio history | Lead only; check profile/login/region and complete trade semantics |
| [Bitget Copy](https://www.bitget.com/copy-trading) | Crypto trader history | Lead only; distinguish aggregate performance from event-level data |
| [Chợ Bot](https://chobot.vn/) | VN30 futures backtest/live/order-book views | Observed public homepage + login redirect; user-assisted free-login audit |
| [Darwinex](https://www.darwinex.com/) | Trading journals/exposure/performance | Lead only; establish deliberate hidden/delayed coverage before use |
| [cTrader bot Store](https://ctrader.com/bots) | Product descriptions, backtests, linked monitoring | Lead only; discover linked records; do not confuse Store with Copy |
| [MQL5 Market](https://www.mql5.com/en/market) | EA descriptions, tests, monitoring links | Lead only; prioritize linked Signals, not screenshots as fills |
| [TradingView Scripts](https://vn.tradingview.com/scripts/) | Public strategy code and simulated behavior where accessible | Export documented separately; declare white-box vs black-box and plan eligibility |
| [eToro](https://www.etoro.com/discover/people) | Holdings, performance and trade summaries | Lead only; point holdings may be insufficient for transition labels |
| [Tradetron](https://tradetron.tech/) | India-market deployment/performance data | Lead only; historical orders and free eligibility unverified |
| [ZuluTrade](https://www.zulutrade.com/) | Provider trade/performance records | Lead only; audit provider/follower differences and privacy |
| [SignalStart](https://www.signalstart.com/) | Signal-account monitoring | Lead only; detailed fields/export/free path unverified |
| [Composer](https://www.composer.trade/) | US stock/ETF compositions and simulations | Lead only; may serve as a declared rule-reference exercise, not live fills |

Japan-specific marketplaces: **unresolved discovery work**, not a verified
source family. Include Japanese queries and venue filters in discovery;
require the same audit. Japanese seller identity or USDJPY trading does not
establish Japan equities/futures coverage. Commodities must distinguish
exchange contracts from CFDs; VN30 front-month continuous displays require
expiry/roll mapping before instrument-level reconstruction.

## 4. Discovery implementation

Inputs: explicit source URL, platform/strategy name, local export reference,
or a research objective with configured search capability.

1. Resolve user URLs safely, normalize platform/strategy identity, and retain
   original URLs. Follow only authorized public links/origins.
2. Search a small versioned source registry and, when configured, a search
   provider using market/timeframe/modality constraints. Search results are
   discovery evidence, not source-access proof.
3. On storefront pages, extract permitted outbound monitoring links. Keep the
   storefront and linked monitor as distinct sources with an evidence edge.
4. Deduplicate candidate identity without merging different accounts or
   renamed providers. Freeze the selected research universe before fitting.
5. Order candidates lexicographically: permission/free-path confidence,
   behavior modality, required-field presence, history suitability, then
   operational cost. Do not fabricate precise numerical ranking scores.
6. Return bounded candidates, discovery artifacts, and unresolved questions.
   If search is unavailable, continue with registry/user URLs; a fully broad
   request with no usable candidates returns a missing-search/source action.

A new domain can enter discovery without a bespoke parser, but collection
requires a supported audited adapter, a user-supplied export, or a reviewed
connector task. An LLM must not invent an endpoint and call it a connector.

## 5. AccessProbe procedure

Use the contract in [02](02-data-contracts.md). Implement each check as an
observable action with evidence, including rejected and unknown outcomes.

1. **Identity and permission:** record source/profile/account role, terms or
   API/export policy, intended local research use, rate limits and allowed
   method. Robots directives are relevant but are not a data license.
   If permission cannot be established, record unknown and seek review.
2. **Guest check:** inspect an actual profile/history surface; detect login,
   CAPTCHA, payment, private-history and geography restrictions. Save a
   safe response/screenshot reference and final redirect, not just HTTP 200.
3. **Free login check:** only if policy permits, pause for user login to an
   isolated local profile. Do not register accounts or purchase services.
   Re-run the same profile checks under that profile; record the changed
   access mode without serializing cookies or user credentials.
4. **Field semantics:** verify symbol/venue, side versus position direction,
   entry/exit/event time precision and timezone, native size versus lots,
   fees/funding/PnL currencies, realized versus unrealized values, and
   provider versus subscriber identity. Unknown semantics are blockers for
   the corresponding claim, even if a table contains numeric values.
5. **Depth and pagination:** inspect first and subsequent pages, an older
   date boundary, reported totals, accessible window and cursor termination.
   Stable duplicate-page detection must stop a loop with `partial` coverage,
   not claim completion. Never use an unbounded paginator.
6. **Completeness:** determine whether open positions, partial fills, cash
   flows, cancelled orders, source revisions and window-crossing trades are
   included. A closed-trades table alone is not a complete initial-position
   ledger. Record publisher delays and gaps as observed or unknown.
7. **Export path:** prefer documented permitted API/CSV/export. Visible web
   app requests may explain the page, but private/internal endpoints are not
   presumed public APIs and account APIs do not imply access to all traders.
8. **Verdict:** approved only for the verified method/window/modalities with
   known permission and no payment. Otherwise needs action, rejected, or
   unknown. Store explicit reasons and downstream claim limitations.

Example probe outcome for the sampled Chợ Bot route, expressed as a design
example from an observed redirect: `access_mode=guest`,
`verdict=needs_user_action`, `reason_codes=[login_required]`,
`available_modalities=[]`, `pagination_status=unknown`. Do not set
`reported_total_rows=0` or infer `source_type=live` from that response.

## 6. Ingestion paths and priority connectors

### Path A — local authorized import (first complete path)

Support CSV, JSON and Parquet with an ImportManifest: file reference/hash,
source identity, permission basis, source type/account role, observation kind,
column mapping, timestamp format/zone/precision, quantity/lot mapping,
currency semantics, window/completeness declaration, known-start state,
revision policy, and instrument-spec references. The manifest is mandatory;
a guessed timezone or size unit cannot support an absolute-position claim.
Preview invalid rows with source locators; fail required-column mapping and
quarantine explicitly rejected rows with counts. Do not silently discard bad
rows and call the resulting dataset complete.

### Path B — one audited online connector

Audit cTrader Copy, MQL5 Signals, Bybit, Collective2, and Chợ Bot first. Select
the **first actually approved and adequate source**, not a platform hardcoded
as accessible by this document. Documented official access paths beat brittle
DOM scraping. Start with one strategy/profile, then a small permitted sample.
After two comparable captures, prove pagination, revision detection, replay
and raw-to-normalized lineage before increasing breadth.

### Path C — source breadth

Add the remaining priority connectors after the online vertical gate; every
connector declares its exact supported modalities. Promote other inventory
entries only after their own audits. Generic import remains available for
permitted exports where ongoing automated collection is disallowed. These
are real adapters with captured fixtures, not empty classes for every site.

Connector application protocol:

```text
discover(query, constraints) -> SourceCandidate[]
audit(candidate, policy, profile_ref?) -> AccessProbe
collect(approved_probe, window, cursor?, remaining_budget) -> CapturePage
```

`CapturePage` contains raw artifact refs, source identity, evidence records,
reported/observed counts, continuation token, scope/coverage, capture time,
limitations and consumed resources. Continuation tokens remain local if they
contain secrets. Bounded backoff for transient errors respects the shared
request budget; payment/privacy denials are not transient errors.

## 7. Market data is a separate acquisition problem

Strategy history is insufficient without matching causal inputs. A market
provider must declare venue/broker mapping, timezone/session calendar,
bar-open/close conventions, finality, quote/price basis, adjustment policy,
precision, coverage, revision policy and permitted retention/redistribution.

For a first real proof, prefer an authorized export of matching instrument
bars or a documented no-payment market-data path with adequate history.
Crypto venue bars are not interchangeable across exchanges. Forex/CFD
broker quotes can differ enough to change triggers. US/JP equities need
exchange calendars and corporate actions. Futures need actual contracts,
multipliers, expiry and explicit rolls; back-adjusted continuous levels are
not executable contract prices. Do not promise a universal free provider.

Map behavior to bars using declared timing uncertainty and timezone rules;
market feature joins must be backward on availability time. A delayed
publication of a historical trade can be used as a retrospective label, but
it was not a real-time model input at the trade's event time. Keep the two
uses separate. Unknown market data/license blocks that claim, not discovery.

## 8. Acceptance and handoff evidence

- Login/paywall/empty-history responses yield distinct typed results.
- A two-page fixture with overlapping source IDs produces one correct
  semantic dataset without deleting two genuinely identical partial fills.
- A page cap produces partial coverage and a resumable cursor; resume cannot
  exceed the original byte/page budget or forget earlier gaps.
- A changed source row appends a revision and updates a versioned dataset;
  the earlier run remains reproducible from its original artifacts.
- At least one real authorized profile/export produces raw artifacts,
  normalized rows, access evidence and market alignment. If not available,
  mark the real-source gate blocked and finish the offline implementation;
  never fabricate a successful connector demonstration.
- The source report lists every requested market/source as usable, rejected,
  blocked, or unverified. A top-performance-only sample discloses survivorship
  bias; cTrader's documented active-provider list is not a census of failures.
- Do not start model fitting until evidence quality/identifiability assessment
  has accepted the requested claim or issued a narrower explicit limitation.
