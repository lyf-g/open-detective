import numpy as np
from typing import List, Dict, Any
from datetime import datetime

def add_months(start_date: datetime, months: int) -> datetime:
    new_month = start_date.month - 1 + months
    year = start_date.year + new_month // 12
    month = new_month % 12 + 1
    # Handle day overflow (though we use day=1 for YYYY-MM)
    return start_date.replace(year=year, month=month, day=1)

def forecast_next_months(data: List[Dict[str, Any]], months: int = 3) -> List[Dict[str, Any]]:
    """
    Predicts next 'months' data points using simple linear regression.
    """
    if not data or len(data) < 2:
        return []

    # Filter out entries without 'value' or 'month'
    valid_data = [d for d in data if 'value' in d and 'month' in d]
    if len(valid_data) < 2: return []

    # Sort by month
    sorted_data = sorted(valid_data, key=lambda x: x['month'])
    
    values = [float(d['value']) for d in sorted_data]
    x = np.arange(len(values))
    y = np.array(values)
    
    # Linear Regression (y = mx + c)
    A = np.vstack([x, np.ones(len(x))]).T
    m, c = np.linalg.lstsq(A, y, rcond=None)[0]
    
    # Forecast
    future_points = []
    last_date_str = sorted_data[-1]['month']
    try:
        # Assuming YYYY-MM
        if len(last_date_str) == 7:
            last_date = datetime.strptime(last_date_str, "%Y-%m")
        else:
            return [] # Unknown format
    except:
        return []

    for i in range(1, months + 1):
        next_x = len(values) - 1 + i
        next_val = m * next_x + c
        next_date = add_months(last_date, i)
        future_points.append({
            "repo_name": sorted_data[0].get('repo_name', 'Forecast'),
            "metric_type": sorted_data[0].get('metric_type', 'unknown'),
            "month": next_date.strftime("%Y-%m"),
            "value": max(0, float(next_val)),
            "is_forecast": True
        })
        
    return future_points

def detect_anomalies(data: List[Dict[str, Any]], threshold: float = 2.0) -> List[Dict[str, Any]]:
    """
    Detects anomalies in time-series data using Z-score.
    """
    if not data or len(data) < 3:
        return []

    valid_data = [d for d in data if 'value' in d]
    if len(valid_data) < 3: return []
    
    try:
        values = [float(d['value']) for d in valid_data]
    except ValueError:
        return [] # Cannot parse values

    mean = np.mean(values)
    std = np.std(values)

    anomalies = []
    if std == 0: return []

    for d in valid_data:
        try:
            val = float(d['value'])
            z_score = (val - mean) / std
            if abs(z_score) > threshold:
                anomalies.append({
                    **d,
                    "z_score": float(z_score),
                    "mean": float(mean),
                    "std_dev": float(std),
                    "is_anomaly": True
                })
        except:
            continue
            
    return anomalies
