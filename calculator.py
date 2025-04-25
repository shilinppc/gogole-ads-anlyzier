import pandas as pd
import numpy as np

# Constants for calculation
CPC_RANGES = {
    'ecommerce': {
        'min': 5.0,  # Min CPC in UAH
        'max': 15.0  # Max CPC in UAH
    },
    'services': {
        'min': 8.0,  # Min CPC in UAH
        'max': 20.0  # Max CPC in UAH
    }
}

CTR_RANGES = {
    'ecommerce': {
        'min': 0.02,  # 2%
        'max': 0.04   # 4%
    },
    'services': {
        'min': 0.015, # 1.5%
        'max': 0.035  # 3.5%
    }
}

CONVERSION_RATE_RANGES = {
    'ecommerce': {
        'min': 0.01,  # 1%
        'max': 0.03   # 3%
    },
    'services': {
        'min': 0.03,  # 3%
        'max': 0.07   # 7%
    }
}

AVG_ORDER_VALUE_RANGES = {
    'ecommerce': {
        'min': 800,   # 800 UAH
        'max': 2000   # 2000 UAH
    },
    'services': {
        'min': 1500,  # 1500 UAH
        'max': 5000   # 5000 UAH
    }
}

def calculate_google_ads_metrics(budget, business_type, params=None):
    """
    Calculate Google Ads campaign metrics based on budget and business type
    
    Args:
        budget (float): Budget in UAH
        business_type (str): 'ecommerce' or 'services'
        params (dict): Optional custom parameters
    
    Returns:
        dict: Campaign metrics
    """
    if params is None:
        params = {}
    
    # Default parameters based on business type
    avg_cpc = params.get('avg_cpc', np.mean([CPC_RANGES[business_type]['min'], CPC_RANGES[business_type]['max']]))
    ctr = params.get('ctr', np.mean([CTR_RANGES[business_type]['min'], CTR_RANGES[business_type]['max']]))
    conversion_rate = params.get('conversion_rate', np.mean([CONVERSION_RATE_RANGES[business_type]['min'], CONVERSION_RATE_RANGES[business_type]['max']]))
    avg_order_value = params.get('avg_order_value', np.mean([AVG_ORDER_VALUE_RANGES[business_type]['min'], AVG_ORDER_VALUE_RANGES[business_type]['max']]))
    
    # Calculate basic metrics
    clicks = budget / avg_cpc
    impressions = clicks / ctr if ctr > 0 else 0
    conversions = clicks * conversion_rate
    revenue = conversions * avg_order_value
    
    # ROI and ROAS calculations
    roi = ((revenue - budget) / budget) if budget > 0 else 0
    roas = revenue / budget if budget > 0 else 0
    
    # Cost metrics
    cost_per_conversion = budget / conversions if conversions > 0 else 0
    
    # Projected metrics
    daily_budget = budget / 30  # Assuming monthly budget
    monthly_revenue = revenue
    
    results = {
        'budget': budget,
        'avg_cpc': avg_cpc,
        'clicks': clicks,
        'impressions': impressions,
        'ctr': ctr,
        'conversion_rate': conversion_rate,
        'conversions': conversions,
        'cost_per_conversion': cost_per_conversion,
        'avg_order_value': avg_order_value,
        'revenue': revenue,
        'roi': roi,
        'roas': roas,
        'daily_budget': daily_budget,
        'monthly_revenue': monthly_revenue
    }
    
    return results

def generate_detailed_analysis(budget, business_type, params=None):
    """
    Generate detailed analysis with scenario variations
    
    Args:
        budget (float): Budget in UAH
        business_type (str): 'ecommerce' or 'services'
        params (dict): Optional custom parameters
    
    Returns:
        tuple: (base_case, pessimistic_case, optimistic_case)
    """
    if params is None:
        params = {}
    
    # Base case - using average values
    base_case = calculate_google_ads_metrics(budget, business_type, params)
    
    # Pessimistic case - lower CTR, conversion rate, higher CPC
    pessimistic_params = params.copy()
    pessimistic_params.update({
        'avg_cpc': CPC_RANGES[business_type]['max'] * 1.1,  # 10% higher CPC
        'ctr': CTR_RANGES[business_type]['min'] * 0.9,  # 10% lower CTR
        'conversion_rate': CONVERSION_RATE_RANGES[business_type]['min'] * 0.9,  # 10% lower conversion rate
        'avg_order_value': AVG_ORDER_VALUE_RANGES[business_type]['min'] * 0.9  # 10% lower average order value
    })
    pessimistic_case = calculate_google_ads_metrics(budget, business_type, pessimistic_params)
    
    # Optimistic case - higher CTR, conversion rate, lower CPC
    optimistic_params = params.copy()
    optimistic_params.update({
        'avg_cpc': CPC_RANGES[business_type]['min'] * 0.9,  # 10% lower CPC
        'ctr': CTR_RANGES[business_type]['max'] * 1.1,  # 10% higher CTR
        'conversion_rate': CONVERSION_RATE_RANGES[business_type]['max'] * 1.1,  # 10% higher conversion rate
        'avg_order_value': AVG_ORDER_VALUE_RANGES[business_type]['max'] * 1.1  # 10% higher average order value
    })
    optimistic_case = calculate_google_ads_metrics(budget, business_type, optimistic_params)
    
    return base_case, pessimistic_case, optimistic_case
