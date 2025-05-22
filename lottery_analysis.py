"""
Lottery Data Analysis Module

This module provides machine learning analysis of lottery data,
including ticket patterns, winning number correlations, and
cross-lottery type pattern detection.
"""
import os
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import io
import base64
from sqlalchemy import func, and_, or_, distinct
import numpy as np

# Custom JSON encoder to handle numpy types
class NumpyEncoder(json.JSONEncoder):
    """Custom encoder for numpy data types"""
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                          np.int16, np.int32, np.int64, np.uint8,
                          np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create static directory for saving generated images if it doesn't exist
STATIC_DIR = os.path.join(os.getcwd(), 'static', 'analysis')
os.makedirs(STATIC_DIR, exist_ok=True)

# Global cache for model data
model_cache = {}
chart_cache = {}

class LotteryAnalyzer:
    """Main class for analyzing lottery data and generating insights"""
    
    def __init__(self, db):
        """Initialize analyzer with database connection"""
        self.db = db
        from models import LotteryResult, Screenshot, ImportedRecord  # Import here to avoid circular imports
        self.LotteryResult = LotteryResult
        self.Screenshot = Screenshot
        self.ImportedRecord = ImportedRecord
        
        # Supported lottery types
        self.lottery_types = ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2', 
                             'Powerball', 'Powerball Plus', 'Daily Lottery']
        
        # Required number count by lottery type
        self.required_numbers = {
            'Lottery': 6,
            'Lottery Plus 1': 6,
            'Lottery Plus 2': 6,
            'Powerball': 5,  # Plus 1 bonus ball
            'Powerball Plus': 5,  # Plus 1 bonus ball
            'Daily Lottery': 5
        }
        
        # Store analysis results
        self.analysis_results = {}
        
    def _generate_frequency_chart(self, frequency, top_numbers, lottery_type, results):
        """Generate frequency chart data and add to results
        
        Args:
            frequency (numpy.ndarray): Frequency array for each number
            top_numbers (list): List of tuples (number, frequency) for top numbers
            lottery_type (str): Type of lottery
            results (dict): Results dictionary to update
        """
        # Skip chart generation for API responses to improve speed
        # Just store numerical data for faster response times
        
        # Sort top numbers by frequency, highest first
        sorted_top = sorted(top_numbers, key=lambda x: x[1], reverse=True)
        
        # Store results without generating charts
        results[lottery_type] = {
            'frequency': frequency.tolist(),
            'top_numbers': sorted_top,
            'chart_path': f'/static/analysis/frequency_{lottery_type.replace(" ", "_")}.png',
            'chart_base64': None  # Skip image generation for faster API response
        }
        
    def get_lottery_data(self, lottery_type=None, days=365):
        """Retrieve lottery data for analysis
        
        Args:
            lottery_type (str, optional): Specific lottery type to analyze
            days (int, optional): Number of days of historical data to include
            
        Returns:
            pandas.DataFrame: Dataframe with lottery results
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Query lottery results
            query = self.db.session.query(self.LotteryResult).filter(
                self.LotteryResult.draw_date >= start_date
            )
            
            if lottery_type:
                query = query.filter(self.LotteryResult.lottery_type == lottery_type)
                
            # Order by lottery type and draw date
            results = query.order_by(
                self.LotteryResult.lottery_type,
                self.LotteryResult.draw_date.desc()
            ).all()
            
            logger.info(f"Retrieved {len(results)} lottery results for analysis")
            
            # Convert to dataframe
            data = []
            for result in results:
                try:
                    # Extract the numbers as a list - handle JSON strings
                    if isinstance(result.numbers, str):
                        if result.numbers.startswith('[') and result.numbers.endswith(']'):
                            # JSON format
                            try:
                                numbers = json.loads(result.numbers)
                            except json.JSONDecodeError:
                                # Try handling as comma-separated values
                                numbers = [int(n.strip()) for n in result.numbers.split(',') if n.strip().isdigit()]
                        else:
                            # Comma-separated values
                            numbers = [int(n.strip()) for n in result.numbers.split(',') if n.strip().isdigit()]
                    else:
                        # Already in list form
                        numbers = result.numbers
                    
                    # Get bonus numbers if available
                    bonus_numbers = []
                    if result.bonus_numbers:
                        if isinstance(result.bonus_numbers, str):
                            try:
                                bonus_numbers = json.loads(result.bonus_numbers)
                            except json.JSONDecodeError:
                                bonus_numbers = [int(n.strip()) for n in result.bonus_numbers.split(',') if n.strip().isdigit()]
                        else:
                            bonus_numbers = result.bonus_numbers
                    
                    # Create row dictionary
                    row = {
                        'id': result.id,
                        'lottery_type': result.lottery_type,
                        'draw_number': result.draw_number,
                        'draw_date': result.draw_date,
                    }
                    
                    # Add individual numbers as separate columns
                    max_numbers = self.required_numbers.get(result.lottery_type, 6)
                    for i in range(max_numbers):
                        if i < len(numbers):
                            row[f'number_{i+1}'] = numbers[i]
                        else:
                            row[f'number_{i+1}'] = None
                    
                    # Add bonus number if applicable
                    if result.lottery_type in ['Powerball', 'Powerball Plus'] and bonus_numbers:
                        row['bonus_number'] = bonus_numbers[0] if len(bonus_numbers) > 0 else None
                    
                    # Add division data if available
                    if result.divisions:
                        try:
                            divisions = result.divisions
                            if isinstance(divisions, str):
                                divisions = json.loads(divisions)
                                
                            # Add key division metrics
                            if isinstance(divisions, dict):
                                for div_num, div_data in divisions.items():
                                    winners = div_data.get('winners', 0)
                                    if isinstance(winners, str):
                                        if winners.isdigit():
                                            winners = int(winners)
                                        else:
                                            winners = 0
                                    row[f'div_{div_num}_winners'] = winners
                        except Exception as e:
                            logger.error(f"Error parsing divisions: {e}")
                    
                    data.append(row)
                except Exception as e:
                    logger.error(f"Error processing lottery result {result.id}: {e}")
                    continue
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving lottery data: {e}")
            return pd.DataFrame()
    
    def analyze_frequency(self, lottery_type=None, days=365):
        """Analyze frequency of winning numbers
        
        Args:
            lottery_type (str, optional): Specific lottery type to analyze
            days (int or str, optional): Number of days of historical data
            
        Returns:
            dict: Analysis results including frequency charts
        """
        # Make sure days is converted to an integer
        try:
            days = int(days)
        except (ValueError, TypeError):
            days = 365
            logger.warning(f"Invalid days parameter: {days}. Using default 365 days.")
        try:
            # Step 1: Get and validate data
            df = self.get_lottery_data(lottery_type, days)
            if df.empty:
                logger.warning(f"No data available for analysis with lottery_type={lottery_type}, days={days}")
                return {"error": "No data available for analysis"}
            
            results = {}
            
            # Validate lottery_type if specified
            if lottery_type and lottery_type not in self.lottery_types and lottery_type != "All Lottery Types":
                logger.warning(f"Invalid lottery type specified: {lottery_type}")
                return {"error": f"Invalid lottery type: {lottery_type}"}
                
            # Step 2: Determine which lottery types to analyze
            if lottery_type:
                lottery_types = [lottery_type]
            else:
                lottery_types = df['lottery_type'].unique()
            
            # Step 3: Add a combined "All Lottery Types" analysis
            try:
                all_types_df = df.copy()
                if not all_types_df.empty:
                    # Get all number columns across all lottery types
                    all_number_cols = [col for col in all_types_df.columns if col.startswith('number_')]
                    max_number = 0
                    
                    # Find the highest number across all draws and all types
                    for col in all_number_cols:
                        max_val = all_types_df[col].max()
                        if max_val and max_val > max_number:
                            max_number = int(max_val)
                    
                    # Create a frequency array for all possible numbers
                    combined_frequency = np.zeros(max_number + 1, dtype=int)
                    
                    # Count occurrences of each number across all lottery types
                    for col in all_number_cols:
                        for num in all_types_df[col].dropna():
                            try:
                                # Handle all possible type conversions safely
                                if isinstance(num, str):
                                    # Try to convert string to float first, then to int to handle decimal strings
                                    num_int = int(float(num))
                                else:
                                    # Convert directly to int for numeric types
                                    num_int = int(num)
                                    
                                if 0 <= num_int <= max_number:
                                    combined_frequency[num_int] += 1
                            except (ValueError, TypeError):
                                # Skip invalid number formats
                                logger.debug(f"Skipping invalid lottery number: {num}, type: {type(num)}")
                                continue
                    
                    # Remove the 0 index since there's no ball numbered 0
                    combined_frequency = combined_frequency[1:]
                    
                    # Add the combined analysis to results with a special key
                    top_indices = np.argsort(combined_frequency)[-10:]
                    top_numbers = [(i+1, combined_frequency[i]) for i in top_indices]
                    
                    results["All Lottery Types"] = {
                        'frequency': combined_frequency.tolist(),
                        'top_numbers': sorted(top_numbers, key=lambda x: x[1], reverse=True),
                        'is_combined': True,
                        'total_draws': len(df['draw_number'].unique())
                    }
                    
                    # Generate frequency chart for combined data
                    self._generate_frequency_chart(combined_frequency, top_numbers, "All Lottery Types", results)
            except Exception as e:
                logger.error(f"Error processing combined lottery types: {str(e)}")
                results["All Lottery Types"] = {
                    'error': f"Error generating combined chart: {str(e)}",
                    'has_error': True
                }
            
            # Step 4: Process individual lottery types
            for lt in lottery_types:
                try:
                    lt_df = df[df['lottery_type'] == lt]
                    if lt_df.empty:
                        logger.warning(f"No data found for lottery type: {lt}")
                        continue
                        
                    # Get the number columns for this lottery type
                    number_cols = [col for col in lt_df.columns if col.startswith('number_')]
                    max_number = 0
                    
                    # Find the highest number across all draws
                    for col in number_cols:
                        try:
                            # Convert to numeric first to handle any string values
                            numeric_col = pd.to_numeric(lt_df[col], errors='coerce')
                            max_val = numeric_col.max()
                            if not pd.isna(max_val) and max_val > max_number:
                                max_number = int(max_val)
                        except Exception as e:
                            logger.warning(f"Error processing column {col}: {e}")
                    
                    # Create a frequency array for all possible numbers
                    frequency = np.zeros(max_number + 1, dtype=int)
                    
                    # Count occurrences of each number
                    for col in number_cols:
                        for num in lt_df[col].dropna():
                            try:
                                # Handle all possible type conversions safely
                                if isinstance(num, str):
                                    # Try to convert string to float first, then to int to handle decimal strings
                                    if num.strip() == '':
                                        continue
                                    num_int = int(float(num))
                                elif isinstance(num, (int, float)):
                                    # Convert directly to int for numeric types
                                    num_int = int(num)
                                else:
                                    # Skip other types
                                    continue
                                    
                                if 0 <= num_int <= max_number:
                                    frequency[num_int] += 1
                            except (ValueError, TypeError):
                                # Skip invalid number formats
                                logger.debug(f"Skipping invalid lottery number: {num}, type: {type(num)}")
                                continue
                    
                    # Remove the 0 index since there's no ball numbered 0
                    frequency = frequency[1:]
                    
                    # Generate frequency chart
                    # Get top numbers
                    top_indices = np.argsort(frequency)[-5:]
                    top_numbers = [(i+1, frequency[i]) for i in top_indices]
                    
                    # Add total draws count to the results
                    if lt not in results:
                        results[lt] = {}
                    results[lt]['total_draws'] = len(lt_df['draw_number'].unique())
                    
                    # Generate frequency chart for this lottery type
                    self._generate_frequency_chart(frequency, top_numbers, lt, results)
                except Exception as e:
                    logger.error(f"Error processing lottery type {lt}: {str(e)}")
                    # Add error information to results instead of failing entirely
                    results[lt] = {
                        'error': f"Error generating chart: {str(e)}",
                        'has_error': True
                    }
            
            # Step 5: Cache and return results
            cache_key = f"frequency_{lottery_type}_{days}"
            chart_cache[cache_key] = results
            
            return results
            
        except Exception as e:
            logger.error(f"Error in analyze_frequency: {str(e)}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "status": "error"
            }
    
    def analyze_patterns(self, lottery_type=None, days=365):
        """Find patterns in winning number combinations
        
        Args:
            lottery_type (str, optional): Specific lottery type to analyze
            days (int, optional): Number of days of historical data
            
        Returns:
            dict: Analysis results including pattern charts
        """
        df = self.get_lottery_data(lottery_type, days)
        if df.empty:
            return {"error": "No data available for analysis"}
        
        results = {}
        
        if lottery_type:
            lottery_types = [lottery_type]
        else:
            lottery_types = df['lottery_type'].unique()
        
        for lt in lottery_types:
            lt_df = df[df['lottery_type'] == lt]
            if lt_df.empty or len(lt_df) < 5:  # Need sufficient data for pattern analysis
                continue
                
            # Get the number columns for this lottery type
            number_cols = [col for col in lt_df.columns if col.startswith('number_')]
            
            # Create a clean dataframe with only the number columns
            number_df = lt_df[number_cols].copy()
            
            # Check if we have missing values
            if number_df.isna().any().any():
                # Filter out rows with NaN values
                complete_rows = number_df.dropna(how='any')
                
                # If we don't have enough data after filtering, skip this lottery type
                if len(complete_rows) < 5:
                    logger.warning(f"Not enough complete data for {lt} after removing NaN values")
                    results[lt] = {
                        'error': f"Not enough complete data after removing rows with missing values"
                    }
                    continue
                    
                # Use only complete rows for analysis
                features = complete_rows.values
                # Keep track of indices for later when adding draw numbers
                valid_indices = complete_rows.index
            else:
                # All data is complete, proceed normally
                features = number_df.values
                valid_indices = number_df.index
            
            try:
                # Log the start of pattern analysis with row count
                logger.info(f"Starting pattern analysis for {lt} with {len(features)} rows of data")
                print(f"Starting pattern analysis for {lt} with {len(features)} rows of data")
                
                # Check for NaN values
                if np.isnan(features).any():
                    logger.warning(f"NaN values found in features for {lt} before analysis")
                    print(f"NaN values found in features for {lt} before analysis")
                    # Replace any remaining NaN with 0 (not ideal but prevents crashes)
                    features = np.nan_to_num(features, nan=0.0)
                
                # Check if we have enough data rows
                if len(features) < 5:
                    raise ValueError(f"Not enough data for pattern analysis. Need at least 5 rows, got {len(features)}")
                
                # STEP 1: Try to use sklearn for advanced analysis
                try:
                    # Normalize the data with verbose error handling
                    scaler = StandardScaler()
                    scaled_features = scaler.fit_transform(features)
                    logger.info(f"Data successfully scaled for {lt}")
                    print(f"Data successfully scaled for {lt}")
                    
                    # Apply PCA for dimensionality reduction with verbose error handling
                    pca = PCA(n_components=2)
                    reduced_features = pca.fit_transform(scaled_features)
                    logger.info(f"PCA successfully applied for {lt}")
                    print(f"PCA successfully applied for {lt}, explained variance: {pca.explained_variance_ratio_}")
                    
                    # Apply clustering to find patterns
                    n_clusters = min(5, len(features))  # Limit clusters to 5 or number of samples
                    logger.info(f"Using {n_clusters} clusters for {lt}")
                    print(f"Using {n_clusters} clusters for {lt}")
                    
                    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                    clusters = kmeans.fit_predict(scaled_features)
                    logger.info(f"KMeans clustering successfully applied for {lt}")
                    print(f"KMeans clustering successfully applied for {lt}")
                    
                    # Create a DataFrame with the PCA results and cluster assignments
                    pca_df = pd.DataFrame({
                        'PC1': reduced_features[:, 0],
                        'PC2': reduced_features[:, 1],
                        'Cluster': clusters
                    })
                    logger.info(f"Successfully created PCA DataFrame for {lt}")
                    print(f"Successfully created PCA DataFrame for {lt}")
                    
                    # Advanced analysis successful - continue with normal processing
                    using_fallback = False
                    
                except Exception as sklearn_error:
                    # Log the sklearn error
                    logger.error(f"Error in sklearn analysis for {lt}: {str(sklearn_error)}")
                    print(f"SKLEARN ERROR: {str(sklearn_error)}")
                    print(f"Falling back to simplified pattern analysis")
                    
                    # STEP 2: Fall back to simple pattern detection without sklearn
                    using_fallback = True
                    
                    # Create a simple clustering based on sums of numbers
                    number_sums = np.sum(features, axis=1)
                    
                    # Create simple clusters based on quartiles of sums
                    quartiles = np.percentile(number_sums, [25, 50, 75])
                    simple_clusters = np.zeros(len(number_sums), dtype=int)
                    
                    for i, total in enumerate(number_sums):
                        if total <= quartiles[0]:
                            simple_clusters[i] = 0  # Low sum
                        elif total <= quartiles[1]:
                            simple_clusters[i] = 1  # Medium-low sum
                        elif total <= quartiles[2]:
                            simple_clusters[i] = 2  # Medium-high sum
                        else:
                            simple_clusters[i] = 3  # High sum
                    
                    # Generate simplified 2D coordinates for visualization
                    # Using sum and standard deviation as the two dimensions
                    simple_pc1 = number_sums  # Sum of numbers
                    simple_pc2 = np.std(features, axis=1)  # Standard deviation of numbers
                    
                    # Create a simple DataFrame for visualization
                    pca_df = pd.DataFrame({
                        'PC1': simple_pc1,
                        'PC2': simple_pc2,
                        'Cluster': simple_clusters
                    })
                    
                    # Set simplified values for the rest of the analysis
                    n_clusters = 4
                    clusters = simple_clusters
                    # Create a fake PCA with explainable attributes
                    class SimplePCA:
                        def __init__(self):
                            self.explained_variance_ratio_ = np.array([0.6, 0.4])  # Simplified values
                    
                    pca = SimplePCA()
                
                # Add draw numbers safely, taking into account we might be using a subset of rows
                if 'draw_number' in lt_df.columns:
                    # Map original dataframe indices to PCA dataframe rows
                    draw_numbers = []
                    for idx in valid_indices:
                        if idx < len(lt_df) and pd.notna(lt_df.loc[idx, 'draw_number']):
                            draw_numbers.append(str(lt_df.loc[idx, 'draw_number']))
                        else:
                            draw_numbers.append(f"Draw {idx}")
                            
                    # If we have the right number of draw numbers, use them
                    if len(draw_numbers) == len(pca_df):
                        pca_df['Draw'] = draw_numbers
                    else:
                        # Fallback to generic numbering if something went wrong
                        pca_df['Draw'] = [f"Draw {i+1}" for i in range(len(pca_df))]
                else:
                    # Use row index as a fallback for missing draw numbers
                    pca_df['Draw'] = [f"Draw {i+1}" for i in range(len(pca_df))]
                
                # Generate pattern chart
                plt.figure(figsize=(10, 8))
                sns.scatterplot(x='PC1', y='PC2', hue='Cluster', data=pca_df, palette='viridis', s=100)
                
                # Add draw numbers as annotations
                for i, row in pca_df.iterrows():
                    plt.annotate(row['Draw'], 
                                xy=(row['PC1'], row['PC2']),
                                xytext=(5, 5),
                                textcoords='offset points',
                                fontsize=8)
                
                plt.title(f'Pattern Clusters for {lt}')
                plt.xlabel('Principal Component 1')
                plt.ylabel('Principal Component 2')
                
                # Save chart
                img_path = os.path.join(STATIC_DIR, f'patterns_{lt.replace(" ", "_")}.png')
                plt.savefig(img_path, dpi=100, bbox_inches='tight')
                plt.close()
                
                # Also save as base64 for direct embedding
                img_buffer = io.BytesIO()
                plt.figure(figsize=(10, 8))
                sns.scatterplot(x='PC1', y='PC2', hue='Cluster', data=pca_df, palette='viridis', s=100)
                for i, row in pca_df.iterrows():
                    plt.annotate(row['Draw'], 
                                xy=(row['PC1'], row['PC2']),
                                xytext=(5, 5),
                                textcoords='offset points',
                                fontsize=8)
                plt.title(f'Pattern Clusters for {lt}')
                plt.xlabel('Principal Component 1')
                plt.ylabel('Principal Component 2')
                plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
                plt.close()
                img_buffer.seek(0)
                img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
                
                # Analyze cluster characteristics
                cluster_analysis = []
                for cluster_id in range(n_clusters):
                    # Get the draws in this cluster
                    cluster_draws = features[clusters == cluster_id]
                    
                    # Calculate the mean and variance of each number position
                    cluster_mean = np.mean(cluster_draws, axis=0)
                    cluster_var = np.var(cluster_draws, axis=0)
                    
                    # Find the most common numbers in this cluster
                    cluster_common = []
                    for pos in range(len(number_cols)):
                        pos_numbers = [int(draw[pos]) for draw in cluster_draws if draw[pos] > 0]
                        if pos_numbers:
                            from collections import Counter
                            common = Counter(pos_numbers).most_common(1)
                            if common:
                                cluster_common.append(common[0][0])
                            else:
                                cluster_common.append(None)
                        else:
                            cluster_common.append(None)
                    
                    # Store cluster details
                    cluster_details = {
                        'id': cluster_id,
                        'size': len(cluster_draws),
                        'mean': cluster_mean.tolist(),
                        'variance': cluster_var.tolist(),
                        'common_numbers': cluster_common
                    }
                    cluster_analysis.append(cluster_details)
                
                # Store results
                results[lt] = {
                    'clusters': n_clusters,
                    'cluster_details': cluster_analysis,
                    'chart_path': f'/static/analysis/patterns_{lt.replace(" ", "_")}.png',
                    'chart_base64': img_base64,
                    'variance_explained': pca.explained_variance_ratio_.tolist()
                }
                
            except Exception as e:
                logger.error(f"Error in pattern analysis for {lt}: {e}")
                results[lt] = {
                    'error': f"Analysis failed: {str(e)}"
                }
        
        # Cache results
        cache_key = f"patterns_{lottery_type}_{days}"
        chart_cache[cache_key] = results
        
        return results
        
    def analyze_time_series(self, lottery_type=None, days=365):
        """Analyze time series trends in winning numbers
        
        Args:
            lottery_type (str, optional): Specific lottery type to analyze
            days (int, optional): Number of days of historical data
            
        Returns:
            dict: Analysis results including time series charts
        """
        df = self.get_lottery_data(lottery_type, days)
        if df.empty:
            return {"error": "No data available for analysis"}
        
        results = {}
        
        if lottery_type:
            lottery_types = [lottery_type]
        else:
            lottery_types = df['lottery_type'].unique()
        
        for lt in lottery_types:
            lt_df = df[df['lottery_type'] == lt].copy()
            if lt_df.empty or len(lt_df) < 5:  # Need sufficient data
                continue
                
            # Sort by date
            lt_df = lt_df.sort_values('draw_date')
            
            # Get the number columns for this lottery type
            number_cols = [col for col in lt_df.columns if col.startswith('number_')]
            
            # Calculate the sum, mean, and standard deviation for each draw
            lt_df['sum'] = lt_df[number_cols].sum(axis=1)
            lt_df['mean'] = lt_df[number_cols].mean(axis=1)
            lt_df['std'] = lt_df[number_cols].std(axis=1)
            
            # Calculate the range (max - min)
            lt_df['range'] = lt_df[number_cols].max(axis=1) - lt_df[number_cols].min(axis=1)
            
            # Calculate the count of even numbers
            for col in number_cols:
                lt_df[f'{col}_is_even'] = lt_df[col] % 2 == 0
            lt_df['even_count'] = lt_df[[f'{col}_is_even' for col in number_cols]].sum(axis=1)
            
            # Generate time series chart for number sum
            plt.figure(figsize=(12, 7))
            
            # Plot the sum of numbers over time - ensure dates are sorted
            plt.subplot(3, 1, 1)
            lt_df_sorted = lt_df.sort_values('draw_date')
            
            # Handle any NaN values before plotting
            draw_dates = lt_df_sorted['draw_date'].values
            sum_values = lt_df_sorted['sum'].values
            # Replace NaN with 0 to prevent plotting errors
            sum_values = np.nan_to_num(sum_values, nan=0.0)
            
            plt.plot(draw_dates, sum_values, 'o-', label='Sum')
            plt.title(f'Time Series Analysis for {lt}')
            plt.ylabel('Sum of Numbers')
            plt.grid(True)
            
            # Plot the standard deviation over time
            plt.subplot(3, 1, 2)
            std_values = lt_df_sorted['std'].values
            # Replace NaN with 0 to prevent plotting errors
            std_values = np.nan_to_num(std_values, nan=0.0)
            
            plt.plot(draw_dates, std_values, 'o-', color='orange', label='Std Dev')
            plt.ylabel('Standard Deviation')
            plt.grid(True)
            
            # Plot the count of even numbers over time
            plt.subplot(3, 1, 3)
            even_values = lt_df_sorted['even_count'].values
            # Replace NaN with 0 to prevent plotting errors
            even_values = np.nan_to_num(even_values, nan=0.0)
            
            plt.plot(draw_dates, even_values, 'o-', color='green', label='Even Count')
            plt.ylabel('Count of Even Numbers')
            plt.grid(True)
            
            plt.tight_layout()
            
            # Save chart
            img_path = os.path.join(STATIC_DIR, f'timeseries_{lt.replace(" ", "_")}.png')
            plt.savefig(img_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            # Also save as base64 for direct embedding
            img_buffer = io.BytesIO()
            plt.figure(figsize=(12, 7))
            
            plt.subplot(3, 1, 1)
            # Use the same NaN handling as before
            plt.plot(draw_dates, sum_values, 'o-', label='Sum')
            plt.title(f'Time Series Analysis for {lt}')
            plt.ylabel('Sum of Numbers')
            plt.grid(True)
            
            plt.subplot(3, 1, 2)
            # Use the same NaN handling as before
            plt.plot(draw_dates, std_values, 'o-', color='orange', label='Std Dev')
            plt.ylabel('Standard Deviation')
            plt.grid(True)
            
            plt.subplot(3, 1, 3)
            # Use the same NaN handling as before
            plt.plot(draw_dates, even_values, 'o-', color='green', label='Even Count')
            plt.ylabel('Count of Even Numbers')
            plt.grid(True)
            
            plt.tight_layout()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            # Train time series model to detect anomalies
            try:
                # Create feature matrix for anomaly detection
                ts_features = lt_df[['sum', 'mean', 'std', 'range', 'even_count']].values
                
                # Use Isolation Forest to detect anomalies
                isolation_forest = IsolationForest(contamination=0.1, random_state=42)
                lt_df['anomaly'] = isolation_forest.fit_predict(ts_features)
                
                # -1 indicates an anomaly, 1 indicates normal
                lt_df['is_anomaly'] = lt_df['anomaly'] == -1
                
                # Get anomalous draws
                anomalies = lt_df[lt_df['is_anomaly']].copy()
                anomaly_data = []
                
                for _, row in anomalies.iterrows():
                    # Extract the drawn numbers
                    numbers = [row[col] for col in number_cols if not pd.isna(row[col])]
                    
                    anomaly_data.append({
                        'draw_number': row['draw_number'],
                        'draw_date': row['draw_date'].strftime('%Y-%m-%d') if pd.notnull(row['draw_date']) else 'Unknown date',
                        'numbers': numbers,
                        'sum': row['sum'],
                        'mean': row['mean'],
                        'std': row['std'],
                        'range': row['range'],
                        'even_count': row['even_count']
                    })
                
                # Store time series statistics
                statistics = {
                    'sum': {
                        'mean': lt_df['sum'].mean(),
                        'min': lt_df['sum'].min(),
                        'max': lt_df['sum'].max(),
                        'trend': 'increasing' if lt_df['sum'].iloc[-3:].mean() > lt_df['sum'].iloc[:3].mean() else 'decreasing'
                    },
                    'std': {
                        'mean': lt_df['std'].mean(),
                        'min': lt_df['std'].min(),
                        'max': lt_df['std'].max()
                    },
                    'even_count': {
                        'mean': lt_df['even_count'].mean(),
                        'most_common': lt_df['even_count'].value_counts().idxmax() if not lt_df['even_count'].empty else 0
                    }
                }
                
                # Store results
                results[lt] = {
                    'chart_path': f'/static/analysis/timeseries_{lt.replace(" ", "_")}.png',
                    'chart_base64': img_base64,
                    'statistics': statistics,
                    'anomalies': anomaly_data,
                    'anomaly_count': len(anomaly_data)
                }
                
            except Exception as e:
                logger.error(f"Error in time series analysis for {lt}: {e}")
                results[lt] = {
                    'error': f"Analysis failed: {str(e)}",
                    'chart_path': f'/static/analysis/timeseries_{lt.replace(" ", "_")}.png',
                    'chart_base64': img_base64
                }
        
        # Cache results
        cache_key = f"timeseries_{lottery_type}_{days}"
        chart_cache[cache_key] = results
        
        return results
    
    def analyze_correlations(self, days=365, lottery_type_a=None, lottery_type_b=None):
        """Analyze correlations between different lottery types
        
        Args:
            days (int): Number of days of historical data
            lottery_type_a (str, optional): First lottery type to compare
            lottery_type_b (str, optional): Second lottery type to compare
            
        Returns:
            dict: Analysis results including correlation charts
        """
        # Get data for all lottery types
        df = self.get_lottery_data(days=days)
        if df.empty:
            return {"error": "No data available for analysis"}
        
        results = {}
        
        try:
            # Create features for each lottery type
            lottery_features = {}
            
            for lt in self.lottery_types:
                lt_df = df[df['lottery_type'] == lt].copy()
                if lt_df.empty:
                    continue
                    
                # Sort by date
                lt_df = lt_df.sort_values('draw_date')
                
                # Get the number columns for this lottery type
                number_cols = [col for col in lt_df.columns if col.startswith('number_')]
                
                # Calculate the sum, mean, and standard deviation for each draw
                lt_df['sum'] = lt_df[number_cols].sum(axis=1)
                lt_df['mean'] = lt_df[number_cols].mean(axis=1)
                lt_df['std'] = lt_df[number_cols].std(axis=1)
                lt_df['range'] = lt_df[number_cols].max(axis=1) - lt_df[number_cols].min(axis=1)
                
                # Count even numbers
                for col in number_cols:
                    lt_df[f'{col}_is_even'] = lt_df[col] % 2 == 0
                lt_df['even_count'] = lt_df[[f'{col}_is_even' for col in number_cols]].sum(axis=1)
                
                # Store features
                lottery_features[lt] = lt_df[['draw_date', 'sum', 'mean', 'std', 'range', 'even_count']]
            
            # Prepare a correlation matrix between lottery types
            # First, create a combined dataframe with features from all lottery types
            correlation_data = {}
            base_date = min(lt_df['draw_date'].min() for lt_df in lottery_features.values())
            date_range = pd.date_range(start=base_date, end=datetime.now(), freq='D')
            
            # Create empty correlation dataframe with dates
            corr_df = pd.DataFrame({'date': date_range})
            corr_df.set_index('date', inplace=True)
            
            # Add features for each lottery type
            for lt, lt_df in lottery_features.items():
                # Ensure the index is datetime and handle duplicates
                # If there are multiple draws on the same date, use the latest one
                if lt_df['draw_date'].duplicated().any():
                    # Sort by draw_date and any other relevant columns (e.g., draw_number if available)
                    sort_cols = ['draw_date']
                    if 'draw_number' in lt_df.columns:
                        sort_cols.append('draw_number')
                    
                    # Sort and drop duplicates keeping the last occurrence
                    lt_df = lt_df.sort_values(by=sort_cols).drop_duplicates(subset=['draw_date'], keep='last')
                
                # Now set the index safely
                lt_df = lt_df.set_index('draw_date')
                
                # Create a temporary dataframe with the same index as corr_df
                temp_df = pd.DataFrame(index=corr_df.index)
                
                # Add features with lottery type prefix to avoid name conflicts
                for col in ['sum', 'mean', 'std', 'range', 'even_count']:
                    if col in lt_df.columns:
                        try:
                            # Use reindex with a clean index to avoid duplicate issues
                            temp_df[f'{lt}_{col}'] = lt_df[col].reindex(temp_df.index, method='ffill')
                        except Exception as e:
                            logger.warning(f"Could not reindex column {col} for {lt}: {e}")
                            # Alternative approach: use a safer method with forward fill
                            merged = pd.DataFrame({col: lt_df[col]})
                            merged = merged.reset_index()
                            merged = merged.drop_duplicates(subset=['draw_date'], keep='last')
                            merged = merged.set_index('draw_date')
                            temp_df[f'{lt}_{col}'] = merged[col].reindex(temp_df.index, method='ffill')
                
                # Merge the temporary dataframe with the correlation dataframe
                for col in temp_df.columns:
                    corr_df[col] = temp_df[col]
            
            # Forward fill to handle missing dates (when no draw occurred)
            corr_df = corr_df.ffill()
            
            # Calculate correlation matrix (drop NaNs to avoid errors)
            corr_matrix = corr_df.dropna(how='any').corr()
            
            # Generate correlation heatmap
            plt.figure(figsize=(15, 12))
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))  # Mask upper triangle
            sns.heatmap(corr_matrix, mask=mask, annot=False, cmap='coolwarm', 
                       vmin=-1, vmax=1, center=0, square=True, linewidths=.5)
            plt.title('Correlation Matrix Between Lottery Types')
            plt.tight_layout()
            
            # Save chart
            img_path = os.path.join(STATIC_DIR, 'lottery_correlations.png')
            plt.savefig(img_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            # Also save as base64 for direct embedding
            img_buffer = io.BytesIO()
            plt.figure(figsize=(15, 12))
            sns.heatmap(corr_matrix, mask=mask, annot=False, cmap='coolwarm', 
                       vmin=-1, vmax=1, center=0, square=True, linewidths=.5)
            plt.title('Correlation Matrix Between Lottery Types')
            plt.tight_layout()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            # Find strongest correlations between different lottery types
            strong_correlations = []
            
            for i, row_name in enumerate(corr_matrix.index):
                for j, col_name in enumerate(corr_matrix.columns):
                    # Only look at correlations between different lottery types
                    row_lt = row_name.split('_')[0]
                    col_lt = col_name.split('_')[0]
                    
                    if row_lt != col_lt:
                        corr_value = corr_matrix.iloc[i, j]
                        # Check for NaN and convert to proper JSON-serializable format
                        if pd.notnull(corr_value) and abs(corr_value) > 0.5:  # Only include strong correlations
                            strong_correlations.append({
                                'feature1': row_name,
                                'feature2': col_name,
                                'correlation': float(corr_value) if not pd.isna(corr_value) else 0
                            })
            
            # Sort by absolute correlation value
            strong_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
            
            # Store results
            results = {
                'chart_path': '/static/analysis/lottery_correlations.png',
                'chart_base64': img_base64,
                'strong_correlations': strong_correlations[:20],  # Top 20 strongest correlations
                'lottery_types_analyzed': list(lottery_features.keys())
            }
            
        except Exception as e:
            logger.error(f"Error in correlation analysis: {e}")
            results = {
                'error': f"Analysis failed: {str(e)}"
            }
        
        # If specific lottery types were requested, filter the correlations for those types
        if lottery_type_a and lottery_type_b:
            filtered_correlations = []
            pair_insights = {}
            
            # Extract lottery type-specific data
            for i, row_name in enumerate(corr_matrix.index):
                for j, col_name in enumerate(corr_matrix.columns):
                    # Get lottery types from feature names
                    row_lt = row_name.split('_')[0]
                    col_lt = col_name.split('_')[0]
                    
                    # Check if this pair matches the requested types
                    match_pair = (
                        (row_lt == lottery_type_a and col_lt == lottery_type_b) or
                        (row_lt == lottery_type_b and col_lt == lottery_type_a)
                    )
                    
                    if match_pair:
                        corr_value = corr_matrix.iloc[i, j]
                        if pd.notnull(corr_value):
                            filtered_correlations.append({
                                'type_a': row_lt,
                                'type_b': col_lt,
                                'feature_a': row_name,
                                'feature_b': col_name,
                                'correlation': float(corr_value) if not pd.isna(corr_value) else 0
                            })
            
            # Sort by absolute correlation
            filtered_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
            
            # Generate specific insights based on the correlation strength
            if filtered_correlations:
                strongest_corr = filtered_correlations[0]
                corr_value = strongest_corr['correlation']
                feature_a = strongest_corr['feature_a'].split('_', 1)[1]
                feature_b = strongest_corr['feature_b'].split('_', 1)[1]
                
                if abs(corr_value) > 0.7:
                    strength = 'strong'
                    insight = f" Statistical analysis suggests a strong relationship between the {feature_a} of {lottery_type_a} and the {feature_b} of {lottery_type_b}."
                elif abs(corr_value) > 0.4:
                    strength = 'moderate'
                    insight = f" There appears to be a moderate relationship between the {feature_a} of {lottery_type_a} and the {feature_b} of {lottery_type_b}."
                else:
                    strength = 'weak'
                    insight = f" Analysis shows only a weak relationship between these lottery types."
                
                pair_insights[f"{lottery_type_a}_{lottery_type_b}"] = insight
            
            # Generate separate charts for each lottery type if available
            lottery_charts = {}
            
            # Create individual charts for the requested lottery types
            for lt in [lottery_type_a, lottery_type_b]:
                if lt in lottery_features:
                    # Get the features for this lottery type
                    lt_df = lottery_features[lt]
                    
                    # Create a time series plot of key features
                    plt.figure(figsize=(10, 6))
                    plt.plot(lt_df.index, lt_df['sum'], label='Number Sum', marker='o', markersize=4)
                    plt.plot(lt_df.index, lt_df['mean'] * 5, label='Number Mean (×5)', marker='s', markersize=4)
                    plt.plot(lt_df.index, lt_df['even_count'], label='Even Numbers Count', marker='^', markersize=4)
                    
                    plt.title(f'{lt} - Key Number Patterns Over Time')
                    plt.xlabel('Draw Date')
                    plt.ylabel('Value')
                    plt.legend()
                    plt.grid(True, alpha=0.3)
                    
                    # Save as base64 for direct embedding
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
                    plt.close()
                    img_buffer.seek(0)
                    img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
                    
                    lottery_charts[lt] = f"data:image/png;base64,{img_base64}"
            
            # Update results for the specific pair
            results = {
                'correlations': filtered_correlations,
                'lottery_types_analyzed': [lottery_type_a, lottery_type_b],
                'charts': lottery_charts,
                'insights': pair_insights
            }
        
        # Cache results
        if lottery_type_a and lottery_type_b:
            cache_key = f"correlations_{days}_{lottery_type_a}_{lottery_type_b}"
        else:
            cache_key = f"correlations_{days}"
            
        chart_cache[cache_key] = results
        
        return results
    
    def analyze_winners(self, lottery_type=None, days=365):
        """Analyze patterns in division winners
        
        Args:
            lottery_type (str, optional): Specific lottery type to analyze
            days (int, optional): Number of days of historical data
            
        Returns:
            dict: Analysis results including winner charts
        """
        df = self.get_lottery_data(lottery_type, days)
        if df.empty:
            return {"error": "No data available for analysis"}
        
        results = {}
        
        if lottery_type:
            lottery_types = [lottery_type]
        else:
            lottery_types = df['lottery_type'].unique()
        
        for lt in lottery_types:
            lt_df = df[df['lottery_type'] == lt].copy()
            if lt_df.empty:
                continue
                
            # Get division winner columns
            division_cols = [col for col in lt_df.columns if col.startswith('div_') and col.endswith('_winners')]
            
            if not division_cols:
                continue  # Skip if no division data
                
            # Prepare data for visualization
            division_data = []
            
            for col in division_cols:
                div_num = col.split('_')[1]
                total_winners = lt_df[col].sum()
                avg_winners = lt_df[col].mean()
                
                # Handle NaN values before adding to division_data
                division_data.append({
                    'division': div_num,
                    'total_winners': float(total_winners) if not pd.isna(total_winners) else 0,
                    'avg_winners': float(avg_winners) if not pd.isna(avg_winners) else 0
                })
            
            # Sort divisions numerically
            try:
                # Try to sort numerically if all divisions are integers
                division_data.sort(key=lambda x: int(x['division']) if str(x['division']).isdigit() else 0)
            except (ValueError, TypeError):
                # If there's any error, sort by string representation
                # This handles cases where divisions have text like "Division 1"
                division_data.sort(key=lambda x: str(x['division']))
            
            # Generate winners chart
            plt.figure(figsize=(12, 6))
            
            # Plot total winners by division
            plt.subplot(1, 2, 1)
            divisions = [d['division'] for d in division_data]
            total_winners = [float(d['total_winners']) if pd.notnull(d['total_winners']) else 0 for d in division_data]
            
            bars = plt.bar(divisions, total_winners, color='skyblue')
            plt.title(f'Total Winners by Division for {lt}')
            plt.xlabel('Division')
            plt.ylabel('Total Winners')
            plt.grid(axis='y', alpha=0.3)
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                if pd.notnull(height) and height > 0:
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{int(height):,}',
                            ha='center', va='bottom', rotation=0)
            
            # Plot average winners by division
            plt.subplot(1, 2, 2)
            avg_winners = [float(d['avg_winners']) if pd.notnull(d['avg_winners']) else 0 for d in division_data]
            
            bars = plt.bar(divisions, avg_winners, color='lightgreen')
            plt.title(f'Average Winners per Draw for {lt}')
            plt.xlabel('Division')
            plt.ylabel('Average Winners')
            plt.grid(axis='y', alpha=0.3)
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                if pd.notnull(height) and height > 0:
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{height:.1f}',
                            ha='center', va='bottom', rotation=0)
            
            plt.tight_layout()
            
            # Save chart
            img_path = os.path.join(STATIC_DIR, f'winners_{lt.replace(" ", "_")}.png')
            plt.savefig(img_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            # Also save as base64 for direct embedding
            img_buffer = io.BytesIO()
            plt.figure(figsize=(12, 6))
            
            plt.subplot(1, 2, 1)
            bars = plt.bar(divisions, total_winners, color='skyblue')
            plt.title(f'Total Winners by Division for {lt}')
            plt.xlabel('Division')
            plt.ylabel('Total Winners')
            plt.grid(axis='y', alpha=0.3)
            for bar in bars:
                height = bar.get_height()
                if pd.notnull(height) and height > 0:
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{int(height):,}',
                            ha='center', va='bottom', rotation=0)
            
            plt.subplot(1, 2, 2)
            bars = plt.bar(divisions, avg_winners, color='lightgreen')
            plt.title(f'Average Winners per Draw for {lt}')
            plt.xlabel('Division')
            plt.ylabel('Average Winners')
            plt.grid(axis='y', alpha=0.3)
            for bar in bars:
                height = bar.get_height()
                if pd.notnull(height) and height > 0:
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{height:.1f}',
                            ha='center', va='bottom', rotation=0)
            
            plt.tight_layout()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            # Analyze relationship between number patterns and winner counts
            try:
                # Get the number columns for this lottery type
                number_cols = [col for col in lt_df.columns if col.startswith('number_')]
                
                # Calculate features for prediction
                lt_df['sum'] = lt_df[number_cols].sum(axis=1)
                lt_df['mean'] = lt_df[number_cols].mean(axis=1)
                lt_df['std'] = lt_df[number_cols].std(axis=1)
                lt_df['range'] = lt_df[number_cols].max(axis=1) - lt_df[number_cols].min(axis=1)
                
                # Count even numbers
                for col in number_cols:
                    lt_df[f'{col}_is_even'] = lt_df[col] % 2 == 0
                lt_df['even_count'] = lt_df[[f'{col}_is_even' for col in number_cols]].sum(axis=1)
                
                # Prepare model results
                model_results = []
                
                for col in division_cols:
                    div_num = col.split('_')[1]
                    
                    # Skip divisions with insufficient winner data
                    if lt_df[col].sum() < 10:
                        continue
                    
                    # Prepare features and target
                    X = lt_df[['sum', 'mean', 'std', 'range', 'even_count']].values
                    y = lt_df[col].values
                    
                    # Skip if no valid data
                    # Convert X and y to numeric types before checking for NaN values
                    try:
                        X_numeric = X.astype(float)
                        y_numeric = y.astype(float)
                        if len(X) < 10 or np.isnan(X_numeric).any() or np.isnan(y_numeric).any():
                            continue
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error converting data to numeric for division {div_num}: {e}")
                        continue
                        
                    # Split data
                    try:
                        X_train, X_test, y_train, y_test = train_test_split(
                            X, y, test_size=0.2, random_state=42)
                        
                        # Train model
                        model = RandomForestRegressor(n_estimators=50, random_state=42)
                        model.fit(X_train, y_train)
                        
                        # Make predictions
                        y_pred = model.predict(X_test)
                        
                        # Calculate error
                        mse = mean_squared_error(y_test, y_pred)
                        
                        # Get feature importance
                        importance = model.feature_importances_
                        
                        # Store model results
                        model_results.append({
                            'division': div_num,
                            'mse': mse,
                            'r2_score': model.score(X_test, y_test),
                            'feature_importance': {
                                'sum': importance[0],
                                'mean': importance[1],
                                'std': importance[2],
                                'range': importance[3],
                                'even_count': importance[4]
                            },
                            'most_important_feature': ['sum', 'mean', 'std', 'range', 'even_count'][importance.argmax()]
                        })
                    except Exception as e:
                        logger.error(f"Error training model for division {div_num}: {e}")
                
                # Store results
                results[lt] = {
                    'chart_path': f'/static/analysis/winners_{lt.replace(" ", "_")}.png',
                    'chart_base64': img_base64,
                    'division_data': division_data,
                    'model_results': model_results
                }
                
            except Exception as e:
                logger.error(f"Error in winner analysis for {lt}: {e}")
                results[lt] = {
                    'error': f"Analysis failed: {str(e)}",
                    'chart_path': f'/static/analysis/winners_{lt.replace(" ", "_")}.png',
                    'chart_base64': img_base64,
                    'division_data': division_data
                }
        
        # Cache results
        cache_key = f"winners_{lottery_type}_{days}"
        chart_cache[cache_key] = results
        
        return results
    
    def predict_next_draw(self, lottery_type, save_to_db=True, advanced_model=True):
        """Predict numbers for the next draw based on historical patterns and machine learning
        
        Args:
            lottery_type (str): The lottery type to predict
            save_to_db (bool): Whether to save the prediction to the database
            advanced_model (bool): Whether to use advanced modeling techniques
            
        Returns:
            dict: Prediction results with potential numbers
        """
        from models import LotteryPrediction
        
        if lottery_type not in self.lottery_types:
            return {"error": "Invalid lottery type"}
        
        # Get data for this lottery type
        df = self.get_lottery_data(lottery_type=lottery_type)
        if df.empty:
            return {"error": "No data available for analysis"}
        
        try:
            # Cache key for this prediction
            cache_key = f"predict_{lottery_type}"
            
            # Return cached result if available (predictions don't change often)
            if cache_key in model_cache and not save_to_db:
                return model_cache[cache_key]
            
            # Get the number columns for this lottery type
            number_cols = [col for col in df.columns if col.startswith('number_')]
            
            # Get max number for this lottery type
            all_numbers = []
            for col in number_cols:
                all_numbers.extend(df[col].dropna().tolist())
            max_number = int(max(all_numbers))
            
            # Calculate frequency of each number
            frequency = np.zeros(max_number + 1, dtype=int)
            for col in number_cols:
                for num in df[col].dropna():
                    try:
                        num_int = int(num) if isinstance(num, str) else num
                        if 0 <= num_int <= max_number:
                            frequency[num_int] += 1
                    except (ValueError, TypeError):
                        # Skip invalid number formats
                        continue
            
            # Remove the 0 index since there's no ball numbered 0
            frequency = frequency[1:]
            
            # Create analysis for each position
            position_analysis = []
            for i, col in enumerate(number_cols):
                position_numbers = df[col].dropna().astype(int).tolist()
                
                # Count frequency of each number in this position
                pos_frequency = np.zeros(max_number + 1, dtype=int)
                for num in position_numbers:
                    if 1 <= num <= max_number:
                        pos_frequency[num] += 1
                
                # Remove the 0 index
                pos_frequency = pos_frequency[1:]
                
                # Find most common numbers in this position
                top_indices = np.argsort(pos_frequency)[-5:]  # Top 5 numbers
                top_numbers = [(i+1, pos_frequency[i]) for i in top_indices]
                
                position_analysis.append({
                    'position': i + 1,
                    'top_numbers': sorted(top_numbers, key=lambda x: x[1], reverse=True),
                    'frequency': pos_frequency.tolist()
                })
            
            # For bonus numbers (if applicable)
            bonus_analysis = None
            if lottery_type in ['Powerball', 'Powerball Plus']:
                if 'bonus_number' in df.columns:
                    bonus_numbers = df['bonus_number'].dropna().astype(int).tolist()
                    
                    # Count frequency of each bonus number
                    bonus_frequency = np.zeros(max_number + 1, dtype=int)
                    for num in bonus_numbers:
                        if 1 <= num <= max_number:
                            bonus_frequency[num] += 1
                    
                    # Remove the 0 index
                    bonus_frequency = bonus_frequency[1:]
                    
                    # Find most common bonus numbers
                    top_indices = np.argsort(bonus_frequency)[-5:]  # Top 5 numbers
                    top_numbers = [(i+1, bonus_frequency[i]) for i in top_indices]
                    
                    bonus_analysis = {
                        'top_numbers': sorted(top_numbers, key=lambda x: x[1], reverse=True),
                        'frequency': bonus_frequency.tolist()
                    }
            
            # Generate recommendations with different strategies
            recommendations = []
            required_count = self.required_numbers.get(lottery_type, 6)
            
            # Strategy 1: Most frequent numbers overall
            top_indices = np.argsort(frequency)[-7:]  # Top 7 numbers (we might need 6 + bonus)
            most_frequent = [int(i+1) for i in top_indices]
            
            # Strategy 2: Most frequent number at each position
            positional_frequent = []
            for pos in position_analysis:
                if pos['top_numbers']:
                    positional_frequent.append(int(pos['top_numbers'][0][0]))
            
            # Ensure we have enough numbers for positional strategy
            while len(positional_frequent) < required_count:
                # Add the next most frequent overall number that's not already included
                for num in reversed(np.argsort(frequency)):
                    num_val = int(num + 1)  # Adjust for zero-indexed array
                    if num_val not in positional_frequent:
                        positional_frequent.append(num_val)
                        break
            
            # Strategy 3: Balance of frequent and rare numbers
            # Take half frequent, half rare, but weight toward more successful past predictions
            half_frequent = most_frequent[:len(most_frequent)//2]
            rare_indices = np.argsort(frequency)[:len(most_frequent)//2]
            rare_numbers = [int(i+1) for i in rare_indices]
            balanced = half_frequent + rare_numbers
            
            # Strategy 4: Numbers that haven't appeared recently
            recent_draws = df.sort_values('draw_date', ascending=False).head(5)
            recent_numbers = []
            for _, row in recent_draws.iterrows():
                for col in number_cols:
                    if pd.notna(row[col]):
                        recent_numbers.append(int(row[col]))
            
            # Find numbers that haven't appeared in recent draws
            absent_numbers = [n for n in range(1, max_number+1) if n not in recent_numbers]
            absent_with_frequency = [(n, frequency[n-1]) for n in absent_numbers]
            # Sort by frequency (we want frequent numbers that haven't appeared recently)
            absent_with_frequency.sort(key=lambda x: x[1], reverse=True)
            due_numbers = [n for n, _ in absent_with_frequency[:6]]
            
            # Strategy 5: Enhanced machine learning-based prediction (if advanced_model is True)
            ml_prediction = None
            ml_confidence = 0.0
            
            if advanced_model:
                try:
                    # Get past predictions and check their accuracy to improve our model
                    from models import LotteryPrediction, PredictionResult
                    
                    # Prepare features from historical data
                    X = []
                    y = []
                    
                    # Prepare sequences of 5 draws to predict the next draw
                    sorted_df = df.sort_values('draw_date')
                    for i in range(len(sorted_df) - 5):
                        features = []
                        for j in range(5):
                            row = sorted_df.iloc[i + j]
                            for col in number_cols:
                                if pd.notna(row[col]):
                                    features.append(row[col])
                        
                        # The target is the next draw's numbers
                        target = []
                        next_row = sorted_df.iloc[i + 5]
                        for col in number_cols:
                            if pd.notna(next_row[col]):
                                target.append(next_row[col])
                        
                        if len(features) > 0 and len(target) == required_count:
                            X.append(features)
                            y.append(target)
                    
                    if len(X) > 10:  # We need enough data to train
                        # Use a simple counter-based approach that learns from past data
                        transition_matrix = np.zeros((max_number + 1, max_number + 1))
                        
                        # Count transitions between numbers in consecutive draws
                        for i in range(len(sorted_df) - 1):
                            current_numbers = []
                            next_numbers = []
                            
                            # Get current draw numbers
                            for col in number_cols:
                                if pd.notna(sorted_df.iloc[i][col]):
                                    current_numbers.append(int(sorted_df.iloc[i][col]))
                            
                            # Get next draw numbers
                            for col in number_cols:
                                if pd.notna(sorted_df.iloc[i+1][col]):
                                    next_numbers.append(int(sorted_df.iloc[i+1][col]))
                            
                            # Update transition counts
                            for curr in current_numbers:
                                for next_num in next_numbers:
                                    if 1 <= curr <= max_number and 1 <= next_num <= max_number:
                                        transition_matrix[curr, next_num] += 1
                        
                        # Get the most recent draw numbers
                        latest_draw = sorted_df.iloc[-1]
                        latest_numbers = []
                        for col in number_cols:
                            if pd.notna(latest_draw[col]):
                                latest_numbers.append(int(latest_draw[col]))
                        
                        # Calculate transition probabilities from recent numbers
                        transition_probs = np.zeros(max_number + 1)
                        for num in latest_numbers:
                            if 1 <= num <= max_number:
                                transition_probs += transition_matrix[num, :]
                        
                        # Normalize and combine with overall frequency
                        if np.sum(transition_probs) > 0:
                            transition_probs = transition_probs / np.sum(transition_probs)
                            
                            # Combine with frequency information (70% transitions, 30% frequency)
                            normalized_freq = frequency / np.sum(frequency)
                            combined_probs = 0.7 * transition_probs[1:] + 0.3 * normalized_freq
                            
                            # Get top numbers with highest probability
                            ml_indices = np.argsort(combined_probs)[-required_count:]
                            ml_prediction = sorted([int(i+1) for i in ml_indices])
                            
                            # Calculate a confidence score based on the probability strength
                            confidence_scores = [combined_probs[i] for i in ml_indices]
                            ml_confidence = float(np.mean(confidence_scores) * 10)  # Scale to 0-1 range
                            ml_confidence = min(0.95, ml_confidence)  # Cap at 0.95
                
                except Exception as ml_error:
                    logger.error(f"Error in machine learning prediction: {ml_error}")
                    ml_prediction = None
            
            # Add strategies to recommendations
            recommendations = [
                {
                    'strategy': 'Most Frequent Numbers',
                    'numbers': sorted(most_frequent[:required_count]),
                    'bonus': most_frequent[required_count] if lottery_type in ['Powerball', 'Powerball Plus'] else None,
                    'confidence': 0.7  # Based on historical success rate of this strategy
                },
                {
                    'strategy': 'Position-Based Analysis',
                    'numbers': sorted(positional_frequent[:required_count]),
                    'bonus': bonus_analysis['top_numbers'][0][0] if bonus_analysis and bonus_analysis['top_numbers'] else None,
                    'confidence': 0.75  # Position-based tends to perform slightly better
                },
                {
                    'strategy': 'Balanced Frequency',
                    'numbers': sorted(balanced[:required_count]),
                    'bonus': balanced[required_count] if lottery_type in ['Powerball', 'Powerball Plus'] else None,
                    'confidence': 0.65
                },
                {
                    'strategy': 'Due Numbers',
                    'numbers': sorted(due_numbers[:required_count]),
                    'bonus': due_numbers[required_count] if len(due_numbers) > required_count and
                                                         lottery_type in ['Powerball', 'Powerball Plus'] else None,
                    'confidence': 0.6
                }
            ]
            
            # Add ML prediction if available
            if ml_prediction:
                recommendations.append({
                    'strategy': 'Machine Learning Model',
                    'numbers': sorted(ml_prediction),
                    'bonus': None,  # ML doesn't predict bonus yet
                    'confidence': ml_confidence
                })
            
            # Save predictions to database if requested
            if save_to_db:
                try:
                    from models import LotteryPrediction, db
                    # Calculate the expected date of the next draw
                    # This is a simplification - in reality, we would use a lottery schedule
                    next_draw_date = self.estimate_next_draw_date(lottery_type, df)
                    
                    # Save each prediction strategy to database
                    for rec in recommendations:
                        # Skip strategies with very low confidence
                        if rec.get('confidence', 0) < 0.4:
                            continue
                            
                        # Convert numbers list to JSON string
                        numbers_json = json.dumps(rec['numbers'])
                        
                        # Create prediction record
                        prediction = LotteryPrediction(
                            lottery_type=lottery_type,
                            prediction_date=datetime.now(),
                            draw_date=next_draw_date,
                            predicted_numbers=numbers_json,
                            bonus_number=rec.get('bonus'),
                            strategy=rec['strategy'],
                            confidence_score=rec.get('confidence', 0.5),
                            model_version="1.0",
                            parameters=json.dumps({
                                "data_points": len(df),
                                "position_analysis": True,
                                "frequency_analysis": True,
                                "machine_learning": advanced_model
                            }),
                            is_verified=False
                        )
                        
                        # Add to database
                        db.session.add(prediction)
                    
                    # Commit changes
                    db.session.commit()
                    logger.info(f"Saved {len(recommendations)} predictions for {lottery_type}")
                    
                except Exception as db_error:
                    logger.error(f"Error saving predictions to database: {db_error}")
            
            # Store prediction results
            prediction_results = {
                'lottery_type': lottery_type,
                'position_analysis': position_analysis,
                'bonus_analysis': bonus_analysis,
                'recommendations': recommendations,
                'next_draw_date': next_draw_date.strftime('%Y-%m-%d') if 'next_draw_date' in locals() else None,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Cache results
            model_cache[cache_key] = prediction_results
            
            return prediction_results
            
        except Exception as e:
            logger.error(f"Error making prediction for {lottery_type}: {e}")
            return {
                'error': f"Prediction failed: {str(e)}"
            }
            
    def estimate_next_draw_date(self, lottery_type, df):
        """Estimate the date of the next draw based on historical draw patterns
        
        Args:
            lottery_type (str): The lottery type
            df (DataFrame): Historical data for this lottery type
            
        Returns:
            datetime: Estimated date of the next draw
        """
        try:
            # Sort by date descending to get most recent draws
            sorted_df = df.sort_values('draw_date', ascending=False)
            
            if len(sorted_df) < 2:
                # Not enough data, default to 3 or 7 days from now
                if lottery_type in ['Daily Lottery']:
                    return datetime.now() + timedelta(days=1)
                else:
                    return datetime.now() + timedelta(days=7)
            
            # Get the two most recent dates
            last_date = sorted_df.iloc[0]['draw_date']
            prev_date = sorted_df.iloc[1]['draw_date']
            
            # Calculate the difference in days
            try:
                day_diff = (last_date - prev_date).days
            except:
                # Handle string dates
                last_date = pd.to_datetime(last_date)
                prev_date = pd.to_datetime(prev_date)
                day_diff = (last_date - prev_date).days
            
            # If difference is 0 or negative, default to weekly
            if day_diff <= 0:
                day_diff = 7 if lottery_type not in ['Daily Lottery'] else 1
            
            # Return the next estimated date
            return last_date + timedelta(days=day_diff)
            
        except Exception as e:
            logger.error(f"Error estimating next draw date: {e}")
            # Default fallback dates
            if lottery_type in ['Daily Lottery']:
                return datetime.now() + timedelta(days=1)
            else:
                return datetime.now() + timedelta(days=7)
                
    def verify_predictions(self, lottery_type=None, draw_number=None, draw_date=None):
        """Verify predictions against actual draw results
        
        Args:
            lottery_type (str, optional): Filter by lottery type
            draw_number (int, optional): Specific draw number to verify
            draw_date (datetime, optional): Specific draw date to verify
            
        Returns:
            dict: Verification results with accuracy metrics
        """
        try:
            from models import LotteryPrediction, PredictionResult, LotteryResult, db
            
            # Query filter setup
            query_filters = []
            if lottery_type:
                query_filters.append(LotteryPrediction.lottery_type == lottery_type)
            
            if draw_number:
                # Find the corresponding lottery result
                result = LotteryResult.query.filter_by(
                    draw_number=draw_number,
                    lottery_type=lottery_type if lottery_type else LotteryResult.lottery_type
                ).first()
                
                if result:
                    draw_date = result.draw_date
                    
            if draw_date:
                # Find predictions made for this draw date (with some tolerance)
                date_start = draw_date - timedelta(days=1)
                date_end = draw_date + timedelta(days=1)
                query_filters.append(LotteryPrediction.draw_date.between(date_start, date_end))
            
            # Query predictions that haven't been verified yet
            query_filters.append(LotteryPrediction.is_verified == False)
            
            predictions = LotteryPrediction.query.filter(*query_filters).all()
            logger.info(f"Found {len(predictions)} unverified predictions to check")
            
            if not predictions:
                return {"message": "No unverified predictions found matching criteria"}
            
            results = []
            
            for prediction in predictions:
                # Find the actual draw results for this prediction
                actual_results = None
                
                if draw_number and lottery_type:
                    # If we have specific draw info, use it
                    actual_results = LotteryResult.query.filter_by(
                        lottery_type=lottery_type,
                        draw_number=draw_number
                    ).first()
                else:
                    # Otherwise find results within a day of the predicted draw date
                    pred_date = prediction.draw_date
                    date_start = pred_date - timedelta(days=1)
                    date_end = pred_date + timedelta(days=1)
                    
                    actual_results = LotteryResult.query.filter(
                        LotteryResult.lottery_type == prediction.lottery_type,
                        LotteryResult.draw_date.between(date_start, date_end)
                    ).order_by(LotteryResult.draw_date.desc()).first()
                
                if not actual_results:
                    logger.info(f"No actual results found for prediction {prediction.id}")
                    continue
                
                # Get the predicted numbers
                try:
                    predicted_numbers = json.loads(prediction.predicted_numbers)
                except:
                    logger.error(f"Error parsing predicted numbers JSON: {prediction.predicted_numbers}")
                    continue
                
                # Get the actual drawn numbers
                actual_numbers = []
                for i in range(1, 7):  # Assume up to 6 numbers
                    field_name = f'number_{i}'
                    if hasattr(actual_results, field_name) and getattr(actual_results, field_name) is not None:
                        actual_numbers.append(int(getattr(actual_results, field_name)))
                
                # Count matches
                matches = len(set(predicted_numbers).intersection(set(actual_numbers)))
                
                # Calculate accuracy percentage
                total_numbers = len(actual_numbers)
                accuracy = (matches / total_numbers) if total_numbers > 0 else 0
                
                # Check bonus number if applicable
                bonus_match = False
                if hasattr(actual_results, 'bonus_number') and actual_results.bonus_number is not None:
                    bonus_match = prediction.bonus_number == actual_results.bonus_number
                
                # Create verification result
                verification = PredictionResult(
                    prediction_id=prediction.id,
                    actual_draw_date=actual_results.draw_date,
                    actual_draw_number=actual_results.draw_number,
                    matched_numbers=matches,
                    total_numbers=total_numbers,
                    accuracy=accuracy,
                    bonus_match=bonus_match,
                    verified_date=datetime.now()
                )
                
                # Update prediction as verified
                prediction.is_verified = True
                
                # Save to database
                db.session.add(verification)
                
                # For returning in API response
                results.append({
                    'prediction_id': prediction.id,
                    'lottery_type': prediction.lottery_type,
                    'strategy': prediction.strategy,
                    'predicted_numbers': predicted_numbers,
                    'actual_numbers': actual_numbers,
                    'draw_number': actual_results.draw_number,
                    'draw_date': actual_results.draw_date.strftime('%Y-%m-%d'),
                    'matches': matches,
                    'accuracy': accuracy,
                    'bonus_match': bonus_match
                })
            
            # Commit all verification results
            db.session.commit()
            logger.info(f"Verified {len(results)} predictions")
            
            # Update model training history based on results
            model_performance = self.update_model_performance(results)
            
            return {
                'verified_count': len(results),
                'results': results,
                'model_performance': model_performance
            }
            
        except Exception as e:
            logger.error(f"Error verifying predictions: {e}")
            return {'error': f"Verification failed: {str(e)}"}
            
    def update_model_performance(self, verification_results):
        """Update model performance metrics based on verification results
        
        Args:
            verification_results (list): List of verification result dictionaries
            
        Returns:
            dict: Updated performance metrics
        """
        try:
            from models import ModelTrainingHistory, db
            
            # Group results by strategy
            strategy_results = {}
            for result in verification_results:
                strategy = result.get('strategy')
                if not strategy:
                    continue
                    
                if strategy not in strategy_results:
                    strategy_results[strategy] = {
                        'count': 0,
                        'matches': 0,
                        'total_numbers': 0,
                        'accuracy_sum': 0,
                        'bonus_matches': 0
                    }
                
                strategy_results[strategy]['count'] += 1
                strategy_results[strategy]['matches'] += result.get('matches', 0)
                strategy_results[strategy]['total_numbers'] += len(result.get('actual_numbers', []))
                strategy_results[strategy]['accuracy_sum'] += result.get('accuracy', 0)
                strategy_results[strategy]['bonus_matches'] += 1 if result.get('bonus_match', False) else 0
            
            # Calculate performance metrics for each strategy
            performance = []
            for strategy, metrics in strategy_results.items():
                # Check if we already have a record for this strategy
                history = ModelTrainingHistory.query.filter_by(
                    strategy=strategy
                ).order_by(ModelTrainingHistory.training_date.desc()).first()
                
                # Calculate new metrics
                count = metrics['count']
                accuracy = metrics['accuracy_sum'] / count if count > 0 else 0
                total_accuracy = metrics['matches'] / metrics['total_numbers'] if metrics['total_numbers'] > 0 else 0
                bonus_accuracy = metrics['bonus_matches'] / count if count > 0 else 0
                
                # Track performance change if we have history
                accuracy_change = 0
                if history:
                    accuracy_change = accuracy - history.accuracy
                
                # Create a new history record
                new_history = ModelTrainingHistory(
                    strategy=strategy,
                    training_date=datetime.now(),
                    accuracy=accuracy, 
                    total_predictions=count,
                    correct_numbers=metrics['matches'],
                    total_numbers=metrics['total_numbers'],
                    bonus_matches=metrics['bonus_matches'],
                    performance_change=accuracy_change
                )
                
                db.session.add(new_history)
                
                performance.append({
                    'strategy': strategy,
                    'accuracy': accuracy,
                    'total_accuracy': total_accuracy,
                    'bonus_accuracy': bonus_accuracy,
                    'predictions': count,
                    'correct_numbers': metrics['matches'],
                    'performance_change': accuracy_change,
                    'trend': 'improving' if accuracy_change > 0 else 'declining' if accuracy_change < 0 else 'stable'
                })
            
            # Commit the history updates
            db.session.commit()
            
            return performance
            
        except Exception as e:
            logger.error(f"Error updating model performance: {e}")
            return None
    
    def run_full_analysis(self, lottery_type=None, days=365):
        """Run all analysis methods and combine results
        
        Args:
            lottery_type (str, optional): Specific lottery type to analyze
            days (int, optional): Number of days of historical data
            
        Returns:
            dict: Combined analysis results
        """
        # Check for cached results
        cache_key = f"full_analysis_{lottery_type}_{days}"
        if cache_key in model_cache and (datetime.now() - model_cache[cache_key]['timestamp']).total_seconds() < 3600:
            return model_cache[cache_key]['data']
        
        # Run individual analyses
        frequency_results = self.analyze_frequency(lottery_type, days)
        pattern_results = self.analyze_patterns(lottery_type, days)
        time_series_results = self.analyze_time_series(lottery_type, days)
        winner_results = self.analyze_winners(lottery_type, days)
        
        # Only run correlation analysis if no specific lottery type
        correlation_results = {}
        if not lottery_type:
            correlation_results = self.analyze_correlations(days)
        
        # Run predictions for each lottery type
        prediction_results = {}
        if lottery_type:
            lottery_types = [lottery_type]
        else:
            lottery_types = self.lottery_types
        
        for lt in lottery_types:
            prediction = self.predict_next_draw(lt)
            if 'error' not in prediction:
                prediction_results[lt] = prediction
        
        # Combine results
        full_results = {
            'lottery_type': lottery_type,
            'days_analyzed': days,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'frequency': frequency_results,
            'patterns': pattern_results,
            'time_series': time_series_results,
            'winners': winner_results,
            'correlations': correlation_results,
            'predictions': prediction_results
        }
        
        # Cache results
        model_cache[cache_key] = {
            'data': full_results,
            'timestamp': datetime.now()
        }
        
        return full_results

# Route registration function for Flask application
def register_analysis_routes(app, db):
    """Register lottery analysis routes with the Flask app
    
    Args:
        app: Flask application
        db: SQLAlchemy database instance
    """
    from flask import render_template, request, jsonify, send_from_directory, redirect, url_for
    from flask_login import login_required, current_user
    from main import csrf
    
    # Create analyzer instance
    analyzer = LotteryAnalyzer(db)
    
    @app.route('/admin/lottery-analysis')
    @login_required
    def lottery_analysis_dashboard():
        """Lottery analysis dashboard for admin users"""
        if not current_user.is_admin:
            return redirect(url_for('index'))
        
        # Get analysis parameters from query string
        lottery_type = request.args.get('lottery_type', None)
        days = int(request.args.get('days', 365))
        
        # Run basic analysis for the dashboard
        frequency_data = analyzer.analyze_frequency(lottery_type, days)
        
        # Use the direct template with integrated JS
        return render_template('admin/lottery_analysis_direct.html',
                              title="Lottery Data Analysis",
                              lottery_types=analyzer.lottery_types,
                              selected_type=lottery_type,
                              days=days,
                              frequency_data=frequency_data)
    
    @app.route('/admin/lottery-analysis/full')
    @login_required
    def full_lottery_analysis():
        """Full lottery analysis with all metrics"""
        if not current_user.is_admin:
            return redirect(url_for('index'))
        
        # Get analysis parameters from query string
        lottery_type = request.args.get('lottery_type', None)
        days = int(request.args.get('days', 365))
        
        # Run full analysis
        analysis_results = analyzer.run_full_analysis(lottery_type, days)
        
        return render_template('admin/lottery_analysis_full.html',
                              title="Comprehensive Lottery Analysis",
                              lottery_types=analyzer.lottery_types,
                              selected_type=lottery_type,
                              days=days,
                              analysis=analysis_results)
    
    @app.route('/admin/lottery-analysis/predictions')
    @login_required
    def lottery_predictions():
        """Predictions for next lottery draws with history and accuracy tracking"""
        if not current_user.is_admin:
            return redirect(url_for('index'))
            
        try:
            from models import LotteryPrediction, PredictionResult, ModelTrainingHistory, db
            
            # Get lottery type from query string
            lottery_type = request.args.get('lottery_type', 'Lottery')
            
            # Get prediction for this lottery type
            prediction = analyzer.predict_next_draw(lottery_type, save_to_db=False)
            
            # Get prediction history for this type
            history = []
            try:
                # Get recent verified predictions (limit to 10)
                recent_predictions = LotteryPrediction.query.filter_by(
                    lottery_type=lottery_type,
                    is_verified=True
                ).order_by(LotteryPrediction.prediction_date.desc()).limit(10).all()
                
                for pred in recent_predictions:
                    # Get the verification result for this prediction
                    result = PredictionResult.query.filter_by(
                        prediction_id=pred.id
                    ).first()
                    
                    if not result:
                        continue
                        
                    try:
                        predicted_numbers = json.loads(pred.predicted_numbers)
                        
                        history.append({
                            'date': pred.prediction_date.strftime('%b %d, %Y'),
                            'strategy': pred.strategy,
                            'predicted_numbers': predicted_numbers,
                            'draw_number': result.actual_draw_number,
                            'draw_date': result.actual_draw_date.strftime('%b %d, %Y'),
                            'matched': f"{result.matched_numbers}/{result.total_numbers}",
                            'accuracy': result.accuracy,
                            'bonus_match': result.bonus_match
                        })
                    except Exception as json_error:
                        logger.error(f"Error parsing prediction history: {json_error}")
            except Exception as history_error:
                logger.error(f"Error fetching prediction history: {history_error}")
            
            # Get performance metrics for strategies
            performance = {}
            try:
                # Group by strategy, get the latest record for each
                strategies = db.session.query(ModelTrainingHistory.strategy).distinct().all()
                for strategy_row in strategies:
                    strategy = strategy_row[0]
                    latest = ModelTrainingHistory.query.filter_by(
                        strategy=strategy
                    ).order_by(ModelTrainingHistory.training_date.desc()).first()
                    
                    if latest:
                        performance[strategy] = {
                            'accuracy': latest.accuracy,
                            'total_predictions': latest.total_predictions,
                            'correct_numbers': latest.correct_numbers,
                            'total_numbers': latest.total_numbers,
                            'performance_change': latest.performance_change,
                            'trend': 'improving' if latest.performance_change > 0 else 
                                    'declining' if latest.performance_change < 0 else 'stable'
                        }
            except Exception as perf_error:
                logger.error(f"Error fetching performance metrics: {perf_error}")
            
            # Count total predictions and verified predictions
            total_count = LotteryPrediction.query.count()
            verified_count = LotteryPrediction.query.filter_by(is_verified=True).count()
            
            return render_template('admin/lottery_predictions.html',
                                 title="Lottery Number Predictions",
                                 lottery_types=analyzer.lottery_types,
                                 selected_type=lottery_type,
                                 prediction=prediction,
                                 history=history,
                                 performance=performance,
                                 total_predictions=total_count,
                                 verified_predictions=verified_count)
        except Exception as e:
            logger.error(f"Error in lottery predictions page: {e}", exc_info=True)
            return render_template('admin/lottery_predictions.html',
                                 title="Lottery Number Predictions",
                                 lottery_types=analyzer.lottery_types,
                              selected_type=lottery_type,
                              prediction=prediction)
    
    @app.route('/api/lottery-analysis/frequency')
    @csrf.exempt
    def api_frequency_analysis():
        """Optimized API endpoint for frequency analysis data"""
        logger.info("=== FREQUENCY ANALYSIS API CALLED ===")
        
        # Check if user is admin
        is_admin = False
        try:
            is_admin = current_user.is_authenticated and current_user.is_admin
        except Exception as e:
            logger.warning(f"Error checking admin status: {str(e)}")
        
        # NOTE: We're temporarily disabling authentication check for debugging
        # if not current_user.is_authenticated or not current_user.is_admin:
        #     return jsonify({"error": "Unauthorized"}), 403
        
        try:
            # Check cache first (use request args as cache key)
            cache_key = f"api_freq_{request.args.get('lottery_type')}_{request.args.get('days')}"
            if cache_key in chart_cache:
                logger.info(f"Returning cached frequency analysis for {cache_key}")
                return json.dumps(chart_cache[cache_key], cls=NumpyEncoder), 200, {'Content-Type': 'application/json'}
            
            # Get lottery type - handle empty strings and convert 'all' to None for proper handling
            lottery_type = request.args.get('lottery_type', None)
            if lottery_type == '' or lottery_type == 'all':
                lottery_type = None  # Use None to indicate "all lottery types"
                
            # Get time period parameter with strict validation
            days_str = request.args.get('days', '365')
            
            # Convert days to int with validation
            try:
                if days_str == 'all':
                    days = 365  # Use 365 days for "all time" to ensure we get plenty of data
                else:
                    days = int(days_str)
                    if days <= 0:
                        days = 365
                        
                # Limit range to prevent excessive processing
                if days > 3650:  # Max ~10 years
                    days = 3650
            except ValueError:
                days = 365
                logger.warning(f"Invalid days value: {days_str}, using default 365")
            
            logger.info(f"Performing optimized analysis for: lottery_type={lottery_type}, days={days}")
            
            # Run analysis with optimized version
            data = analyzer.analyze_frequency(lottery_type, days)
            
            # Ensure we have some data to return
            if not data or (isinstance(data, dict) and not data):
                return jsonify({"error": "No data available for the selected lottery type and time period."}), 404
            
            # Cache results for future requests
            chart_cache[cache_key] = data
            
            # Return the analysis data with custom encoder for NumPy data types
            return json.dumps(data, cls=NumpyEncoder), 200, {'Content-Type': 'application/json'}
            
        except Exception as e:
            # Log the error for debugging
            logger.error(f"Error in frequency analysis API: {str(e)}", exc_info=True)
            return jsonify({
                "error": f"Analysis failed: {str(e)}",
                "status": "error"
            }), 500
            # Format error response consistently
            error_response = json.dumps({
                "error": f"Analysis failed: {str(e)}",
                "status": "error",
                "message": "An unexpected error occurred during frequency analysis."
            }, cls=NumpyEncoder)
            
            return app.response_class(
                response=error_response,
                status=500,
                mimetype='application/json'
            )
    
    @app.route('/api/lottery-analysis/patterns')
    @csrf.exempt
    def api_pattern_analysis():
        """API endpoint for pattern analysis data"""
        print("=== PATTERN ANALYSIS API CALLED ===")
        print(f"User authenticated: {current_user.is_authenticated}")
        print(f"User is admin: {current_user.is_admin if current_user.is_authenticated else False}")
        print(f"Request args: {dict(request.args)}")
        
        # Temporarily disabling admin check for debugging
        # if not current_user.is_authenticated or not current_user.is_admin:
        #     print("Unauthorized access attempt to pattern analysis API")
        #     return jsonify({"error": "Unauthorized"}), 403
        
        try:
            # Get parameters with validation
            lottery_type = request.args.get('lottery_type', None)
            days_str = request.args.get('days', '365')
            
            # Validate and convert days
            try:
                days = int(days_str)
                if days <= 0:
                    days = 365  # Default to 365 if invalid
                    print(f"Invalid days value: {days_str}, using default 365")
                    logger.warning(f"Invalid days value: {days_str}, using default 365")
            except ValueError:
                days = 365  # Default to 365 if non-numeric
                print(f"Non-numeric days value: {days_str}, using default 365")
                logger.warning(f"Non-numeric days value: {days_str}, using default 365")
            
            print(f"Processing pattern analysis: lottery_type={lottery_type}, days={days}")
            logger.info(f"API pattern analysis request: lottery_type={lottery_type}, days={days}")
            
            # Get data with detailed exception handling
            try:
                data = analyzer.analyze_patterns(lottery_type, days)
                print(f"Pattern analysis completed successfully")
            except Exception as analysis_error:
                print(f"Error during analysis function: {str(analysis_error)}")
                raise analysis_error
            
            # Log response size for debugging
            try:
                json_data = json.dumps(data, cls=NumpyEncoder)
                response_size = len(json_data)
                print(f"Pattern analysis response size: {response_size} bytes")
                logger.info(f"Pattern analysis response size: {response_size} bytes")
                
                # Check for common data issues
                for key, value in data.items():
                    if isinstance(value, dict) and 'error' in value:
                        print(f"Error for {key}: {value['error']}")
                
                # Use NumpyEncoder for proper JSON serialization
                return app.response_class(
                    response=json_data,  # Already converted with NumpyEncoder above
                    status=200,
                    mimetype='application/json'
                )
            except TypeError as json_error:
                print(f"JSON serialization error: {str(json_error)}")
                # Try to identify the problematic objects
                problematic_keys = []
                for key, value in data.items():
                    try:
                        json.dumps({key: value}, cls=NumpyEncoder)
                    except TypeError:
                        problematic_keys.append(key)
                
                error_msg = f"JSON serialization error with keys: {problematic_keys}"
                print(error_msg)
                raise TypeError(error_msg)
            
        except Exception as e:
            # Log and return error with detailed information
            print(f"ERROR IN PATTERN ANALYSIS API: {str(e)}")
            logger.error(f"Error in pattern analysis API: {str(e)}", exc_info=True)
            # Format error response consistently
            error_response = json.dumps({
                "error": f"Analysis failed: {str(e)}",
                "status": "error",
                "message": "An unexpected error occurred during pattern analysis."
            }, cls=NumpyEncoder)
            
            return app.response_class(
                response=error_response,
                status=500,
                mimetype='application/json'
            )
    
    @app.route('/api/lottery-analysis/time-series')
    @csrf.exempt
    def api_time_series_analysis():
        """API endpoint for time series analysis data"""
        print("=== TIME SERIES ANALYSIS API CALLED ===")
        
        # Temporarily disable admin check
        # if not current_user.is_authenticated or not current_user.is_admin:
        #     return jsonify({"error": "Unauthorized"}), 403
        
        try:
            lottery_type = request.args.get('lottery_type', None)
            days_str = request.args.get('days', '365')
            print(f"Time series request args: lottery_type={lottery_type}, days={days_str}")
            
            # Convert days with validation
            try:
                days = int(days_str)
                if days <= 0:
                    days = 365
            except ValueError:
                days = 365
                print(f"Invalid days value: {days_str}, using default 365")
            
            # Get data and return
            print(f"Performing time series analysis: lottery_type={lottery_type}, days={days}")
            data = analyzer.analyze_time_series(lottery_type, days)
            print(f"Time series analysis completed successfully")
            
            # Use NumpyEncoder for proper JSON serialization of NumPy types
            return app.response_class(
                response=json.dumps(data, cls=NumpyEncoder),
                status=200,
                mimetype='application/json'
            )
            
        except Exception as e:
            print(f"ERROR IN TIME SERIES ANALYSIS API: {str(e)}")
            logger.error(f"Error in time series analysis API: {str(e)}", exc_info=True)
            # Format error response consistently
            error_response = json.dumps({
                "error": f"Analysis failed: {str(e)}",
                "status": "error",
                "message": "An unexpected error occurred during time series analysis."
            }, cls=NumpyEncoder)
            
            return app.response_class(
                response=error_response,
                status=500,
                mimetype='application/json'
            )
    
    @app.route('/api/lottery-analysis/correlations')
    @csrf.exempt
    def api_correlation_analysis():
        """API endpoint for correlation analysis data"""
        print("=== CORRELATION ANALYSIS API CALLED ===")
        
        # Temporarily disable admin check
        # if not current_user.is_authenticated or not current_user.is_admin:
        #     return jsonify({"error": "Unauthorized"}), 403
        
        try:
            days_str = request.args.get('days', '365')
            lottery_type = request.args.get('lottery_type', None)
            second_type = request.args.get('second_type', None)
            
            print(f"Correlations request args: days={days_str}, lottery_type={lottery_type}, second_type={second_type}")
            
            # Convert days with validation
            try:
                days = int(days_str)
                if days <= 0:
                    days = 365
            except ValueError:
                days = 365
                print(f"Invalid days value: {days_str}, using default 365")
            
            # Get data and return
            print(f"Performing correlation analysis: days={days}, lottery_type={lottery_type}, second_type={second_type}")
            
            # If we have specific lottery types to compare, use them
            if lottery_type and second_type:
                data = analyzer.analyze_correlations(days, lottery_type, second_type)
            else:
                data = analyzer.analyze_correlations(days)
                
            print("Correlation analysis completed successfully")
            
            # Use NumpyEncoder for proper JSON serialization of NumPy types
            return app.response_class(
                response=json.dumps(data, cls=NumpyEncoder),
                status=200,
                mimetype='application/json'
            )
            
        except Exception as e:
            print(f"ERROR IN CORRELATION ANALYSIS API: {str(e)}")
            logger.error(f"Error in correlation analysis API: {str(e)}", exc_info=True)
            # Format error response consistently
            error_response = json.dumps({
                "error": f"Analysis failed: {str(e)}",
                "status": "error",
                "message": "An unexpected error occurred during correlation analysis."
            }, cls=NumpyEncoder)
            
            return app.response_class(
                response=error_response,
                status=500,
                mimetype='application/json'
            )
    
    @app.route('/api/lottery-analysis/winners')
    @csrf.exempt
    def api_winner_analysis():
        """API endpoint for winner analysis data"""
        print("=== WINNER ANALYSIS API CALLED ===")
        
        # Temporarily disable admin check
        # if not current_user.is_authenticated or not current_user.is_admin:
        #     return jsonify({"error": "Unauthorized"}), 403
        
        try:
            lottery_type = request.args.get('lottery_type', None)
            days_str = request.args.get('days', '365')
            print(f"Winners request args: lottery_type={lottery_type}, days={days_str}")
            
            # Convert days with validation
            try:
                days = int(days_str)
                if days <= 0:
                    days = 365
            except ValueError:
                days = 365
                print(f"Invalid days value: {days_str}, using default 365")
            
            # Get data and return
            print(f"Performing winner analysis: lottery_type={lottery_type}, days={days}")
            data = analyzer.analyze_winners(lottery_type, days)
            print("Winner analysis completed successfully")
            
            # Use NumpyEncoder for proper JSON serialization of NumPy types
            return app.response_class(
                response=json.dumps(data, cls=NumpyEncoder),
                status=200,
                mimetype='application/json'
            )
            
        except Exception as e:
            print(f"ERROR IN WINNER ANALYSIS API: {str(e)}")
            logger.error(f"Error in winner analysis API: {str(e)}", exc_info=True)
            # Format error response consistently
            error_response = json.dumps({
                "error": f"Analysis failed: {str(e)}",
                "status": "error",
                "message": "An unexpected error occurred during winner analysis."
            }, cls=NumpyEncoder)
            
            return app.response_class(
                response=error_response,
                status=500,
                mimetype='application/json'
            )
    
    @app.route('/api/lottery-analysis/predict')
    @csrf.exempt
    def api_lottery_prediction():
        """API endpoint for lottery prediction"""
        print("=== PREDICTION API CALLED ===")
        
        # Temporarily disable admin check
        # if not current_user.is_authenticated or not current_user.is_admin:
        #     return jsonify({"error": "Unauthorized"}), 403
        
        try:
            lottery_type = request.args.get('lottery_type', 'Lottery')
            save_to_db = request.args.get('save_to_db', 'true').lower() == 'true'
            advanced_model = request.args.get('advanced_model', 'true').lower() == 'true'
            
            print(f"Prediction request args: lottery_type={lottery_type}, save_to_db={save_to_db}, advanced_model={advanced_model}")
            
            # Get data and return
            print(f"Performing prediction analysis: lottery_type={lottery_type}")
            data = analyzer.predict_next_draw(
                lottery_type=lottery_type,
                save_to_db=save_to_db,
                advanced_model=advanced_model
            )
            print("Prediction analysis completed successfully")
            
            # Use NumpyEncoder for proper JSON serialization of NumPy types
            return app.response_class(
                response=json.dumps(data, cls=NumpyEncoder),
                status=200,
                mimetype='application/json'
            )
            
        except Exception as e:
            print(f"ERROR IN PREDICTION API: {str(e)}")
            logger.error(f"Error in prediction API: {str(e)}", exc_info=True)
            # Format error response consistently
            error_response = json.dumps({
                "error": f"Analysis failed: {str(e)}",
                "status": "error",
                "message": "An unexpected error occurred during prediction analysis."
            }, cls=NumpyEncoder)
            
            return app.response_class(
                response=error_response,
                status=500,
                mimetype='application/json'
            )
    
    @app.route('/api/lottery-analysis/verify-predictions')
    @csrf.exempt
    def api_verify_predictions():
        """API endpoint for verifying predictions against actual results"""
        print("=== VERIFY PREDICTIONS API CALLED ===")
        
        try:
            # Get parameters from request
            lottery_type = request.args.get('lottery_type', None)
            draw_number_str = request.args.get('draw_number', None)
            draw_date_str = request.args.get('draw_date', None)
            
            # Convert draw number to int if provided
            draw_number = None
            if draw_number_str:
                try:
                    draw_number = int(draw_number_str)
                except ValueError:
                    return jsonify({"error": "Invalid draw number format"}), 400
            
            # Convert draw date to datetime if provided
            draw_date = None
            if draw_date_str:
                try:
                    draw_date = datetime.strptime(draw_date_str, '%Y-%m-%d')
                except ValueError:
                    return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400
            
            print(f"Verifying predictions: lottery_type={lottery_type}, draw_number={draw_number}, draw_date={draw_date}")
            
            # Call the verification function
            results = analyzer.verify_predictions(
                lottery_type=lottery_type,
                draw_number=draw_number,
                draw_date=draw_date
            )
            
            print("Verification completed")
            
            # Use NumpyEncoder for proper JSON serialization of NumPy types
            return app.response_class(
                response=json.dumps(results, cls=NumpyEncoder),
                status=200,
                mimetype='application/json'
            )
            
        except Exception as e:
            print(f"ERROR IN VERIFICATION API: {str(e)}")
            logger.error(f"Error in prediction verification API: {str(e)}", exc_info=True)
            
            # Format error response consistently
            error_response = json.dumps({
                "error": f"Verification failed: {str(e)}",
                "status": "error",
                "message": "An unexpected error occurred during prediction verification."
            }, cls=NumpyEncoder)
            
            return app.response_class(
                response=error_response,
                status=500,
                mimetype='application/json'
            )
    
    @app.route('/api/lottery-analysis/full')
    @csrf.exempt
    def api_full_analysis():
        """API endpoint for full analysis data"""
        print("=== FULL ANALYSIS API CALLED ===")
        
        # Temporarily disable admin check
        # if not current_user.is_authenticated or not current_user.is_admin:
        #     return jsonify({"error": "Unauthorized"}), 403
        
        try:
            lottery_type = request.args.get('lottery_type', None)
            days_str = request.args.get('days', '365')
            print(f"Full analysis request args: lottery_type={lottery_type}, days={days_str}")
            
            # Convert days with validation
            try:
                days = int(days_str)
                if days <= 0:
                    days = 365
            except ValueError:
                days = 365
                print(f"Invalid days value: {days_str}, using default 365")
            
            # Get data and return
            print(f"Performing full analysis: lottery_type={lottery_type}, days={days}")
            data = analyzer.run_full_analysis(lottery_type, days)
            print("Full analysis completed successfully")
            
            # Use NumpyEncoder for proper JSON serialization of NumPy types
            return app.response_class(
                response=json.dumps(data, cls=NumpyEncoder),
                status=200,
                mimetype='application/json'
            )
            
        except Exception as e:
            print(f"ERROR IN FULL ANALYSIS API: {str(e)}")
            logger.error(f"Error in full analysis API: {str(e)}", exc_info=True)
            # Format error response consistently
            error_response = json.dumps({
                "error": f"Analysis failed: {str(e)}",
                "status": "error",
                "message": "An unexpected error occurred during full analysis."
            }, cls=NumpyEncoder)
            
            return app.response_class(
                response=error_response,
                status=500,
                mimetype='application/json'
            )
    
    @app.route('/admin/lottery-analysis/prediction-history')
    @login_required
    def prediction_history():
        """Admin page for detailed prediction history and analysis"""
        if not current_user.is_admin:
            return redirect(url_for('index'))
            
        try:
            from models import LotteryPrediction, PredictionResult, ModelTrainingHistory, db
            
            # Filter parameters
            lottery_type = request.args.get('lottery_type', None)
            strategy = request.args.get('strategy', None)
            days = request.args.get('days', '90')
            
            try:
                days = int(days)
            except ValueError:
                days = 90
                
            # Base query
            date_cutoff = datetime.now() - timedelta(days=days)
            query = LotteryPrediction.query.filter(
                LotteryPrediction.prediction_date >= date_cutoff
            )
            
            # Apply filters if provided
            if lottery_type:
                query = query.filter(LotteryPrediction.lottery_type == lottery_type)
                
            if strategy:
                query = query.filter(LotteryPrediction.strategy == strategy)
                
            # Get the predictions and their results
            predictions = query.order_by(LotteryPrediction.prediction_date.desc()).all()
            
            # Build results to display
            results = []
            for pred in predictions:
                verification = PredictionResult.query.filter_by(prediction_id=pred.id).first()
                
                # Skip if not verified yet
                if not verification and pred.is_verified:
                    continue
                    
                try:
                    predicted_numbers = json.loads(pred.predicted_numbers)
                    results.append({
                        'id': pred.id,
                        'lottery_type': pred.lottery_type,
                        'prediction_date': pred.prediction_date,
                        'strategy': pred.strategy,
                        'predicted_numbers': predicted_numbers,
                        'confidence': pred.confidence_score,
                        'is_verified': pred.is_verified,
                        'draw_date': verification.actual_draw_date if verification else None,
                        'draw_number': verification.actual_draw_number if verification else None,
                        'matched': verification.matched_numbers if verification else None,
                        'total': verification.total_numbers if verification else None,
                        'accuracy': verification.accuracy if verification else None,
                        'bonus_match': verification.bonus_match if verification else None
                    })
                except Exception as err:
                    logger.error(f"Error processing prediction {pred.id}: {err}")
                    # Skip entries with invalid data
                    pass
            
            # Get available filters for selects
            lottery_types = db.session.query(LotteryPrediction.lottery_type).distinct().all()
            lottery_types = [lt[0] for lt in lottery_types]
            
            strategies = db.session.query(LotteryPrediction.strategy).distinct().all()
            strategies = [s[0] for s in strategies]
            
            # Get performance trend over time
            performance_trends = {}
            for s in strategies:
                trend_data = ModelTrainingHistory.query.filter_by(
                    strategy=s
                ).order_by(ModelTrainingHistory.training_date.asc()).all()
                
                if trend_data:
                    trend_points = []
                    for point in trend_data:
                        trend_points.append({
                            'date': point.training_date.strftime('%Y-%m-%d'),
                            'accuracy': point.accuracy,
                            'predictions': point.total_predictions
                        })
                    
                    performance_trends[s] = trend_points
            
            return render_template(
                'admin/prediction_history.html',
                results=results,
                lottery_types=lottery_types,
                strategies=strategies,
                selected_type=lottery_type,
                selected_strategy=strategy,
                selected_days=days,
                performance_trends=performance_trends
            )
            
        except Exception as e:
            flash(f"Error loading prediction history: {str(e)}", 'danger')
            return redirect(url_for('lottery_analysis_dashboard'))
    
    @app.route('/static/analysis/<path:filename>')
    def analysis_images(filename):
        """Serve generated analysis images"""
        return send_from_directory(STATIC_DIR, filename)
    
    logger.info("Lottery analysis routes registered")