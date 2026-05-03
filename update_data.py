#!/usr/bin/env python3
"""
投資計劃數據更新腳本
用於獲取ETF實時價格並更新數據
"""

import json
import urllib.request
import ssl
import os
from datetime import datetime

# 禁用SSL驗證（用於Yahoo Finance）
ssl._create_default_https_context = ssl._create_unverified_context

# 投資計劃配置
CONFIG = {
    "start_date": "2025-05-04",
    "monthly_investment": 1960,
    "target_amount": 350000,
    "contribution_years": 5,
    "expected_return": 0.15,
    "etfs": [
        {"symbol": "QQQ", "name": "納斯達克100 ETF", "allocation": 0.35, "monthly": 686},
        {"symbol": "SMH", "name": "半導體 ETF", "allocation": 0.35, "monthly": 686},
        {"symbol": "VGT", "name": "科技行業 ETF", "allocation": 0.30, "monthly": 588}
    ]
}

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
                print(f"Error fetching {symbol}: {data['chart']['error']}")
                return None
            
            result = data['chart']['result'][0]
            meta = result['meta']
            timestamps = result['timestamp']
            prices = result['indicators']['quote'][0]
            
            # 獲取最新數據
            latest_idx = -1
            for i in range(len(prices['close']) - 1, -1, -1):
                if prices['close'][i] is not None:
                    latest_idx = i
                    break
            
            if latest_idx == -1:
                return None
            
            # 計算YTD回報
            first_price = None
            for price in prices['close']:
                if price is not None:
                    first_price = price
                    break
            
            current_price = prices['close'][latest_idx]
            ytd_return = ((current_price - first_price) / first_price * 100) if first_price else 0
            
            return {
                'symbol': symbol,
                'price': current_price,
                'ytd_return': ytd_return,
                'timestamp': timestamps[latest_idx],
                'currency': meta.get('currency', 'USD')
            }
            
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def calculate_portfolio_value():
    """計算投資組合當前價值"""
    start_date = datetime.strptime(CONFIG['start_date'], '%Y-%m-%d')
    today = datetime.now()
    months_elapsed = max(0, 
        (today.year - start_date.year) * 12 + 
        (today.month - start_date.month)
    )
    
    total_invested = min(months_elapsed, CONFIG['contribution_years'] * 12) * CONFIG['monthly_investment']
    
    # 簡化計算預期資產值
    current_value = 0
    for i in range(min(months_elapsed, CONFIG['contribution_years'] * 12)):
        months_remaining = months_elapsed - i
        current_value += CONFIG['monthly_investment'] * ((1 + CONFIG['expected_return'] / 12) ** months_remaining)
    
    if months_elapsed > CONFIG['contribution_years'] * 12:
        growth_months = months_elapsed - CONFIG['contribution_years'] * 12
        current_value = current_value * ((1 + CONFIG['expected_return']) ** (growth_months / 12))
    
    return {
        'months_elapsed': months_elapsed,
        'total_invested': round(total_invested, 2),
        'current_value': round(current_value, 2),
        'total_return': round(current_value - total_invested, 2),
        'return_rate': round((current_value - total_invested) / total_invested * 100, 2) if total_invested > 0 else 0
    }

def check_rebalance_needed(etf_data):
    """檢查是否需要再平衡"""
    alerts = []
    
    # 這裡可以添加實際的偏差檢查邏輯
    # 目前只檢查下次再平衡時間
    
    today = datetime.now()
    current_month = today.month
    current_date = today.day
    
    # 再平衡月份：5月和11月
    rebalance_months = [5, 11]
    
    for month in rebalance_months:
        if month == current_month and current_date <= 4:
            days_until = 4 - current_date
            if days_until >= 0:
                alerts.append({
                    'type': 'rebalance',
                    'message': f'再平衡檢視日：{month}月4日（還有{days_until}天）',
                    'severity': 'warning'
                })
    
    return alerts

def update_data():
    """更新所有數據"""
    print("=" * 60)
    print("投資計劃數據更新")
    print("=" * 60)
    
    # 獲取ETF數據
    etf_data = []
    for etf in CONFIG['etfs']:
        print(f"\n獲取 {etf['symbol']} 數據...")
        data = fetch_yahoo_finance(etf['symbol'])
        if data:
            etf_data.append({
                **etf,
                'current_price': data['price'],
                'ytd_return': data['ytd_return'],
                'last_updated': datetime.now().isoformat()
            })
            print(f"  價格: ${data['price']:.2f}")
            print(f"  YTD: {data['ytd_return']:+.2f}%")
        else:
            print(f"  無法獲取數據")
    
    # 計算投資組合價值
    portfolio = calculate_portfolio_value()
    
    # 檢查再平衡
    alerts = check_rebalance_needed(etf_data)
    
    # 保存數據
    data = {
        'last_updated': datetime.now().isoformat(),
        'config': CONFIG,
        'portfolio': portfolio,
        'etfs': etf_data,
        'alerts': alerts
    }
    
    # 確保數據目錄存在
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 保存到JSON文件
    with open(os.path.join(data_dir, 'portfolio.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("更新完成")
    print("=" * 60)
    print(f"\n投資組合概覽:")
    print(f"  累計投入: ${portfolio['total_invested']:,.2f}")
    print(f"  當前價值: ${portfolio['current_value']:,.2f}")
    print(f"  累計回報: ${portfolio['total_return']:,.2f}")
    print(f"  回報率: {portfolio['return_rate']:+.2f}%")
    print(f"\n目標進度: {portfolio['current_value'] / CONFIG['target_amount'] * 100:.1f}%")
    
    if alerts:
        print(f"\n提醒:")
        for alert in alerts:
            print(f"  ⚠️ {alert['message']}")
    
    print(f"\n數據已保存至: data/portfolio.json")

if __name__ == '__main__':
    update_data()
