#!/usr/bin/env python3
"""
投資計劃數據更新腳本
支持ETF和基金交易記錄管理
"""

import json
import urllib.request
import ssl
import os
import sys
from datetime import datetime
from pathlib import Path

# 禁用SSL驗證
ssl._create_default_https_context = ssl._create_unverified_context

# 匯率設定
USD_TO_HKD = 7.8

def get_data_file():
    """獲取數據文件路徑"""
    return Path(__file__).parent / 'data' / 'portfolio.json'

def load_data():
    """加載投資組合數據"""
    data_file = get_data_file()
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    """保存投資組合數據"""
    data_file = get_data_file()
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_etf_transaction(date, etf_symbol, shares, price, amount, currency='USD'):
    """添加ETF交易記錄"""
    data = load_data()
    
    # 找到ETF組合
    etf_portfolio = None
    for p in data['portfolios']:
        if p['id'] == 'etfs':
            etf_portfolio = p
            break
    
    if not etf_portfolio:
        print("❌ 找不到ETF組合")
        return
    
    transaction = {
        'date': date,
        'etf_symbol': etf_symbol,
        'shares': float(shares),
        'price_per_share': float(price),
        'amount': float(amount),
        'currency': currency,
        'type': 'buy',
        'created_at': datetime.now().isoformat()
    }
    
    etf_portfolio['transactions'].append(transaction)
    save_data(data)
    
    print(f"✅ 已添加ETF交易：")
    print(f"   日期：{date}")
    print(f"   ETF：{etf_symbol}")
    print(f"   股數：{shares}")
    print(f"   價格：${price}")
    print(f"   金額：${amount} {currency}")

def add_fund_transaction(date, fund_symbol, units, nav, amount, currency='HKD'):
    """添加基金交易記錄"""
    data = load_data()
    
    # 找到基金組合
    fund_portfolio = None
    for p in data['portfolios']:
        if p['id'] == 'funds':
            fund_portfolio = p
            break
    
    if not fund_portfolio:
        print("❌ 找不到基金組合")
        return
    
    transaction = {
        'date': date,
        'fund_symbol': fund_symbol,
        'units': float(units),
        'nav': float(nav),
        'amount': float(amount),
        'currency': currency,
        'type': 'buy',
        'created_at': datetime.now().isoformat()
    }
    
    fund_portfolio['transactions'].append(transaction)
    
    # 更新基金當前價值
    for inv in fund_portfolio['investments']:
        if inv['symbol'] == fund_symbol:
            inv['current_value'] = (inv.get('current_value', 0) or 0) + float(amount)
            if currency == 'USD':
                inv['current_value_hkd'] = inv['current_value'] * USD_TO_HKD
            else:
                inv['current_value_hkd'] = inv['current_value']
            break
    
    # 重新計算總值
    calculate_fund_summary(fund_portfolio)
    
    save_data(data)
    
    print(f"✅ 已添加基金交易：")
    print(f"   日期：{date}")
    print(f"   基金：{fund_symbol}")
    print(f"   單位：{units}")
    print(f"   NAV：${nav}")
    print(f"   金額：${amount} {currency}")

def calculate_fund_summary(fund_portfolio):
    """計算基金組合摘要"""
    total_value_hkd = 0
    
    for inv in fund_portfolio['investments']:
        if inv['currency'] == 'USD':
            total_value_hkd += (inv.get('current_value', 0) or 0) * USD_TO_HKD
        else:
            total_value_hkd += (inv.get('current_value', 0) or 0)
    
    fund_portfolio['summary'] = {
        'total_current_value_hkd': round(total_value_hkd, 2),
        'total_invested_hkd': 0,
        'total_return_hkd': 0,
        'return_rate': 0,
        'progress_percent': round((total_value_hkd / fund_portfolio['target_amount']) * 100, 2)
    }

def update_fund_value(fund_symbol, new_value, currency='HKD'):
    """更新基金當前價值"""
    data = load_data()
    
    fund_portfolio = None
    for p in data['portfolios']:
        if p['id'] == 'funds':
            fund_portfolio = p
            break
    
    if not fund_portfolio:
        print("❌ 找不到基金組合")
        return
    
    for inv in fund_portfolio['investments']:
        if inv['symbol'] == fund_symbol:
            inv['current_value'] = float(new_value)
            if currency == 'USD':
                inv['current_value_hkd'] = float(new_value) * USD_TO_HKD
            else:
                inv['current_value_hkd'] = float(new_value)
            print(f"✅ 已更新 {fund_symbol} 價值為 ${new_value} {currency}")
            break
    
    calculate_fund_summary(fund_portfolio)
    save_data(data)

def show_summary():
    """顯示投資組合摘要"""
    data = load_data()
    
    print("\n" + "=" * 60)
    print("📊 投資組合摘要")
    print("=" * 60)
    
    for portfolio in data['portfolios']:
        print(f"\n【{portfolio['name']}】")
        print(f"  類型：{portfolio['type']}")
        print(f"  每月投入：${portfolio['monthly_investment']:,} {portfolio.get('currency', 'USD')}")
        print(f"  目標金額：${portfolio['target_amount']:,}")
        print(f"  投資年期：{portfolio['contribution_years']}年")
        
        if portfolio['id'] == 'funds' and 'summary' in portfolio:
            summary = portfolio['summary']
            print(f"  當前總值：HKD ${summary['total_current_value_hkd']:,.2f}")
            print(f"  目標進度：{summary['progress_percent']:.1f}%")
        
        print(f"  投資數量：{len(portfolio['investments'])}")
        print(f"  交易記錄：{len(portfolio.get('transactions', []))} 筆")
    
    print("\n" + "=" * 60)

def show_fund_details():
    """顯示基金詳情"""
    data = load_data()
    
    fund_portfolio = None
    for p in data['portfolios']:
        if p['id'] == 'funds':
            fund_portfolio = p
            break
    
    if not fund_portfolio:
        print("❌ 找不到基金組合")
        return
    
    print("\n" + "=" * 60)
    print("💼 基金持倉詳情")
    print("=" * 60)
    
    total_hkd = 0
    
    for i, inv in enumerate(fund_portfolio['investments'], 1):
        value_hkd = (inv.get('current_value', 0) or 0) * USD_TO_HKD if inv['currency'] == 'USD' else (inv.get('current_value', 0) or 0)
        total_hkd += value_hkd
        
        print(f"\n{i}. {inv['name']}")
        print(f"   代碼：{inv['symbol']}")
        print(f"   每月投入：{inv['currency']} ${inv['monthly']:,}")
        print(f"   配置比例：{inv['allocation']*100:.2f}%")
        print(f"   當前價值：{inv['currency']} ${inv.get('current_value', 0):,.2f}")
        print(f"   等值港幣：HKD ${value_hkd:,.2f}")
    
    print(f"\n{'=' * 60}")
    print(f"總值（港幣）：HKD ${total_hkd:,.2f}")
    print(f"目標進度：{(total_hkd / fund_portfolio['target_amount'])*100:.1f}%")
    print("=" * 60)

def main():
    """主函數"""
    if len(sys.argv) < 2:
        print("用法：")
        print("  python update_data.py summary              # 顯示摘要")
        print("  python update_data.py fund-details         # 顯示基金詳情")
        print("  python update_data.py add-etf 日期 ETF 股數 價格 金額 [貨幣]")
        print("  python update_data.py add-fund 日期 基金 單位 NAV 金額 [貨幣]")
        print("  python update_data.py update-fund 基金 新價值 [貨幣]")
        print("\n示例：")
        print("  python update_data.py add-etf 2025-05-04 QQQ 1.02 672.55 686.00 USD")
        print("  python update_data.py add-fund 2025-05-04 富蘭克林科技 28.5 105.26 3000 HKD")
        print("  python update_data.py update-fund 富蘭克林科技 65000 HKD")
        return
    
    command = sys.argv[1]
    
    if command == 'summary':
        show_summary()
    elif command == 'fund-details':
        show_fund_details()
    elif command == 'add-etf' and len(sys.argv) >= 7:
        currency = sys.argv[8] if len(sys.argv) > 8 else 'USD'
        add_etf_transaction(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], currency)
    elif command == 'add-fund' and len(sys.argv) >= 7:
        currency = sys.argv[8] if len(sys.argv) > 8 else 'HKD'
        add_fund_transaction(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], currency)
    elif command == 'update-fund' and len(sys.argv) >= 4:
        currency = sys.argv[5] if len(sys.argv) > 5 else 'HKD'
        update_fund_value(sys.argv[2], sys.argv[3], currency)
    else:
        print("❌ 未知命令或參數不足")
        print("請使用：python update_data.py 查看用法")

if __name__ == '__main__':
    main()
