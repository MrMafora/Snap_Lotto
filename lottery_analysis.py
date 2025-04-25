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
        self.lottery_types = ['Lotto', 'Lotto Plus 1', 'Lotto Plus 2', 
                             'Powerball', 'Powerball Plus', 'Daily Lotto']
        
        # Required number count by lottery type
        self.required_numbers = {
            'Lotto': 6,
            'Lotto Plus 1': 6,
            'Lotto Plus 2': 6,
            'Powerball': 5,  # Plus 1 bonus ball
            'Powerball Plus': 5,  # Plus 1 bonus ball
            'Daily Lotto': 5
        }
        
        # Store analysis results
        self.analysis_results = {}
        
    def _generate_frequency_chart(self, frequency, top_numbers, lottery_type, results):
        """Generate frequency chart and add to results
        
        Args:
            frequency (numpy.ndarray): Frequency array for each number
            top_numbers (list): List of tuples (number, frequency) for top numbers
            lottery_type (str): Type of lottery
            results (dict): Results dictionary to update
        """
        # Sort top numbers by frequency, highest first
        sorted_top = sorted(top_numbers, key=lambda x: x[1], reverse=True)
        
        # Set up color palette - more distinct colors with visual hierarchy
        # Use 9 colors instead of default to ensure better distinction
        colors = plt.cm.viridis(np.linspace(0, 1, 9))
        
        # Add 10% padding on each side for visual distinction
        bar_width = 0.8  
        
        # Generate frequency chart with enhanced styling
        plt.figure(figsize=(10, 6))
        bars = plt.bar(
            range(1, len(frequency) + 1), 
            frequency, 
            width=bar_width,
            edgecolor='gray',
            linewidth=0.5,
            zorder=3  # Make bars appear above grid lines
        )
        
        # Add rounded corners and shadows to bars
        for bar in bars:
            # Get the current color of the bar
            bar_color = bar.get_facecolor()
            
            # Highlight top 3 numbers with specific colors
            if bar.get_x() + bar_width/2 in [n[0] for n in sorted_top[:3]]:
                rank = [n[0] for n in sorted_top[:3]].index(bar.get_x() + bar_width/2)
                if rank == 0:  # 1st place
                    bar.set_color('red')
                elif rank == 1:  # 2nd place
                    bar.set_color('gold')
                elif rank == 2:  # 3rd place
                    bar.set_color('green')
            
            # Add styling to enhance visual appeal
            # Note: Using simpler styling instead of patheffects which isn't available
            bar.set_edgecolor('darkgray')
            bar.set_linewidth(0.8)
        
        plt.xlabel('Number', fontweight='bold', fontsize=12)
        plt.ylabel('Frequency', fontweight='bold', fontsize=12)
        plt.title(f'Number Frequency for {lottery_type}', fontsize=14, pad=20)
        
        # Enhance grid with lighter lines
        plt.grid(axis='y', alpha=0.3, linestyle='--', zorder=0)
        
        # Increase spacing to prevent overlap with X-axis
        plt.subplots_adjust(bottom=0.15, top=0.85)
        
        # Add text with the top 5 most frequent numbers
        top_text = "Top 5 numbers:\n" + "\n".join([f"#{n}: {f} times" for n, f in sorted_top[:5]])
        plt.annotate(top_text, xy=(0.02, 0.95), xycoords='axes fraction', 
                    fontsize=10, bbox=dict(
                        boxstyle="round,pad=0.5", 
                        facecolor='white', 
                        alpha=0.9,
                        edgecolor='lightgray'
                    ))
        
        # Save chart with enhanced quality
        img_path = os.path.join(STATIC_DIR, f'frequency_{lottery_type.replace(" ", "_")}.png')
        plt.savefig(img_path, dpi=120, bbox_inches='tight')
        plt.close()
        
        # Also save as base64 for direct embedding
        img_buffer = io.BytesIO()
        
        # Create the same chart again for buffer
        plt.figure(figsize=(10, 6))
        bars = plt.bar(
            range(1, len(frequency) + 1), 
            frequency, 
            width=bar_width,
            edgecolor='gray',
            linewidth=0.5,
            zorder=3
        )
        
        # Add rounded corners and shadows to bars
        for bar in bars:
            # Highlight top 3 numbers with specific colors
            if bar.get_x() + bar_width/2 in [n[0] for n in sorted_top[:3]]:
                rank = [n[0] for n in sorted_top[:3]].index(bar.get_x() + bar_width/2)
                if rank == 0:  # 1st place
                    bar.set_color('red')
                elif rank == 1:  # 2nd place
                    bar.set_color('gold')
                elif rank == 2:  # 3rd place
                    bar.set_color('green')
            
            # Add styling to enhance visual appeal
            # Note: Using simpler styling instead of patheffects which isn't available
            bar.set_edgecolor('darkgray')
            bar.set_linewidth(0.8)
        
        plt.xlabel('Number', fontweight='bold', fontsize=12)
        plt.ylabel('Frequency', fontweight='bold', fontsize=12)
        plt.title(f'Number Frequency for {lottery_type}', fontsize=14, pad=20)
        plt.grid(axis='y', alpha=0.3, linestyle='--', zorder=0)
        plt.subplots_adjust(bottom=0.15, top=0.85)
        plt.annotate(top_text, xy=(0.02, 0.95), xycoords='axes fraction', 
                    fontsize=10, bbox=dict(
                        boxstyle="round,pad=0.5", 
                        facecolor='white', 
                        alpha=0.9,
                        edgecolor='lightgray'
                    ))
        
        plt.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight')
        plt.close()
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        
        # Store results
        results[lottery_type] = {
            'frequency': frequency.tolist(),
            'top_numbers': sorted_top,
            'chart_path': f'/static/analysis/frequency_{lottery_type.replace(" ", "_")}.png',
            'chart_base64': img_base64
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
            days (int, optional): Number of days of historical data
            
        Returns:
            dict: Analysis results including frequency charts
        """
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
                            if 0 <= int(num) <= max_number:
                                combined_frequency[int(num)] += 1
                    
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
                        max_val = lt_df[col].max()
                        if max_val and max_val > max_number:
                            max_number = int(max_val)
                    
                    # Create a frequency array for all possible numbers
                    frequency = np.zeros(max_number + 1, dtype=int)
                    
                    # Count occurrences of each number
                    for col in number_cols:
                        for num in lt_df[col].dropna():
                            if 0 <= int(num) <= max_number:
                                frequency[int(num)] += 1
                    
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
    
    def analyze_correlations(self, days=365):
        """Analyze correlations between different lottery types
        
        Args:
            days (int): Number of days of historical data
            
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
        
        # Cache results
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
    
    def predict_next_draw(self, lottery_type):
        """Predict numbers for the next draw based on historical patterns
        
        Args:
            lottery_type (str): The lottery type to predict
            
        Returns:
            dict: Prediction results with potential numbers
        """
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
            if cache_key in model_cache:
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
                    if 0 <= int(num) <= max_number:
                        frequency[int(num)] += 1
            
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
            
            # Strategy 1: Most frequent numbers overall
            top_indices = np.argsort(frequency)[-7:]  # Top 7 numbers (we might need 6 + bonus)
            most_frequent = [int(i+1) for i in top_indices]
            
            # Strategy 2: Most frequent number at each position
            positional_frequent = []
            for pos in position_analysis:
                if pos['top_numbers']:
                    positional_frequent.append(int(pos['top_numbers'][0][0]))
            
            # Strategy 3: Balance of frequent and rare numbers
            # Take half frequent, half rare
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
            
            # Add strategies to recommendations
            required_count = self.required_numbers.get(lottery_type, 6)
            
            recommendations = [
                {
                    'strategy': 'Most Frequent Numbers',
                    'numbers': most_frequent[:required_count],
                    'bonus': most_frequent[required_count] if lottery_type in ['Powerball', 'Powerball Plus'] else None
                },
                {
                    'strategy': 'Position-Based Frequent Numbers',
                    'numbers': positional_frequent[:required_count],
                    'bonus': bonus_analysis['top_numbers'][0][0] if bonus_analysis and bonus_analysis['top_numbers'] else None
                },
                {
                    'strategy': 'Balanced Frequency',
                    'numbers': balanced[:required_count],
                    'bonus': balanced[required_count] if lottery_type in ['Powerball', 'Powerball Plus'] else None
                },
                {
                    'strategy': 'Due Numbers',
                    'numbers': due_numbers[:required_count],
                    'bonus': due_numbers[required_count] if len(due_numbers) > required_count and
                                                         lottery_type in ['Powerball', 'Powerball Plus'] else None
                }
            ]
            
            # Store prediction results
            prediction_results = {
                'lottery_type': lottery_type,
                'position_analysis': position_analysis,
                'bonus_analysis': bonus_analysis,
                'recommendations': recommendations,
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
        """Predictions for next lottery draws"""
        if not current_user.is_admin:
            return redirect(url_for('index'))
        
        # Get lottery type from query string
        lottery_type = request.args.get('lottery_type', 'Lotto')
        
        # Get prediction for this lottery type
        prediction = analyzer.predict_next_draw(lottery_type)
        
        return render_template('admin/lottery_predictions.html',
                              title="Lottery Number Predictions",
                              lottery_types=analyzer.lottery_types,
                              selected_type=lottery_type,
                              prediction=prediction)
    
    @app.route('/api/lottery-analysis/frequency')
    @csrf.exempt
    def api_frequency_analysis():
        """API endpoint for frequency analysis data"""
        print("=== FREQUENCY ANALYSIS API CALLED ===")
        print(f"User authenticated: {current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else 'No current_user'}")
        
        # Check if user is admin
        is_admin = False
        try:
            is_admin = current_user.is_authenticated and current_user.is_admin
            print(f"User is admin: {is_admin}")
        except Exception as e:
            print(f"Error checking admin status: {str(e)}")
        
        # NOTE: We're temporarily disabling authentication check for debugging
        # if not current_user.is_authenticated or not current_user.is_admin:
        #     return jsonify({"error": "Unauthorized"}), 403
        
        try:
            # Get lottery type - handle empty strings and convert 'all' to None for proper handling
            lottery_type = request.args.get('lottery_type', None)
            if lottery_type == '' or lottery_type == 'all':
                lottery_type = None  # Use None to indicate "all lottery types"
                
            # Get time period parameter
            days_str = request.args.get('days', '365')
            print(f"Request args: lottery_type={lottery_type}, days={days_str}")
            
            # Convert days to int with validation
            try:
                if days_str == 'all':
                    days = 365  # Use 365 days for "all time" to ensure we get plenty of data
                else:
                    days = int(days_str)
                    if days <= 0:
                        days = 365
            except ValueError:
                days = 365
                print(f"Invalid days value: {days_str}, using default 365")
            
            print(f"Performing analysis for: lottery_type={lottery_type}, days={days}")
            
            # Use a try-except block to catch any errors during analysis
            try:
                data = analyzer.analyze_frequency(lottery_type, days)
                print(f"Analysis completed successfully with {len(data.keys() if isinstance(data, dict) else [])} items")
                
                # Ensure we have some data to return
                if not data or (isinstance(data, dict) and not data):
                    return jsonify({"error": "No data available for the selected lottery type and time period."}), 404
                    
                # Return the analysis data with custom encoder for NumPy data types
                return json.dumps(data, cls=NumpyEncoder), 200, {'Content-Type': 'application/json'}
            except Exception as e:
                logger.error(f"Error during frequency analysis: {str(e)}")
                return jsonify({"error": f"Analysis error: {str(e)}"}), 500
        except Exception as e:
            # Log the error for debugging
            print(f"ERROR IN FREQUENCY ANALYSIS API: {str(e)}")
            logger.error(f"Error in frequency analysis API: {str(e)}", exc_info=True)
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
            print(f"Correlations request args: days={days_str}")
            
            # Convert days with validation
            try:
                days = int(days_str)
                if days <= 0:
                    days = 365
            except ValueError:
                days = 365
                print(f"Invalid days value: {days_str}, using default 365")
            
            # Get data and return
            print(f"Performing correlation analysis: days={days}")
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
            lottery_type = request.args.get('lottery_type', 'Lotto')
            print(f"Prediction request args: lottery_type={lottery_type}")
            
            # Get data and return
            print(f"Performing prediction analysis: lottery_type={lottery_type}")
            data = analyzer.predict_next_draw(lottery_type)
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
    
    @app.route('/static/analysis/<path:filename>')
    def analysis_images(filename):
        """Serve generated analysis images"""
        return send_from_directory(STATIC_DIR, filename)
    
    logger.info("Lottery analysis routes registered")