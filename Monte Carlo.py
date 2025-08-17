# Monte Carlo.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from backtesting import Backtest

# --- 核心步驟：從您的策略檔案中導入函式和策略類別 ---
from TQQQ_Stra_SeptSell_StopLoss_WeeklyBuy_Simple import TQQQStra, prepare_data

# ==============================================================================
# == 步驟 1: 準備數據並運行一次回測以獲取交易記錄 ==
# ==============================================================================

# 使用導入的函式來準備數據，確保與策略檔的數據完全一致
data_daily = prepare_data(start_date="2000-02-12", end_date="2025-07-30")

if data_daily is not None:
    # 運行一次回測
    print("\n--- [Monte Carlo] Running initial backtest to gather trades... ---")
    bt = Backtest(data_daily, TQQQStra, cash=10000000, commission=0.0002, exclusive_orders=True)
    stats = bt.run()

    # 從回測結果中提取所有交易的回報率
    trade_returns = stats['_trades']['ReturnPct']

    # 檢查並打印原始回測結果
    print("\n--- [Monte Carlo] Initial backtest complete ---")
    print(f"Total trades generated: {len(trade_returns)}")
    if not trade_returns.empty:
        print(f"Average return per trade: {trade_returns.mean():.4%}")
    print("\nOriginal Backtest Stats:")
    print(stats)
    # bt.plot() # 如果需要，可以取消註解來顯示原始回測圖

    # ==============================================================================
    # == 步驟 2: 執行蒙地卡羅模擬 ==
    # ==============================================================================

    def run_monte_carlo_simulation(trade_returns, num_simulations=10000, initial_capital=10000000):
        """
        對策略的交易回報進行蒙地卡羅模擬。
    
        :param trade_returns: 包含每次交易回報率的 Pandas Series。
        :param num_simulations: 模擬的總次數。
        :param initial_capital: 初始資金。
        :return: 包含每次模擬統計結果的 DataFrame，以及包含所有權益曲線的 DataFrame。
        """
        # 防禦性程式設計：確保有交易數據可以模擬
        if trade_returns.empty or len(trade_returns) < 1:
            print("\n沒有足夠的交易來進行蒙地卡羅模擬。")
            return None, None
    
        # 獲取原始交易的總次數
        num_trades = len(trade_returns)
        # 用於存儲每次模擬的最終統計結果
        simulation_results = []
        print(f"\n--- [Monte Carlo] Starting {num_simulations} simulations... ---")
    
        # 【性能優化】: 初始化一個空的 Python 列表來存儲所有的權益曲線 Series。
        # 這遠比在迴圈中反覆向 DataFrame 添加欄位要快得多。
        equity_curves_list = []
    
        for i in range(num_simulations):
            # 核心步驟：從已有的交易回報中，隨機有放回地抽樣，生成一組新的交易序列
            simulated_returns = np.random.choice(trade_returns, size=num_trades, replace=True)
            
            # 根據新的回報序列，計算權益曲線。(1 + 回報率) 的累乘即為淨值變化
            equity_curve = initial_capital * (1 + pd.Series(simulated_returns)).cumprod()
    
            # 【性能優化】: 將本次生成的權益曲線 (一個 Pandas Series) 添加到列表中
            equity_curves_list.append(equity_curve.reset_index(drop=True))
    
            # --- 記錄本次模擬的關鍵統計指標 ---
            # 獲取最終權益，如果曲線為空則返回初始資金
            final_equity = equity_curve.iloc[-1] if not equity_curve.empty else initial_capital
            # 計算歷史最高點
            peak = equity_curve.cummax()
            # 計算回撤百分比
            drawdown = (equity_curve - peak) / peak
            # 找到最大回撤
            max_drawdown = drawdown.min() if not drawdown.empty else 0
            
            simulation_results.append({
                'Final Equity': final_equity,
                'Max Drawdown': max_drawdown,
                'Return [%]': (final_equity / initial_capital - 1) * 100
            })
    
        print("--- [Monte Carlo] Simulation finished! Consolidating results... ---")
    
        # 【性能優化】: 在所有模擬結束後，使用 pd.concat 一次性將列表中的所有 Series 合併成一個 DataFrame。
        # axis=1 表示將每個 Series 作為一個新的欄位進行合併，這是最高效的方法。
        all_equity_curves = pd.concat(equity_curves_list, axis=1)
        # 為合併後的 DataFrame 賦予易於識別的欄位名
        all_equity_curves.columns = [f'Sim_{i}' for i in range(num_simulations)]
    
        # 返回統計結果和所有權益曲線
        return pd.DataFrame(simulation_results), all_equity_curves
    
    def analyze_and_plot_mc_results(mc_results, mc_curves, initial_capital=10000000):
        """
        分析並可視化蒙地卡羅模擬的結果。
        """
        if mc_results is None: return
        
        # 【統計優化】: 同時計算平均值和中位數。中位數更能抵抗極端值的影響，代表典型的結果。
        mean_final_equity = mc_results['Final Equity'].mean()
        median_final_equity = mc_results['Final Equity'].median()
        
        print("\n--- [Monte Carlo] Simulation Analysis ---")
        # 打印描述性統計，如均值、標準差、分位數等
        print(mc_results.describe().round(2))
        
        # 計算 5% 和 95% 分位數，用於評估風險和潛力
        p5 = mc_results['Final Equity'].quantile(0.05)
        p95 = mc_results['Final Equity'].quantile(0.95)
        
        print(f"\nMean Final Equity:   ${mean_final_equity:,.2f} (可能被極端值扭曲)")
        print(f"Median Final Equity: ${median_final_equity:,.2f} (更能代表典型結果)")
        print(f"\n5% Worst-Case Final Equity (VaR): ${p5:,.2f}")
        print(f"5% Best-Case Final Equity:      ${p95:,.2f}")
        
        # 計算最終權益低於初始資金的模擬比例，即虧損機率
        loss_probability = (mc_results['Final Equity'] < initial_capital).mean() * 100
        print(f"Probability of Loss: {loss_probability:.2f}%")
        
        # --- 可視化 ---
        plt.style.use('seaborn-v0_8-whitegrid')
        # 創建一個包含兩個子圖的畫布
        fig, axes = plt.subplots(2, 1, figsize=(14, 12), constrained_layout=True)
        fig.suptitle(f'{len(mc_results)} Monte Carlo Simulations Analysis', fontsize=16)
    
        # --- 子圖 1: 權益曲線 "義大利麵圖" (Spaghetti Plot) ---
        # 【可視化優化】: 使用對數 Y 軸 (log scale) 來更好地展示百分比變化
        mc_curves.plot(ax=axes[0], legend=False, color='gray', alpha=0.1)
        # 繪製平均路徑和初始資金線
        mean_line, = axes[0].plot(mc_curves.mean(axis=1), color='red', linewidth=2, label='Average Path')
        initial_line = axes[0].axhline(initial_capital, color='black', linestyle='--', label='Initial Capital')
        axes[0].set_yscale('log')  # <--- 核心修改：啟用對數座標
        axes[0].set_title('Equity Curves (Log Scale)')
        axes[0].set_ylabel('Portfolio Equity ($) - Log Scale')
        axes[0].legend(handles=[mean_line, initial_line]) # 整理圖例
        
        # --- 子圖 2: 最終權益分佈直方圖 ---
        # 【可視化優化】: 繪製對數化後的最終權益，以更好地觀察分佈形態
        # 為了避免 log(0) 或 log(負數) 的數學錯誤，我們只處理大於零的結果
        positive_equity = mc_results[mc_results['Final Equity'] > 0]['Final Equity']
        log_equity = np.log10(positive_equity)
        
        log_equity.hist(bins=100, ax=axes[1], alpha=0.7)
        # 在直方圖上標記出關鍵的統計位置（同樣進行對數轉換）
        axes[1].axvline(np.log10(initial_capital), color='black', linestyle='--', label='Initial Capital')
        axes[1].axvline(np.log10(mean_final_equity), color='red', linestyle='-', label='Mean Final Equity')
        axes[1].axvline(np.log10(median_final_equity), color='purple', linestyle='-', label='Median Final Equity')
        axes[1].axvline(np.log10(p5), color='orange', linestyle=':', label='5% Quantile (VaR)')
        axes[1].set_title('Distribution of Log10(Final Equity)')
        axes[1].set_xlabel('Final Equity (Log10 Scale)')
        axes[1].set_ylabel('Frequency')
        axes[1].legend()
        
        plt.show()

    # 運行模擬並分析
    mc_results, mc_curves = run_monte_carlo_simulation(trade_returns)
    analyze_and_plot_mc_results(mc_results, mc_curves)

else:
    print("--- [Monte Carlo] Data preparation failed. Halting execution. ---")