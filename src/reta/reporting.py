"""Human-readable financial results, separate from alpha fidelity gates."""

from html import escape
from typing import Any


def _format(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:,.6f}"
    return escape(str(value)).replace("|", "\\|").replace("\n", " ")


def backtest_markdown(result: dict[str, Any]) -> str:
    lines = ["## Backtesting", ""]
    if result["status"] == "not_run":
        lines.extend([f"Not run: {_format(result['reason'])}", ""])
        return "\n".join(lines)
    engine = result["engine"]
    config = result["config"]
    lines.extend(
        [
            f"Engine: **{engine['name']} {engine['version']}**. "
            "Financial simulation is diagnostic, not a model-promotion gate.",
            "",
            "### Assumptions",
            "",
            "| Setting | Value |",
            "| --- | --- |",
            "| Initial cash per instrument | "
            f"{_format(config['initial_cash'])} |",
            "| Currency label (no FX conversion) | "
            f"{_format(config['currency'])} |",
            f"| Fees (bps) | {_format(config['fees_bps'])} |",
            "| Fixed fee per filled net order | "
            f"{_format(config['fixed_fee'])} |",
            f"| Slippage (bps) | {_format(config['slippage_bps'])} |",
            "| Periods per year for Sharpe | "
            f"{_format(config['periods_per_year'])} |",
            "",
        ]
    )
    for assumption in result["assumptions"]:
        lines.append(f"- {assumption}.")
    lines.extend(["", "### Results", ""])
    instruments = set()
    for scope in result["scopes"]:
        instruments.update(
            item["instrument_id"] for item in scope["instruments"]
        )
    for instrument in sorted(instruments):
        lines.extend(_instrument_table(result, instrument))
    lines.extend(
        [
            "Artifacts: `backtest.json`, `backtest_equity.parquet`, "
            "`backtest_orders.parquet`, `backtest_trades.parquet`, "
            "`backtest_rejections.parquet`.",
            "",
            "Open trades are marked, not forcibly closed. "
            "Missing future opens remain pending. "
            "`n/a` ratios are explained in backtest.json.",
            "",
        ]
    )
    return "\n".join(lines)


def _instrument_table(result: dict[str, Any], instrument: str) -> list[str]:
    scopes = []
    for scope in result["scopes"]:
        for item in scope["instruments"]:
            if item["instrument_id"] == instrument:
                scopes.append((scope["scope"], item))
    names = [
        "Full history" if name == "full" else "Held-out (fresh flat book)"
        for name, _ in scopes
    ]
    lines = [
        f"#### {_format(instrument)}",
        "",
        "| Metric | " + " | ".join(names) + " |",
        "| --- | " + " | ".join("---" for _ in names) + " |",
    ]
    fields = [
        ("Status", "status"),
        ("Start", "start_ts"),
        ("End", "end_ts"),
        ("Bars", "bars"),
        ("Initial cash", "initial_cash"),
        ("Final equity", "final_equity"),
        ("Net PnL", "net_pnl"),
        ("Total return (%)", "total_return_pct"),
        ("Maximum drawdown (%)", "max_drawdown_pct"),
        ("Total fees", "total_fees"),
        ("Filled orders", "filled_orders"),
        ("Rejected attempts", "rejected_orders"),
        ("Ignored unmet targets", "ignored_unfilled_orders"),
        ("All unfilled target attempts", "unfilled_orders"),
        ("Closed trades", "closed_trades"),
        ("Open trades", "open_trades"),
        ("Realized PnL", "realized_pnl"),
        ("Open-trade PnL", "open_trade_pnl"),
        ("Closed-trade win rate (%)", "closed_win_rate_pct"),
        ("Closed-trade profit factor", "profit_factor"),
        ("Annualized Sharpe", "sharpe_ratio"),
        ("Pending end-of-data targets", "pending_targets"),
    ]
    for label, key in fields:
        values = " | ".join(_format(item[key]) for _, item in scopes)
        lines.append(f"| {label} | {values} |")
    return [*lines, ""]
