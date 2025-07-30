import pandas as pd
import numpy as np
import os

def generate_synthetic_data():
    """Generates a synthetic P&L statement and saves it as a CSV."""
    accounts = [
        "Revenue", "Cost of Goods Sold", "Gross Profit",
        "R&D Expenses", "Sales & Marketing", "General & Admin",
        "Operating Income", "Interest Expense", "Net Income"
    ]

    data = {
        'Account': accounts,
        '2024 Actual': [
            1250000, 470000, 780000, 210000, 195000,
            130000, 245000, 16000, 229000
        ],
        '2023 Actual': [
            1100000, 420000, 680000, 240000, 170000,
            115000, 155000, 14000, 141000
        ]
    }

    df = pd.DataFrame(data)

    # Ensure the 'assets' directory exists
    output_dir = 'assets'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save to CSV
    output_path = os.path.join(output_dir, 'sample_pnl.csv')
    df.to_csv(output_path, index=False)
    print(f"Synthetic data saved to {output_path}")

if __name__ == '__main__':
    generate_synthetic_data()