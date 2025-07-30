import pandas as pd
import numpy as np
import openai
import time


def clean_financial_data(df, current_col, prior_col):
    """Cleans and prepares the financial DataFrame for analysis."""
    df[current_col] = pd.to_numeric(df[current_col].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')
    df[prior_col] = pd.to_numeric(df[prior_col].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')
    df.dropna(subset=[current_col, prior_col], how='all', inplace=True)
    df.fillna(0, inplace=True)
    df = df[~((df[current_col] == 0) & (df[prior_col] == 0))]
    return df


def get_account_category(account_name):
    """Categorizes account name to determine variance favorability."""
    account_lower = str(account_name).lower()
    if any(keyword in account_lower for keyword in ['revenue', 'sales', 'income', 'gain']):
        return 'revenue'
    elif any(keyword in account_lower for keyword in ['cogs', 'cost', 'expense', 'loss', 'spending']):
        return 'expense'
    else:
        return 'other'


def calculate_variances(df):
    """Calculates dollar, percent, and favorable/unfavorable variances."""
    df['Dollar Variance'] = df['Current Period'] - df['Prior Period']
    df['Percent Variance'] = np.where(df['Prior Period'] != 0, (df['Dollar Variance'] / df['Prior Period']) * 100,
                                      np.inf)

    def get_variance_type(row):
        category = get_account_category(row['Account Name'])
        dollar_variance = row['Dollar Variance']
        if category == 'revenue':
            if dollar_variance > 0: return 'Favorable'
            if dollar_variance < 0: return 'Unfavorable'
        elif category == 'expense':
            if dollar_variance < 0: return 'Favorable'
            if dollar_variance > 0: return 'Unfavorable'
        return 'Neutral'

    df['Variance Type'] = df.apply(get_variance_type, axis=1)
    return df


def flag_material_variances(df, dollar_threshold, percent_threshold):
    """Flags variances that meet the materiality criteria."""
    df['Is Material'] = (
                                (abs(df['Dollar Variance']) >= dollar_threshold) & (df['Variance Type'] != 'Neutral')
                        ) | (
                                (abs(df['Percent Variance']) >= percent_threshold) & (df['Variance Type'] != 'Neutral')
                        )
    return df[df['Is Material']].copy()


def generate_ai_explanation(api_key, account_name, current_amount, prior_amount, dollar_change, percent_change,
                            variance_type):
    """Generates a concise financial explanation for a variance using GPT-4."""
    openai.api_key = api_key
    direction_text = f"a {variance_type.lower()} variance" if variance_type != 'Neutral' else "a change"

    category = get_account_category(account_name)
    category_hints = {
        'revenue': 'Focus on drivers like sales volume, pricing changes, new customer acquisition, or market expansion.',
        'expense': 'Focus on drivers like increased operational activity, supplier cost changes, new hires, or strategic investments.'
    }
    hint = category_hints.get(category, 'Consider general business operations and strategic decisions.')

    prompt = (
        f"You are a senior financial analyst providing a concise, audit-ready explanation for a P&L variance.\n\n"
        f"Account: {account_name}\n"
        f"Analysis: This account shows {direction_text}.\n"
        f"- Current Period: ${current_amount:,.2f}\n"
        f"- Prior Period: ${prior_amount:,.2f}\n"
        f"- Dollar Change: ${dollar_change:,.2f}\n"
        f"- Percent Change: {percent_change:,.1f}%\n\n"
        f"Task: Write a professional, one-sentence explanation for the cause of this variance.\n"
        f"- Be specific and use business-oriented language.\n"
        f"- {hint}\n\n"
        f'Example: "Revenue increased by $150,000 (14.3%) primarily due to a successful new marketing campaign that drove a 20% increase in customer acquisition."\n\n'
        f"Explanation:"
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100, temperature=0.4, n=1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error for account '{account_name}': {e}")
        return f"Error: Could not generate explanation. {e}"


def process_data_and_generate_explanations(df, current_col, prior_col, dollar_thresh, percent_thresh, api_key):
    """Full pipeline: clean, analyze, flag, and generate AI explanations."""
    # Step 1: Clean and Prepare
    df_renamed = df[[current_col, prior_col, 'Account']].rename(columns={
        current_col: 'Current Period',
        prior_col: 'Prior Period',
        'Account': 'Account Name'
    })
    cleaned_df = clean_financial_data(df_renamed, 'Current Period', 'Prior Period')

    # Step 2: Calculate and Flag
    variance_df = calculate_variances(cleaned_df)
    material_df = flag_material_variances(variance_df, dollar_thresh, percent_thresh)

    if material_df.empty:
        return material_df

    # Step 3: Generate Explanations
    explanations = []
    for index, row in material_df.iterrows():
        explanation = generate_ai_explanation(
            api_key, row['Account Name'], row['Current Period'], row['Prior Period'],
            row['Dollar Variance'], row['Percent Variance'], row['Variance Type']
        )
        explanations.append(explanation)
        time.sleep(1)

    material_df['Explanation'] = explanations
    return material_df