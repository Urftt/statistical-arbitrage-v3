export interface GlossaryEntry {
  term: string;
  aka: string;
  definition: string;
}

export const GLOSSARY_TERMS: readonly GlossaryEntry[] = [
  {
    term: 'Statistical Arbitrage',
    aka: 'stat arb',
    definition:
      "A quantitative trading strategy that exploits statistical relationships between assets. Unlike traditional arbitrage (risk-free profit), stat arb relies on historical patterns that may not hold in the future — hence the 'statistical' qualifier.",
  },
  {
    term: 'Pairs Trading',
    aka: 'pair trading',
    definition:
      'A market-neutral strategy that trades two cointegrated assets. When their spread deviates from the historical mean, you go long the underperformer and short the outperformer, betting that the spread reverts.',
  },
  {
    term: 'Correlation',
    aka: 'Pearson correlation',
    definition:
      'A measure of linear co-movement between two series, ranging from -1 to +1. High correlation means assets tend to move in the same direction, but says nothing about whether the gap between them is stable. Correlation \u2260 cointegration.',
  },
  {
    term: 'Cointegration',
    aka: '',
    definition:
      'A statistical property where a linear combination of two non-stationary series produces a stationary series (the spread). Unlike correlation, cointegration implies a long-run equilibrium — the spread always reverts to its mean. This is the foundation of pairs trading.',
  },
  {
    term: 'Stationarity',
    aka: 'stationary process',
    definition:
      "A time series whose statistical properties (mean, variance) don't change over time. Stock prices are non-stationary (they trend), but the spread between cointegrated assets should be stationary — oscillating around a constant mean.",
  },
  {
    term: 'Mean Reversion',
    aka: '',
    definition:
      'The tendency of a series to return to its average value over time. A mean-reverting spread is the core requirement for pairs trading — when it deviates, you trade expecting it to come back.',
  },
  {
    term: 'ADF Test',
    aka: 'Augmented Dickey-Fuller test',
    definition:
      'A statistical test for stationarity. The null hypothesis is that the series has a unit root (is non-stationary). A sufficiently negative test statistic (low p-value) rejects the null — evidence that the series is stationary. Used to test the spread in the Engle-Granger cointegration procedure.',
  },
  {
    term: 'p-value',
    aka: '',
    definition:
      "The probability of observing results at least as extreme as the test statistic, assuming the null hypothesis is true. In cointegration testing, p < 0.05 means there's less than 5% chance the spread is non-stationary — strong evidence for cointegration.",
  },
  {
    term: 'Hedge Ratio',
    aka: 'beta, \u03B2',
    definition:
      'The ratio of positions in the two assets that minimizes portfolio variance. Calculated from OLS regression: if \u03B2 = 20, you hold \u20AC20 of asset 1 for every \u20AC1 of asset 2. This ratio constructs the most stationary spread possible.',
  },
  {
    term: 'OLS Regression',
    aka: 'Ordinary Least Squares',
    definition:
      'A method to fit a straight line through data by minimizing the sum of squared differences between actual and predicted values. In pairs trading, OLS finds the hedge ratio (slope) and intercept that best describe the relationship between two asset prices.',
  },
  {
    term: 'Spread',
    aka: 'residuals',
    definition:
      "The difference between one asset's price and the hedge ratio times the other asset's price: spread = price\u2081 \u2212 \u03B2 \u00D7 price\u2082. When cointegrated, this spread is stationary and oscillates around a mean — deviations are your trading signals.",
  },
  {
    term: 'Z-Score',
    aka: 'standardized score',
    definition:
      "The number of standard deviations the spread is from its rolling mean: z = (spread \u2212 mean) / std. A z-score of +2 means the spread is 2\u03C3 above average — unusually wide. Z-scores standardize the spread so you can set universal entry/exit thresholds regardless of the spread's scale.",
  },
  {
    term: 'Standard Deviation',
    aka: '\u03C3, sigma',
    definition:
      "A measure of how spread out values are from their mean. In pairs trading, \u03C3 bands around the spread show what 'normal' variability looks like. Moves beyond \u00B12\u03C3 are statistically unusual — potential trade signals.",
  },
  {
    term: 'Half-Life',
    aka: 'mean reversion speed',
    definition:
      "The expected number of periods for the spread to revert halfway back to its mean. Calculated from the Ornstein-Uhlenbeck process. A half-life of 10 means if the spread is 2\u03C3 away, you'd expect it to be ~1\u03C3 away after 10 periods. Shorter half-lives mean faster reversion — better for trading.",
  },
  {
    term: 'Entry Signal',
    aka: 'entry threshold',
    definition:
      'The z-score level that triggers opening a position. Typically \u00B12.0\u03C3. When z < \u22122: go long the spread (expect widening). When z > +2: go short the spread (expect narrowing). Lower thresholds generate more trades but more false positives.',
  },
  {
    term: 'Exit Signal',
    aka: 'exit threshold',
    definition:
      'The z-score level that triggers closing a position. Typically \u00B10.5\u03C3 (near zero). When the spread returns to near its mean, the trade has played out. Exiting too early leaves money on the table; too late risks the spread reversing again.',
  },
  {
    term: 'Engle-Granger Test',
    aka: 'EG test',
    definition:
      'A two-step cointegration test: (1) regress one asset on the other to get the hedge ratio and residuals (spread), (2) test the residuals for stationarity using the ADF test. If the residuals are stationary, the assets are cointegrated. Note: the test is order-sensitive — switching which asset is dependent can change results.',
  },
  {
    term: 'Position Sizing',
    aka: 'position size',
    definition:
      'The fraction of your total capital allocated to a single trade. Larger positions amplify both gains and losses. Proper position sizing is a key risk management tool — risking too much on one trade can wipe out your account even with a winning strategy.',
  },
  {
    term: 'Equity Curve',
    aka: 'cumulative PnL',
    definition:
      'A chart showing how your portfolio value changes over time as trades are opened and closed. A healthy equity curve trends upward with manageable drawdowns. Steep drops indicate periods of heavy losses.',
  },
  {
    term: 'Backtesting',
    aka: 'backtest',
    definition:
      'Simulating a trading strategy on historical data to evaluate how it would have performed. A backtest replays past prices, generates signals, executes virtual trades, and computes performance metrics. Essential for validating a strategy before risking real money.',
  },
  {
    term: 'Sharpe Ratio',
    aka: 'risk-adjusted return',
    definition:
      'A measure of risk-adjusted performance: (mean return − risk-free rate) / standard deviation of returns. A Sharpe above 1.0 is decent, above 2.0 is strong. It tells you how much return you earn per unit of risk taken.',
  },
  {
    term: 'Maximum Drawdown',
    aka: 'max drawdown, MDD',
    definition:
      'The largest peak-to-trough decline in your equity curve, expressed as a percentage. A max drawdown of 20% means at some point you lost 20% from your highest equity. Lower is better — large drawdowns are psychologically and financially devastating.',
  },
  {
    term: 'Win Rate',
    aka: 'hit rate',
    definition:
      'The percentage of trades that are profitable. A win rate of 60% means 6 out of 10 trades made money. Win rate alone doesn\u2019t determine profitability — you also need to consider the average win size vs. average loss size (profit factor).',
  },
  {
    term: 'Profit Factor',
    aka: '',
    definition:
      'The ratio of gross profits to gross losses. A profit factor above 1.0 means the strategy is profitable overall. Above 1.5 is good, above 2.0 is excellent. Unlike win rate, profit factor accounts for both frequency and magnitude of wins vs. losses.',
  },
  {
    term: 'Overfitting',
    aka: 'curve fitting',
    definition:
      'When a model or strategy is tuned so precisely to historical data that it captures noise rather than genuine patterns. An overfit strategy looks amazing on past data but fails on new data. More parameters generally means higher overfitting risk.',
  },
  {
    term: 'In-Sample',
    aka: 'training data',
    definition:
      'The historical data period used to develop and optimize a strategy. Performance on in-sample data is biased upward because the strategy was designed to fit this data. Always validate with out-of-sample data.',
  },
  {
    term: 'Out-of-Sample',
    aka: 'test data, OOS',
    definition:
      'Historical data that was NOT used during strategy development or optimization. Out-of-sample performance is a more honest estimate of how a strategy will perform in the future. A large gap between in-sample and out-of-sample results is a red flag for overfitting.',
  },
] as const;

type GlossaryTermInput = string | Pick<GlossaryEntry, 'term'>;

function resolveTerm(input: GlossaryTermInput): string {
  return typeof input === 'string' ? input : input.term;
}

export function getGlossarySlug(input: GlossaryTermInput): string {
  return resolveTerm(input).toLowerCase().replaceAll(' ', '-').replaceAll('/', '-');
}

export function getGlossaryId(input: GlossaryTermInput): string {
  return `glossary-${getGlossarySlug(input)}`;
}

export function getGlossaryHref(input: GlossaryTermInput): string {
  return `/glossary#${getGlossaryId(input)}`;
}

export function getGlossaryAliases(entry: GlossaryEntry): string[] {
  return entry.aka
    .split(',')
    .map((alias) => alias.trim())
    .filter(Boolean);
}

export function glossaryMatchesQuery(entry: GlossaryEntry, query: string): boolean {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) return true;
  return [entry.term, entry.aka, entry.definition].some((value) =>
    value.toLowerCase().includes(normalizedQuery)
  );
}
