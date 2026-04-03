# -*- coding: utf-8 -*-
"""
Created on Wed Sep 10 20:02:14 2025

@author: 54690
"""

import uuid
import random
import json
import sqlite3
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from openai import OpenAI
import backtrader as bt
#import akshare as ak
import yfinance as yf

client = OpenAI(api_key='sk-byJIrY43kdiR9s6m1a11B29f138a4489A2865bAc82DbA04a', base_url='https://api.gpt.ge/v1/')

# 创建SQLite数据库连接
conn = sqlite3.connect('investment_ideas.db')
c = conn.cursor()

# 创建理念数据库表
def create_database():
    c.execute('''CREATE TABLE IF NOT EXISTS investment_ideas (
                 uuid TEXT PRIMARY KEY,
                 content TEXT NOT NULL,
                 score REAL,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 parent_uuid TEXT,
                 investor_name TEXT)''')
    conn.commit()

# 系统初始化
def initialize_system():
    """初始化系统，设置日期和回测区间"""
    current_date = datetime.now()
    backtest_start = current_date - timedelta(days=30)  # 过去1个月
    return current_date, backtest_start

# 从investor_principles_en.json文件中选择初始投资理念
def select_initial_idea():
    """从investor_principles_en.json文件中选择一个投资人的理念"""
    try:
        with open('investor_principles_en.json', 'r', encoding='utf-8') as f:
            investors = json.load(f)
        
        # 随机选择一个投资人
        selected_investor = random.choice(investors)
        investor_name = selected_investor['name']
        principles = selected_investor['principles']
        
        return {
            'name': investor_name,
            'principles': principles,
            'content': f"{investor_name}的投资理念: {principles[:200]}..."  # 截取前200字符作为摘要
        }
    except Exception as e:
        print(f"读取投资人理念文件失败: {e}")
        # 返回默认理念
        return {
            'name': 'Warren Buffett',
            'principles': 'You are Warren Buffett, the Oracle of Omaha. Focus on companies with durable competitive advantages, strong balance sheets, and competent management.',
            'content': '巴菲特的护城河理论：选择具有长期竞争优势的企业'
        }

def get_quarterly_financial_data(
    stock_symbol: str, 
    current_date: str, 
    json_file_path: str = "basic_financials_series.json"
) -> dict:
    """
    从Finnhub财务数据JSON文件中提取指定股票在给定日期前一年内的季度财务数据，并以json格式返回

    参数:
        stock_symbol (str): 股票代码，例如 "AAPL"
        current_date (str): 当前日期，格式为 "YYYY-MM-DD"
        json_file_path (str): JSON文件路径

    返回:
        dict: 包含以下内容的json对象
            - code: 状态码（0成功，非0失败）
            - msg: 信息
            - data: 列表，每个元素为一个季度的财务数据字典
            - available_metrics: 可用指标及其中文描述
            - missing_metrics: 缺失指标列表
            - date_range: 实际数据时间范围
    """

    # 参数简单校验
    if not stock_symbol or not isinstance(stock_symbol, str):
        return {
            "code": 1,
            "msg": "股票代码必须是有效的字符串",
            "data": [],
            "available_metrics": {},
            "missing_metrics": [],
            "date_range": None
        }
    if not current_date or not isinstance(current_date, str):
        return {
            "code": 2,
            "msg": "当前日期必须是有效的字符串，格式为 YYYY-MM-DD",
            "data": [],
            "available_metrics": {},
            "missing_metrics": [],
            "date_range": None
        }

    current_dt = datetime.strptime(current_date, "%Y-%m-%d")
    one_year_ago = current_dt - timedelta(days=365)

    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if "quarterly" not in data:
        return {
            "code": 7,
            "msg": "JSON文件中没有找到quarterly数据",
            "data": [],
            "available_metrics": {},
            "missing_metrics": [],
            "date_range": None
        }

    quarterly_data = data["quarterly"]

    # 定义需要的指标及其描述
    required_metrics = {
        "netDebtToTotalCapital": "净债务占总资本比率",
        "pbTTM": "市净率(TTM)", 
        "peTTM": "市盈率(TTM)", 
        "roaTTM": "总资产收益率(TTM)",
        "roeTTM": "净资产收益率(TTM)",
        "totalDebtToTotalAsset": "总债务占总资产比率"
    }

    # 检查哪些指标在数据中存在
    available_metrics = {}
    missing_metrics = []
    for metric, description in required_metrics.items():
        if metric in quarterly_data:
            available_metrics[metric] = description
        else:
            missing_metrics.append(metric)

    if not available_metrics:
        return {
            "code": 8,
            "msg": "没有找到任何所需的财务指标",
            "data": [],
            "available_metrics": {},
            "missing_metrics": missing_metrics,
            "date_range": None
        }

    # 提取数据
    result_data = []
    for metric, description in available_metrics.items():
        metric_data = quarterly_data[metric]
        for item in metric_data:
            period_str = item.get("period")
            value = item.get("v")
            period_dt = datetime.strptime(period_str, "%Y-%m-%d")
            if one_year_ago <= period_dt <= current_dt:
                # 查找该period是否已存在
                found = False
                for row in result_data:
                    if row["period"] == period_str:
                        row[metric] = value
                        found = True
                        break
                if not found:
                    row = {"period": period_str, metric: value}
                    result_data.append(row)

    if not result_data:
        return {
            "code": 9,
            "msg": f"在 {current_date} 前一年内没有找到任何财务数据，搜索时间范围: {one_year_ago.strftime('%Y-%m-%d')} 到 {current_date}",
            "data": [],
            "available_metrics": available_metrics,
            "missing_metrics": missing_metrics,
            "date_range": None
        }

    # 按period排序
    for row in result_data:
        row["period"] = str(row["period"])
    result_data.sort(key=lambda x: x["period"])

    # 计算实际数据时间范围
    periods = [row["period"] for row in result_data]
    date_range = {
        "min": min(periods) if periods else None,
        "max": max(periods) if periods else None
    }

    return {
        "code": 0,
        "stock_symbol": stock_symbol,
        "msg": f"成功提取 {len(result_data)} 个季度的财务数据",
        "data": result_data,
        "available_metrics": available_metrics,
        "missing_metrics": missing_metrics,
        "date_range": date_range
    }

# 调用LLM生成决策
def llm_inference(prompt, model="deepseek-chat", temperature=0.5):
    """调用OpenAI API生成响应"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是拥有20年经验的专业金融分析师，擅长基于投资理念制定交易策略。"},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM调用失败: {e}")
        return '{"action": "HOLD", "confidence": 50, "reason": "LLM调用失败"}'

# 每日AI分析
def daily_analysis(trading_date, investment_idea, investor_name):
    """执行每日分析并生成交易决策"""
    # 选择要分析的股票
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    selected_ticker = random.choice(tickers)
    
    # 获取财务数据
    financial_data_result = get_quarterly_financial_data(selected_ticker, trading_date.strftime('%Y-%m-%d'))
    
    # 检查财务数据获取是否成功
    if financial_data_result['code'] != 0:
        print(f"获取财务数据失败: {financial_data_result['msg']}")
        # 返回默认决策
        return {
            "action": "HOLD",
            "confidence": 50,
            "reason": f"财务数据获取失败: {financial_data_result['msg']}",
            "date": trading_date.strftime('%Y-%m-%d'),
            "ticker": selected_ticker,
            "investor": investor_name
        }
    
    # 获取最新的财务数据（取最后一个季度的数据）
    if not financial_data_result['data']:
        print("没有找到财务数据")
        return {
            "action": "HOLD",
            "confidence": 50,
            "reason": "没有找到财务数据",
            "date": trading_date.strftime('%Y-%m-%d'),
            "ticker": selected_ticker,
            "investor": investor_name
        }
    
    # 获取最新的财务数据
    latest_financial_data = financial_data_result['data'][-1]
    
    # 构建财务数据摘要
    financial_summary = f"""
## 财务数据摘要
- 股票代码: {selected_ticker}
- 数据期间: {latest_financial_data.get('period', 'N/A')}
"""
    
    # 添加可用的财务指标
    available_metrics = financial_data_result['available_metrics']
    for metric, description in available_metrics.items():
        if metric in latest_financial_data:
            value = latest_financial_data[metric]
            if metric in ['peTTM', 'pb']:
                financial_summary += f"- {description}: {value:.2f}\n"
            elif metric in ['roaTTM', 'roeTTM']:
                financial_summary += f"- {description}: {value:.2f}%\n"
            elif metric in ['netDebtToTotalCapital', 'totalDebtToTotalAsset']:
                financial_summary += f"- {description}: {value:.2f}%\n"
            else:
                financial_summary += f"- {description}: {value}\n"
    
    # 构建提示词，指导LLM充当投资人角色
    prompt = f"""
## 投资决策任务
当前日期: {trading_date.strftime('%Y-%m-%d')}
分析标的: {selected_ticker} 股票

## 投资人角色设定
你现在是{investor_name}，请严格按照{investor_name}的投资理念和风格来分析这只股票。

## 投资理念
{investment_idea}

{financial_summary}

## 分析要求
1. 严格按照{investor_name}的投资理念进行分析
2. 考虑该投资人的风险偏好和投资风格
3. 基于财务数据给出明确的投资建议
4. 使用{investor_name}的语言风格和表达方式

## 输出要求
1. 严格使用JSON格式输出
2. 包含以下字段:
   - "action": 交易动作 (BUY/SELL/HOLD)
   - "confidence": 决策信心 (1-100的整数)
   - "reason": 决策理由 (使用{investor_name}的风格，不超过100字)
3. 决策必须基于提供的投资理念和财务数据
    """
    
    # 调用LLM生成决策
    decision = llm_inference(prompt, temperature=0.2)
    
    try:
        decision_data = json.loads(decision)
        # 添加元数据
        decision_data['date'] = trading_date.strftime('%Y-%m-%d')
        decision_data['ticker'] = selected_ticker 
        decision_data['investor'] = investor_name
        return decision_data
    except:
        # 如果解析失败，返回默认决策
        return {
            "action": "HOLD",
            "confidence": 50,
            "reason": "数据解析错误",
            "date": trading_date.strftime('%Y-%m-%d'),
            "ticker": selected_ticker,
            "investor": investor_name
        }

# Backtrader策略类
class PrincipleStrategy(bt.Strategy):
    """基于投资理念的Backtrader策略"""
    
    params = (
        ('principle', None),  # 投资理念
        ('decisions', []),    # 决策列表
    )
    
    def __init__(self):
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.decision_index = 0
        
    def next(self):
        if self.order:
            return
            
        if self.decision_index >= len(self.p.decisions):
            return
            
        decision = self.p.decisions[self.decision_index]
        
        if decision['action'] == 'BUY' and not self.position:
            # 买入
            self.order = self.buy()
        elif decision['action'] == 'SELL' and self.position:
            # 卖出
            self.order = self.sell()
        # HOLD情况下不做任何操作
        
        self.decision_index += 1
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行, 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f'卖出执行, 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}')
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')
            
        self.order = None
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

# 基于Backtrader的回测评价系统
def evaluate_backtest_with_backtrader(decisions, ticker='AAPL'):
    """使用Backtrader进行回测评价"""
    if not decisions:
        return 0.0
    
    try:
        # 创建Cerebro引擎
        cerebro = bt.Cerebro()
        
        # 获取股票数据
        start_date = min([datetime.strptime(d['date'], '%Y-%m-%d') for d in decisions])
        end_date = max([datetime.strptime(d['date'], '%Y-%m-%d') for d in decisions])
        
        # 获取历史数据
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date - timedelta(days=10), end=end_date + timedelta(days=10))
        
        if len(data) < 5:
            # 如果数据不足，使用模拟数据
            print(f"历史数据不足，使用简化回测")
            return evaluate_backtest_simple(decisions)
        
        # 创建数据源
        data_feed = bt.feeds.PandasData(
            dataname=data,
            datetime=None,
            open=0,
            high=1,
            low=2,
            close=3,
            volume=4,
            openinterest=-1
        )
        
        cerebro.adddata(data_feed)
        
        # 设置初始资金
        cerebro.broker.setcash(1000000.0)
        
        # 设置手续费
        cerebro.broker.setcommission(commission=0.001)
        
        # 添加策略
        cerebro.addstrategy(PrincipleStrategy, decisions=decisions)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        
        # 运行回测
        results = cerebro.run()
        strat = results[0]
        
        # 获取分析结果
        portfolio_value = cerebro.broker.getvalue()
        returns = strat.analyzers.returns.get_analysis()
        sharpe = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        
        # 计算评分
        total_return = (portfolio_value - 1000000.0) / 1000000.0
        sharpe_ratio = sharpe.get('sharperatio', 0)
        max_drawdown = drawdown.get('max', {}).get('drawdown', 0) / 100
        
        # 综合评分公式
        score = total_return * 0.5 + sharpe_ratio * 0.3 - max_drawdown * 0.2
        return round(score, 4)
        
    except Exception as e:
        print(f"Backtrader回测失败: {e}")
        return evaluate_backtest_simple(decisions)

# 简化版回测评价系统（备用）
def evaluate_backtest_simple(decisions):
    """基于每日决策计算理念得分（简化版）"""
    if not decisions:
        return 0.0
    
    portfolio_value = 1_000_000  # 初始100万
    trade_count = 0
    returns = []
    benchmark_return = 0.02  # 同期大盘收益
    
    # 简化的回测逻辑
    for decision in decisions:
        # 模拟价格波动
        daily_return = np.random.normal(0.001, 0.02)
        
        # 根据决策调整价值
        if decision['action'] == "BUY":
            # 买入决策通常预期正收益
            portfolio_value *= (1 + max(daily_return, 0) * (decision.get('confidence', 50)/100))
            trade_count += 1
        elif decision['action'] == "SELL":
            # 卖出决策通常预期避免损失
            portfolio_value *= (1 - max(-daily_return, 0) * (decision.get('confidence', 50)/100))
            trade_count += 1
        else:  # HOLD
            portfolio_value *= (1 + daily_return)
        
        returns.append(portfolio_value)
    
    # 计算绝对收益
    absolute_return = (portfolio_value - 1_000_000) / 1_000_000
    
    # 计算波动率惩罚
    returns_series = pd.Series(returns)
    volatility = returns_series.pct_change().std()
    volatility_penalty = min(volatility * 5, 0.3)  # 波动率惩罚上限30%
    
    # 交易频率惩罚
    trade_penalty = min(trade_count * 0.005, 0.15)  # 交易次数惩罚上限15%
    
    # 计算超额收益
    excess_return = absolute_return - benchmark_return
    
    # 综合评分公式
    score = absolute_return * 0.6 + excess_return * 0.4 - volatility_penalty - trade_penalty
    return round(score, 4)

# 获取数据库中得分最高的理念
def fetch_top_idea_from_db():
    """从数据库获取评分最高的理念"""
    c.execute("SELECT content, score, investor_name FROM investment_ideas ORDER BY score DESC LIMIT 1")
    result = c.fetchone()
    if result:
        return {"content": result[0], "score": result[1], "investor_name": result[2]}
    return None

# 将理念保存到数据库
def save_idea_to_db(idea_content, score=None, parent_uuid=None, investor_name=None):
    """将新理念保存到数据库"""
    idea_uuid = str(uuid.uuid4())
    c.execute("INSERT INTO investment_ideas (uuid, content, score, parent_uuid, investor_name) VALUES (?, ?, ?, ?, ?)",
              (idea_uuid, idea_content, score, parent_uuid, investor_name))
    conn.commit()
    return idea_uuid

# 理念进化引擎
def evolve_idea(current_idea, current_score, investor_name):
    """使用LLM进化投资理念"""
    # 获取历史最佳理念
    best_idea = fetch_top_idea_from_db()
    
    # 构建进化提示词
    prompt = f"""
## 投资理念进化任务
你是一位顶尖投资策略师，需要融合两个投资理念：

### 待进化理念 (当前得分: {current_score:.2f})
投资人: {investor_name}
理念内容: {current_idea}

### 历史最佳理念 (得分: {best_idea['score'] if best_idea else 'N/A'})
{best_idea['content'] if best_idea else '无'}

## 进化要求
1. 保留{investor_name}投资理念的核心优势
2. 吸收历史最佳理念的强项
3. 适应当前市场环境（{datetime.now().strftime('%Y年%m月')}）
4. 改进策略的实操性和风险控制
5. 输出完整的新理念（不超过200字）
6. 保持{investor_name}的投资风格和语言特点

## 输出格式
{{
  "new_idea": "进化后的完整投资理念",
  "investor_name": "{investor_name}"
}}
    """
    
    # 调用LLM生成新理念
    response = llm_inference(prompt, temperature=0.7)
    
    try:
        idea_data = json.loads(response)
        return idea_data.get("new_idea", "进化失败：未生成有效理念")
    except:
        return "进化失败：响应解析错误"

# 主运行流程
def run_evolution_cycle():
    """执行完整的理念进化周期"""
    # 初始化系统
    current_date, backtest_start = initialize_system()
    print(f"=== 开始理念进化周期 {datetime.now().strftime('%Y-%m-%d')} ===")
    
    # 选择初始理念
    idea_info = select_initial_idea()
    current_idea = idea_info['principles']
    investor_name = idea_info['name']
    print(f"选择的投资人: {investor_name}")
    print(f"初始理念: {current_idea[:100]}...")
    
    # 生成回测日期（简化版，仅使用10个日期点）
    trading_days = [backtest_start + timedelta(days=i*3) for i in range(10)]
    
    # 回测阶段
    decisions = []
    for trading_day in trading_days:
        print(f"分析日期: {trading_day.strftime('%Y-%m-%d')}")
        decision = daily_analysis(trading_day, current_idea, investor_name)
        decisions.append(decision)
        print(f"  决策: {decision['action']} {decision['ticker']} - {decision['reason']}")
    
    # 评价当前理念
    score = evaluate_backtest_with_backtrader(decisions)
    print(f"理念得分: {score:.4f}")
    
    # 保存当前理念到数据库
    idea_uuid = save_idea_to_db(current_idea, score, investor_name=investor_name)
    print(f"理念已保存: UUID {idea_uuid}")
    
    # 理念进化
    if score > 0:  # 只进化得分大于0的理念
        new_idea = evolve_idea(current_idea, score, investor_name)
        print(f"进化后理念: {new_idea}")
        
        # 保存新理念到数据库（无评分）
        new_idea_uuid = save_idea_to_db(new_idea, parent_uuid=idea_uuid, investor_name=investor_name)
        print(f"新理念已保存: UUID {new_idea_uuid}")
    else:
        print("理念得分过低，跳过进化")
    
    print("=== 进化周期完成 ===")

# 创建数据库
create_database()

# 运行进化周期
if __name__ == "__main__":
    run_evolution_cycle()
    
    # 关闭数据库连接
    conn.close()