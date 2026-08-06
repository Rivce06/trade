import matplotlib
# Set non-interactive backend FIRST before any other imports
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import datetime
import pandas as pd
import backtrader as bt
import yfinance as yf
import quantstats as qs


# ----------------------------
# Strategy Definition
# ----------------------------
class MACrossoverStrategy(bt.Strategy):
    params = dict(
        fast_period=10,
        slow_period=50,
        risk_per_trade=0.01,       # 1% of account equity risked per trade
        max_daily_loss_pct=0.03,   # stop trading for the day after -3% equity
        max_consecutive_losses=3,  # stop trading for the day after 3 losses
        stop_loss_pct=0.02,        # 2% stop loss from entry price
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.p.fast_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.p.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

        self.order = None
        self.stop_price = None

        # Daily risk tracking
        self.day_start_equity = self.broker.getvalue()
        self.current_day = None
        self.consecutive_losses = 0
        self.trading_halted_today = False

        # Equity curve tracking (for manual plotting + quantstats)
        self.equity_curve = []
        self.dates = []

    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} | {txt}")

    def next(self):
        # --- Track equity curve every bar ---
        self.equity_curve.append(self.broker.getvalue())
        self.dates.append(self.datas[0].datetime.date(0))

        # --- Reset daily tracking on a new day ---
        today = self.datas[0].datetime.date(0)
        if today != self.current_day:
            self.current_day = today
            self.day_start_equity = self.broker.getvalue()

            # Reset daily protections
            self.trading_halted_today = False
            self.consecutive_losses = 0

        # --- Check daily loss limit ---
        equity_now = self.broker.getvalue()
        daily_pnl_pct = (equity_now - self.day_start_equity) / self.day_start_equity
        if daily_pnl_pct <= -self.p.max_daily_loss_pct:
            if not self.trading_halted_today:
                self.log(f"Daily loss limit hit ({daily_pnl_pct:.2%}). No more trades today.")
            self.trading_halted_today = True

        if self.trading_halted_today:
            return

        if self.consecutive_losses >= self.p.max_consecutive_losses:
            return

        if self.order:
            return

        # --- Entry logic ---
        if not self.position:
            if self.crossover > 0:  # fast crossed above slow -> buy signal
                entry_price = self.data.close[0]
                stop_price = entry_price * (1 - self.p.stop_loss_pct)
                risk_per_share = entry_price - stop_price

                account_value = self.broker.getvalue()
                dollar_risk = account_value * self.p.risk_per_trade
                size = int(dollar_risk / risk_per_share) if risk_per_share > 0 else 0

                if size > 0:
                    self.stop_price = stop_price
                    self.order = self.buy(size=size)
                    self.log(f"BUY signal | price={entry_price:.2f} size={size} stop={stop_price:.2f}")

        # --- Exit logic ---
        else:
            if self.crossover < 0:  # fast crossed below slow -> exit
                self.order = self.close()
                self.log(f"SELL signal (crossover) | price={self.data.close[0]:.2f}")
            elif self.data.close[0] <= self.stop_price:
                self.order = self.close()
                self.log(f"STOP LOSS hit | price={self.data.close[0]:.2f}")

    def notify_trade(self, trade):
        if trade.isclosed:
            if trade.pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
            self.log(f"TRADE CLOSED | pnl={trade.pnl:.2f} | consecutive_losses={self.consecutive_losses}")

    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order failed/cancelled")
            self.order = None


# ----------------------------
# Run Backtest
# ----------------------------
if __name__ == "__main__":
    TICKER = "SPY"

    cerebro = bt.Cerebro()
    cerebro.addstrategy(MACrossoverStrategy)

    # Performance analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name="sharpe", riskfreerate=0.0)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

    # Disable multi-level index to avoid pandas tuple column errors
    df = yf.download(TICKER, start="2020-01-01", end="2025-01-01", multi_level_index=False)

    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    starting_cash = 10000
    cerebro.broker.setcash(starting_cash)
    cerebro.broker.setcommission(commission=0.001)

    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")

    # --- Actually run the backtest and capture the strategy instance ---
    results = cerebro.run()
    strat = results[0]

    final_value = cerebro.broker.getvalue()

    print("=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    print(f"Starting Portfolio : ${starting_cash:,.2f}")
    print(f"Final Portfolio    : ${final_value:,.2f}")
    print(f"Net Profit         : ${final_value - starting_cash:,.2f}")
    print()

    # ---------- Returns ----------
    returns = strat.analyzers.returns.get_analysis()
    print("RETURNS")
    print(f"Total Return       : {returns['rtot'] * 100:.2f}%")
    print(f"Annual Return      : {returns['rnorm100']:.2f}%")
    print()

    # ---------- Sharpe ----------
    sharpe = strat.analyzers.sharpe.get_analysis()
    print("RISK")
    print(f"Sharpe Ratio       : {sharpe.get('sharperatio', 'N/A')}")
    print()

    # ---------- Drawdown ----------
    dd = strat.analyzers.drawdown.get_analysis()
    print("DRAWDOWN")
    print(f"Max Drawdown       : {dd.max.drawdown:.2f}%")
    print(f"Max Money Down     : ${dd.max.moneydown:,.2f}")
    print(f"Longest Drawdown   : {dd.max.len} bars")
    print()

    # ---------- SQN ----------
    sqn = strat.analyzers.sqn.get_analysis()
    print("SYSTEM QUALITY")
    print(f"SQN                : {sqn.get('sqn', 'N/A')}")
    print()

    # ---------- Trades ----------
    trades = strat.analyzers.trades.get_analysis()
    if trades.total.total > 0:
        won = trades.won.total
        lost = trades.lost.total
        total = trades.total.closed

        print("TRADES")
        print(f"Closed Trades      : {total}")
        print(f"Winners            : {won}")
        print(f"Losers             : {lost}")

        if total > 0:
            win_rate = won / total * 100
            print(f"Win Rate           : {win_rate:.2f}%")

        if won > 0:
            print(f"Average Win        : ${trades.won.pnl.average:.2f}")
        if lost > 0:
            print(f"Average Loss       : ${trades.lost.pnl.average:.2f}")
        print(f"Net PnL            : ${trades.pnl.net.total:.2f}")
    else:
        print("TRADES")
        print("No closed trades in this backtest period.")

    print("=" * 60)

    # Plot equity curve manually — no TkAgg / GUI backend involved at all
    plt.figure(figsize=(10, 5))
    plt.plot(strat.dates, strat.equity_curve)
    plt.title(f"Equity Curve - MA Crossover Strategy ({TICKER})")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value ($)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("backtest_results.png")
    print("Plot saved as backtest_results.png")

    # ----------------------------
    # QuantStats Tear Sheet
    # ----------------------------
    # Build a daily-indexed equity series from the strategy's tracked curve
    equity_series = pd.Series(
        data=strat.equity_curve,
        index=pd.to_datetime(strat.dates),
    )

    # Collapse to one value per calendar day (in case of any duplicate bars)
    equity_series = equity_series[~equity_series.index.duplicated(keep="last")]

    # Convert equity levels -> daily returns, which is what quantstats expects
    daily_returns = equity_series.pct_change().dropna()

    # Benchmark: buy-and-hold the same ticker over the same period, for comparison
    qs.extend_pandas()
    report_path = f"tearsheet_{TICKER}.html"
    qs.reports.html(
        daily_returns,
        benchmark=TICKER,
        output=report_path,
        title=f"MA Crossover Strategy - {TICKER}",
    )
    print(f"QuantStats tear sheet saved as {report_path}")