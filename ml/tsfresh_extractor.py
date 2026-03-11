"""
Time-Series Feature Extraction using tsfresh

Extracts temporal patterns and statistical features from alert sequences
to improve anomaly detection accuracy.
"""

from tsfresh import extract_features
from tsfresh.utilities.dataframe_functions import impute
from tsfresh.feature_extraction import ComprehensiveFCParameters
import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class TimeSeriesFeatureExtractor:
    """
    Extracts time-series features from security alert sequences.
    
    Features include:
    - Statistical measures (mean, variance, skewness, kurtosis)
    - Temporal patterns (trends, seasonality)
    - Frequency domain features (FFT coefficients)
    - Autocorrelation features
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize feature extractor.
        
        Args:
            window_size: Number of alerts to consider for feature extraction
        """
        self.window_size = window_size
        self.feature_params = ComprehensiveFCParameters()
    
    def prepare_timeseries_data(self, alerts_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare alert data for tsfresh feature extraction.
        
        Args:
            alerts_df: DataFrame with columns [timestamp, attack_type, severity, ...]
        
        Returns:
            DataFrame in tsfresh format with columns [id, time, value]
        """
        # Sort by timestamp
        alerts_df = alerts_df.sort_values('timestamp').copy()
        
        # Create time index (seconds since first alert)
        alerts_df['time'] = (
            pd.to_datetime(alerts_df['timestamp']) - 
            pd.to_datetime(alerts_df['timestamp'].iloc[0])
        ).dt.total_seconds()
        
        # Create entity ID (group by attack_type)
        alerts_df['id'] = alerts_df['attack_type']
        
        # Create multiple value columns for different metrics
        timeseries_data = []
        
        # 1. Alert count over time (binary: 1 for each alert)
        ts_count = alerts_df[['id', 'time']].copy()
        ts_count['value'] = 1
        ts_count['metric'] = 'alert_count'
        timeseries_data.append(ts_count)
        
        # 2. Severity score over time
        severity_map = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        ts_severity = alerts_df[['id', 'time']].copy()
        ts_severity['value'] = alerts_df['severity'].map(severity_map)
        ts_severity['metric'] = 'severity_score'
        timeseries_data.append(ts_severity)
        
        # 3. Port diversity (if available)
        if 'dst_port' in alerts_df.columns:
            ts_port = alerts_df[['id', 'time', 'dst_port']].copy()
            ts_port['value'] = ts_port['dst_port']
            ts_port['metric'] = 'port_diversity'
            ts_port = ts_port.drop('dst_port', axis=1)
            timeseries_data.append(ts_port)
        
        # Combine all metrics
        combined_ts = pd.concat(timeseries_data, ignore_index=True)
        
        return combined_ts
    
    def extract_features(self, alerts_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract time-series features from alerts.
        
        Args:
            alerts_df: DataFrame with alert data
        
        Returns:
            DataFrame with extracted features (one row per attack_type)
        """
        if len(alerts_df) < 10:
            logger.warning("Insufficient data for tsfresh feature extraction (need at least 10 alerts)")
            return pd.DataFrame()
        
        try:
            # Prepare data
            ts_data = self.prepare_timeseries_data(alerts_df)
            
            # Extract features using tsfresh
            logger.info("Extracting time-series features with tsfresh...")
            
            # Use a subset of features for performance
            feature_params = {
                'mean': None,
                'variance': None,
                'skewness': None,
                'kurtosis': None,
                'maximum': None,
                'minimum': None,
                'median': None,
                'standard_deviation': None,
                'sum_values': None,
                'abs_energy': None,
                'mean_abs_change': None,
                'mean_change': None,
                'count_above_mean': None,
                'count_below_mean': None,
                'longest_strike_above_mean': None,
                'longest_strike_below_mean': None,
                'linear_trend': [{'attr': 'slope'}],
                'autocorrelation': [{'lag': 1}, {'lag': 2}],
                'fft_coefficient': [{'coeff': 0}, {'coeff': 1}],
            }
            
            features = extract_features(
                ts_data,
                column_id='id',
                column_sort='time',
                column_value='value',
                default_fc_parameters=feature_params,
                impute_function=impute,
                disable_progressbar=True
            )
            
            logger.info(f"Extracted {len(features.columns)} time-series features")
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            return pd.DataFrame()
    
    def get_temporal_burst_features(self, alerts_df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate temporal burst features manually (faster than tsfresh for simple metrics).
        
        Args:
            alerts_df: DataFrame with alert data
        
        Returns:
            Dictionary of burst-related features
        """
        if len(alerts_df) < 2:
            return {}
        
        # Sort by timestamp
        alerts_df = alerts_df.sort_values('timestamp').copy()
        
        # Calculate inter-arrival times
        alerts_df['timestamp_dt'] = pd.to_datetime(alerts_df['timestamp'])
        inter_arrival = alerts_df['timestamp_dt'].diff().dt.total_seconds()
        
        features = {
            'mean_inter_arrival': inter_arrival.mean(),
            'std_inter_arrival': inter_arrival.std(),
            'min_inter_arrival': inter_arrival.min(),
            'max_inter_arrival': inter_arrival.max(),
            'burst_coefficient': inter_arrival.std() / (inter_arrival.mean() + 1e-6),  # High = bursty
        }
        
        # Calculate alerts per minute
        time_span = (alerts_df['timestamp_dt'].max() - alerts_df['timestamp_dt'].min()).total_seconds() / 60
        if time_span > 0:
            features['alerts_per_minute'] = len(alerts_df) / time_span
        else:
            features['alerts_per_minute'] = len(alerts_df)
        
        # Detect burst windows (1-minute windows with >10 alerts)
        alerts_df['minute'] = alerts_df['timestamp_dt'].dt.floor('1min')
        alerts_per_minute = alerts_df.groupby('minute').size()
        features['max_alerts_per_minute'] = alerts_per_minute.max()
        features['burst_windows'] = (alerts_per_minute > 10).sum()
        
        return features


def add_tsfresh_features_to_alerts(alerts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add tsfresh-extracted features to alert DataFrame.
    
    Args:
        alerts_df: Original alerts DataFrame
    
    Returns:
        Enhanced DataFrame with tsfresh features
    """
    extractor = TimeSeriesFeatureExtractor()
    
    # Extract features per attack type
    features_list = []
    for attack_type in alerts_df['attack_type'].unique():
        attack_alerts = alerts_df[alerts_df['attack_type'] == attack_type]
        
        # Get temporal burst features (fast)
        burst_features = extractor.get_temporal_burst_features(attack_alerts)
        burst_features['attack_type'] = attack_type
        features_list.append(burst_features)
    
    # Create features DataFrame
    features_df = pd.DataFrame(features_list)
    
    # Merge back to original alerts
    enhanced_df = alerts_df.merge(
        features_df,
        on='attack_type',
        how='left'
    )
    
    return enhanced_df
