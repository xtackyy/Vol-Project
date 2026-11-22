# Execution timing: close vs next open

Same forecasts and target weights; only the fill time changes. Costs per unit traded are unchanged (opening-auction spreads can be wider). Financing accrues half a day per segment.

| Asset | Strategy | Sharpe (close) | Sharpe (next open) | CAGR (close) | CAGR (next open) | Max DD (close) | Max DD (next open) |
|---|---|---|---|---|---|---|---|
| SPY | Vol target only | 0.57 | 0.58 | 8.1% | 8.2% | -28.9% | -28.6% |
| SPY | Vol target + signal | 0.57 | 0.58 | 8.1% | 8.2% | -28.9% | -28.6% |
| SPY | Buy & hold | 0.52 | 0.52 | 10.2% | 10.2% | -55.2% | -55.2% |
| TLT | Vol target only | 0.21 | 0.21 | 3.5% | 3.5% | -37.1% | -37.5% |
| TLT | Vol target + signal | 0.24 | 0.25 | 3.8% | 3.9% | -33.4% | -32.5% |
| TLT | Buy & hold | 0.16 | 0.16 | 3.0% | 3.0% | -48.4% | -48.4% |
| GLD | Vol target only | 0.51 | 0.52 | 7.1% | 7.3% | -40.1% | -39.1% |
| GLD | Vol target + signal | 0.51 | 0.52 | 7.1% | 7.3% | -40.1% | -39.1% |
| GLD | Buy & hold | 0.49 | 0.48 | 8.7% | 8.6% | -45.6% | -45.6% |
