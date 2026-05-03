#!/usr/bin/env python3
"""
投資計劃數據更新腳本
用於獲取ETF市場報價（不計算回報，只獲取價格）
"""

import json
import urllib.request
import ssl
import os
from datetime import datetime

# 禁用SSL驗證
ssl._create_default_https_context = ssl._create_unverified_context

def fetch_yahoo_finance(symbol):
    """從Yahoo Finance獲取股票數據"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1y"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if data['chart']['error']:
                return None
            
            result = data['chart']['result'][0]
            meta = result['meta']
            timestamps = result['timestamp']
            prices = result['indicators']['quote'][0]
            
            # 獲取最新價格
            latest_idx = -1
            for i in range(len(prices['close']) - 1, -1, -1):
                if prices['close'][i] is not None:
                    latest_idx = i
                    break
            
            if latest_idx == -1:
                return None
            
            current_price = prices['close'][latest_idx]
            
            # 計算YTD回報
            valid_prices = [p for p in prices['close'] if p is not None]
            first_price = valid_prices[0] if valid_prices else current_price
            ytd_return = ((current_price - first_price) / first_price * 100) if first_price else 0
            
            # 計算52周高低
            week_52_high = max(valid_prices) if valid_prices else current_price
            week_52_low = min(valid_prices) if valid_prices else current_price
            
            return {
                'price': round(current_price, 2),
                'ytd_return': round(ytd_return, 2),
                'week_52_high': round(week_52_high, 2),
                'week_52_low': round(week_52_low, 2),
                'last_updated': datetime.now().isoformat()
            }
            
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def load_portfolio_data():
    """加載投資組合數據"""
    data_file = os.path.join(os.path.dirname(__file__), 'data', 'portfolio.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_portfolio_data(data):
    """保存投資組合數據"""
    data_file = os.path.join(os.path.dirname(__file__), 'data', 'portfolio.json')
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_market_data():
    """更新市場報價數據"""
    print("=" * 60)
    print("獲取ETF市場報價")
    print("=" * 60)
    
    data = load_portfolio_data()
    
    # 更新市場數據
    market_data = {
        'last_updated': datetime.now().isoformat(),
        'prices': {}
    }
    
    for etf in data['etfs']:
        symbol = etf['symbol']
        print(f"\\n獲取 {symbol} 報價...")
        
        price_data = fetch_yahoo_finance(symbol)
        if price_data:
            market_data['prices'][symbol] = price_data
            print(f"  價格: ${price_data['price']:.2f}")
            print(f"  YTD: {price_data['ytd_return']:+.2f}%")
            print(f"  52周: ${price_data['week_52_low']:.2f} - ${price_data['week_52_high']:.2f}")
        else:
            print(f"  無法獲取數據")
    
    data['market_data'] = market_data
    save_portfolio_data(data)
    
    print("\\n" + "=" * 60)
    print("市場報價更新完成")
    print("=" * 60)
    print(f"\\n最後更新: {market_data['last_updated']}")

def add_transaction(date, etf_symbol, shares, price_per_share, amount):
    """添加交易記錄"""
    data = load_portfolio_data()
    
    transaction = {
        'date': date,
        'etf_symbol': etf_symbol,
        'shares': shares,
        'price_per_share': price_per_share,
        'amount': amount,
        'type': 'buy'
    }
    
    data['transactions'].append(transaction)
    save_portfolio_data(data)
    
    print(f"\\n✅ 已添加交易記錄:")
    print(f"   日期: {date}")
    print(f"   ETF: {etf_symbol}")
    print(f"   股數: {shares}")
    print(f"   價格: ${price_per_share:.2f}")
    print(f"   金額: ${amount:.2f}")

def calculate_real_returns():
    """計算真實回報（基於實際買入數據）"""
    data = load_portfolio_data()
    
    print("\\n" + "=" * 60)
    print("投資組合真實回報計算")
    print("=" * 60)
    
    if not data['transactions']:
        print("\\n⚠️ 尚未有交易記錄")
        print("   請先添加首次買入記錄")
        return
    
    # 按ETF分組計算
    etf_summary = {}
    for etf in data['etfs']:
        etf_summary[etf['symbol']] = {
            'name': etf['name'],
            'total_shares': 0,
            'total_cost': 0,
            'transactions': []
        }
    
    for trans in data['transactions']:
        symbol = trans['etf_symbol']
        if symbol in etf_summary:
            etf_summary[symbol]['total_shares'] += trans['shares']
            etf_summary[symbol]['total_cost'] += trans['amount']
            etf_summary[symbol]['transactions'].append(trans)
    
    # 計算每個ETF的回報
    total_cost = 0
    total_value = 0
    
    print("\\n")
    for symbol, summary in etf_summary.items():
        if summary['total_shares'] == 0:
            continue
            
        current_price = data['market_data']['prices'].get(symbol, {}).get('price', 0)
        current_value = summary['total_shares'] * current_price
        cost = summary['total_cost']
        profit = current_value - cost
        return_rate = (profit / cost * 100) if cost > 0 else 0
        
        total_cost += cost
        total_value += current_value
        
        print(f"【{symbol}】{summary['name']}")
        print(f"  持有股數: {summary['total_shares']:.4f}")
        print(f"  總成本: ${cost:,.2f}")
        print(f"  當前價值: ${current_value:,.2f}")
        print(f"  盈虧: ${profit:,.2f} ({return_rate:+.2f}%)")
        print(f"  平均成本: ${cost/summary['total_shares']:.2f}/股")
        print(f"  當前價格: ${current_price:.2f}/股")
        print()
    
    # 總計
    total_profit = total_value - total_cost
    total_return_rate = (total_profit / total_cost * 100) if total_cost > 0 else 0
    
    print("=" * 60)
    print("投資組合總計")
    print("=" * 60)
    print(f"  總成本: ${total_cost:,.2f}")
    print(f"  總價值: ${total_value:,.2f}")
    print(f"  總盈虧: ${total_profit:,.2f} ({total_return_rate:+.2f}%)")
    print(f"  目標進度: {total_value / data['plan']['target_amount'] * 100:.2f}%")
    print("=" * 60)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'add':
        # 添加交易記錄
        # 用法: python update_data.py add 2025-05-04 QQQ 1.02 672.55 686.00
        if len(sys.argv) >= 6:
            date = sys.argv[2]
            etf = sys.argv[3]
            shares = float(sys.argv[4])
            price = float(sys.argv[5])
            amount = float(sys.argv[6])
            add_transaction(date, etf, shares, price, amount)
        else:
            print("用法: python update_data.py add <日期> <ETF> <股數> <價格> <金額>")
            print("示例: python update_data.py add 2025-05-04 QQQ 1.02 672.55 686.00")
    elif len(sys.argv) > 1 and sys.argv[1] == 'returns':
        # 計算真實回報
        update_market_data()
        calculate_real_returns()
    else:
        # 默認：只更新市場報價
        update_market_data()
