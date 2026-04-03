from pydantic import BaseModel
'''
This file defines the data models used for 
interacting with the financial data APIs and for 
structuring the agent's state and analysis. It includes models for price data, financial statements, financial metrics, insider trades, company news, company facts, and the agent's portfolio and analysis outputs.
'''

class Price(BaseModel):
    open: float
    close: float
    high: float
    low: float
    volume: int
    time: str


class PriceResponse(BaseModel):
    ticker: str
    prices: list[Price]

class IncomeStatement(BaseModel):
    ticker: str
    report_period: str
    fiscal_period: str
    period: str
    currency: str
    accession_number: str
    filing_url: str
    revenue: float | None
    cost_of_revenue: float | None
    gross_profit: float | None
    operating_expenses: float | None
    selling_general_and_administrative_expenses: float | None
    research_and_development_expenses: float | None
    operating_income: float | None
    interest_expense: float | None
    ebit: float | None
    income_tax_expense: float | None

    net_income: float | None
    net_income_common_stock: float | None
    preferred_dividends: float | None
    

class IncomeStatementResponse(BaseModel):
    income_statements: list[IncomeStatement]

class BalanceSheet(BaseModel):
    ticker: str
    report_period: str
    fiscal_period: str
    period: str
    currency: str
    accession_number: str
    filing_url: str
    total_assets: float | None
    current_assets: float | None
    cash_and_equivalents: float | None
    trade_and_non_trade_receivables: float | None
    non_current_assets: float | None
    property_plant_and_equipment: float | None
    total_liabilities: float | None
    total_equity: float | None

class BalanceSheetResponse(BaseModel):
    balance_sheets: list[BalanceSheet]

class CashFlowStatement(BaseModel):
    ticker: str
    report_period: str
    fiscal_period: str
    period: str
    currency: str
    accession_number: str
    filing_url: str
    operating_cash_flow: float | None
    investing_cash_flow: float | None
    financing_cash_flow: float | None
    free_cash_flow: float | None
class CashFlowStatementResponse(BaseModel):
    cash_flow_statements: list[CashFlowStatement]


class FinancialMetrics(BaseModel):
    ticker: str
    report_period: str
    period: str
    currency: str
    market_cap: float | None
    enterprise_value: float | None
    price_to_earnings_ratio: float | None
    price_to_book_ratio: float | None
    price_to_sales_ratio: float | None
    enterprise_value_to_ebitda_ratio: float | None
    enterprise_value_to_revenue_ratio: float | None
    free_cash_flow_yield: float | None
    peg_ratio: float | None
    gross_margin: float | None
    operating_margin: float | None
    net_margin: float | None
    return_on_equity: float | None
    return_on_assets: float | None
    return_on_invested_capital: float | None
    asset_turnover: float | None
    inventory_turnover: float | None
    receivables_turnover: float | None
    days_sales_outstanding: float | None
    operating_cycle: float | None
    working_capital_turnover: float | None
    current_ratio: float | None
    quick_ratio: float | None
    cash_ratio: float | None
    operating_cash_flow_ratio: float | None
    debt_to_equity: float | None
    debt_to_assets: float | None
    interest_coverage: float | None
    revenue_growth: float | None
    earnings_growth: float | None
    book_value_growth: float | None
    earnings_per_share_growth: float | None
    free_cash_flow_growth: float | None
    operating_income_growth: float | None
    ebitda_growth: float | None
    payout_ratio: float | None
    earnings_per_share: float | None
    book_value_per_share: float | None
    free_cash_flow_per_share: float | None


class FinancialMetricsResponse(BaseModel):
    financial_metrics: list[FinancialMetrics]


class LineItem(BaseModel):
    ticker: str
    report_period: str
    period: str
    currency: str

    # Allow additional fields dynamically
    model_config = {"extra": "allow"}


class LineItemResponse(BaseModel):
    search_results: list[LineItem]


class InsiderTrade(BaseModel):
    ticker: str
    issuer: str | None
    name: str | None
    title: str | None
    is_board_director: bool | None
    transaction_date: str | None
    transaction_shares: float | None
    transaction_price_per_share: float | None
    transaction_value: float | None
    shares_owned_before_transaction: float | None
    shares_owned_after_transaction: float | None
    security_title: str | None
    filing_date: str


class InsiderTradeResponse(BaseModel):
    insider_trades: list[InsiderTrade]


class CompanyNews(BaseModel):
    ticker: str | None = None
    title: str | None = None
    author: str | None = None
    source: str | None = None
    date: str | None = None
    url: str | None = None
    sentiment: str | None = None


class CompanyNewsResponse(BaseModel):
    news: list[CompanyNews]


class CompanyFacts(BaseModel):
    ticker: str
    name: str
    cik: str | None = None
    industry: str | None = None
    sector: str | None = None
    category: str | None = None
    exchange: str | None = None
    is_active: bool | None = None
    listing_date: str | None = None
    location: str | None = None
    market_cap: float | None = None
    number_of_employees: int | None = None
    sec_filings_url: str | None = None
    sic_code: str | None = None
    sic_industry: str | None = None
    sic_sector: str | None = None
    website_url: str | None = None
    weighted_average_shares: int | None = None


class CompanyFactsResponse(BaseModel):
    company_facts: CompanyFacts


class Position(BaseModel):
    cash: float = 0.0
    shares: int = 0
    ticker: str


class Portfolio(BaseModel):
    positions: dict[str, Position]  # ticker -> Position mapping
    total_cash: float = 0.0


class AnalystSignal(BaseModel):
    signal: str | None = None
    confidence: float | None = None
    reasoning: dict | str | None = None
    max_position_size: float | None = None  # For risk management signals


class TickerAnalysis(BaseModel):
    ticker: str
    analyst_signals: dict[str, AnalystSignal]  # agent_name -> signal mapping


class AgentStateData(BaseModel):
    tickers: list[str]
    portfolio: Portfolio
    start_date: str
    end_date: str
    ticker_analyses: dict[str, TickerAnalysis]  # ticker -> analysis mapping


class AgentStateMetadata(BaseModel):
    show_reasoning: bool = False
    model_config = {"extra": "allow"}
