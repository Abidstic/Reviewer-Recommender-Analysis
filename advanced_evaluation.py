import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, Any
from models import Manager

class AdvancedEvaluation:
    """
    Comprehensive evaluation system for reviewer recommendation algorithms.
    Provides detailed metrics suitable for thesis-level analysis.
    """
    
    def __init__(self, manager: Manager):
        self.manager = manager
        self.ground_truth = self._build_ground_truth()
        
    def _build_ground_truth(self) -> Dict[int, set]:
        """Build ground truth from actual reviews"""
        ground_truth = {}
        for pr in self.manager.pull_requests_list:
            reviewers = [
                review.reviewer_username
                for review in self.manager.reviews_list
                if review.pull_number == pr.number
            ]
            if reviewers:
                ground_truth[pr.number] = set(reviewers)
        return ground_truth
    
    def evaluate_algorithms(self, algorithm_results: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Evaluate multiple algorithms and return comprehensive metrics
        
        Args:
            algorithm_results: Dict with algorithm_name -> {pr_number: {dev: score}}
            
        Returns:
            Dict with detailed evaluation metrics for each algorithm
        """
        print(f"\n{'='*70}")
        print("ADVANCED EVALUATION RESULTS")
        print(f"{'='*70}")
        
        if not algorithm_results:
            print("No algorithm results to evaluate.")
            return {}
        
        print(f"Ground truth: {len(self.ground_truth)} PRs with reviews")
        
        if not self.ground_truth:
            print("No ground truth available for evaluation.")
            return {}
        
        # Calculate metrics for each algorithm
        detailed_metrics = {}
        
        print(f"\n{'='*50}")
        print("ALGORITHM PERFORMANCE ANALYSIS")
        print(f"{'='*50}")
        
        for algo_name, algo_result in algorithm_results.items():
            print(f"\n--- {algo_name} Analysis ---")
            
            if not algo_result:
                print(f"  No results from {algo_name}")
                continue
            
            # Calculate comprehensive metrics
            metrics = self._calculate_algorithm_metrics(algo_name, algo_result)
            detailed_metrics[algo_name] = metrics
            
            # Display individual algorithm analysis
            self._display_algorithm_analysis(algo_name, metrics, algo_result)
        
        # Display comparative analysis
        if len(detailed_metrics) > 1:
            self._display_comparative_analysis(detailed_metrics)
        
        # Save results
        self._save_evaluation_results(detailed_metrics)
        
        return detailed_metrics
    
    def _calculate_algorithm_metrics(self, algo_name: str, algo_result: Dict) -> Dict[str, Any]:
        """Calculate comprehensive metrics for a single algorithm"""
        
        # Basic statistics
        total_prs_analyzed = len(algo_result)
        developers_recommended = len(set(dev for scores in algo_result.values() for dev in scores.keys()))
        
        # Score distribution
        all_scores = [score for scores in algo_result.values() for score in scores.values()]
        score_stats = {}
        if all_scores:
            score_stats = {
                'mean': np.mean(all_scores),
                'median': np.median(all_scores),
                'std': np.std(all_scores),
                'min': np.min(all_scores),
                'max': np.max(all_scores),
                'range': np.max(all_scores) - np.min(all_scores)
            }
        
        # Evaluation metrics calculation
        hits_at_k = {1: 0, 3: 0, 5: 0, 10: 0}
        reciprocal_ranks = []
        average_precisions = []
        dcg_scores = []
        valid_prs = 0
        
        for pr_num, actual_reviewers in self.ground_truth.items():
            if pr_num in algo_result:
                # Get ranked recommendations
                sorted_recs = sorted(algo_result[pr_num].items(), key=lambda x: x[1], reverse=True)
                
                if not sorted_recs:
                    continue
                
                # Calculate hits at different K values
                for k in hits_at_k.keys():
                    top_k = [rec[0] for rec in sorted_recs[:k]]
                    if any(reviewer in actual_reviewers for reviewer in top_k):
                        hits_at_k[k] += 1
                
                # Calculate reciprocal rank (MRR)
                for rank, (rec_reviewer, _) in enumerate(sorted_recs, 1):
                    if rec_reviewer in actual_reviewers:
                        reciprocal_ranks.append(1.0 / rank)
                        break
                else:
                    reciprocal_ranks.append(0.0)
                
                # Calculate Average Precision (for MAP)
                relevant_ranks = []
                for rank, (rec_reviewer, _) in enumerate(sorted_recs, 1):
                    if rec_reviewer in actual_reviewers:
                        relevant_ranks.append(rank)
                
                if relevant_ranks:
                    precisions = []
                    for i, rank in enumerate(relevant_ranks):
                        precision_at_rank = (i + 1) / rank
                        precisions.append(precision_at_rank)
                    average_precisions.append(np.mean(precisions))
                else:
                    average_precisions.append(0.0)
                
                # Calculate DCG (Discounted Cumulative Gain)
                dcg = 0.0
                for rank, (rec_reviewer, score) in enumerate(sorted_recs[:10], 1):
                    relevance = 1.0 if rec_reviewer in actual_reviewers else 0.0
                    dcg += relevance / np.log2(rank + 1)
                dcg_scores.append(dcg)
                
                valid_prs += 1
        
        # Compile final metrics
        metrics = {
            'basic_stats': {
                'total_prs_analyzed': total_prs_analyzed,
                'developers_recommended': developers_recommended,
                'valid_prs': valid_prs,
                'coverage': valid_prs / len(self.ground_truth) if self.ground_truth else 0
            },
            'score_distribution': score_stats,
            'precision_metrics': {},
            'ranking_metrics': {},
            'other_metrics': {}
        }
        
        if valid_prs > 0:
            # Precision metrics
            for k in hits_at_k.keys():
                metrics['precision_metrics'][f'precision_at_{k}'] = hits_at_k[k] / valid_prs
                metrics['precision_metrics'][f'hit_rate_at_{k}'] = hits_at_k[k] / valid_prs
            
            # Ranking metrics
            metrics['ranking_metrics']['mrr'] = np.mean(reciprocal_ranks)
            metrics['ranking_metrics']['map'] = np.mean(average_precisions)
            metrics['ranking_metrics']['avg_dcg'] = np.mean(dcg_scores)
            
            # Additional metrics
            metrics['other_metrics']['successful_recommendations'] = sum(1 for rr in reciprocal_ranks if rr > 0)
            metrics['other_metrics']['recommendation_success_rate'] = metrics['other_metrics']['successful_recommendations'] / valid_prs
        
        return metrics
    
    def _display_algorithm_analysis(self, algo_name: str, metrics: Dict, algo_result: Dict):
        """Display detailed analysis for a single algorithm"""
        
        basic = metrics['basic_stats']
        precision = metrics['precision_metrics']
        ranking = metrics['ranking_metrics']
        other = metrics['other_metrics']
        scores = metrics['score_distribution']
        
        print(f"  Total PRs analyzed: {basic['total_prs_analyzed']}")
        print(f"  Unique developers recommended: {basic['developers_recommended']}")
        print(f"  Valid PRs for evaluation: {basic['valid_prs']}")
        print(f"  Coverage: {basic['coverage']:.4f}")
        
        if scores:
            print(f"  Score statistics:")
            print(f"    Mean: {scores['mean']:.4f}")
            print(f"    Median: {scores['median']:.4f}")
            print(f"    Std Dev: {scores['std']:.4f}")
            print(f"    Range: [{scores['min']:.4f}, {scores['max']:.4f}]")
        
        if precision:
            print(f"  Precision metrics:")
            for k in [1, 3, 5, 10]:
                if f'precision_at_{k}' in precision:
                    print(f"    Precision@{k}: {precision[f'precision_at_{k}']:.4f}")
        
        if ranking:
            print(f"  Ranking metrics:")
            if 'mrr' in ranking:
                print(f"    MRR: {ranking['mrr']:.4f}")
            if 'map' in ranking:
                print(f"    MAP: {ranking['map']:.4f}")
            if 'avg_dcg' in ranking:
                print(f"    Avg DCG@10: {ranking['avg_dcg']:.4f}")
        
        if other:
            print(f"  Success metrics:")
            if 'recommendation_success_rate' in other:
                print(f"    Success Rate: {other['recommendation_success_rate']:.4f}")
    
    def _display_comparative_analysis(self, detailed_metrics: Dict):
        """Display comprehensive comparison between algorithms"""
        
        print(f"\n{'='*60}")
        print("DETAILED COMPARISON TABLE")
        print(f"{'='*60}")
        
        # Create comprehensive comparison table
        algorithms = list(detailed_metrics.keys())
        
        # Header
        header = f"{'Algorithm':<12}{'P@1':<8}{'P@3':<8}{'P@5':<8}{'P@10':<8}{'MRR':<8}{'MAP':<8}{'DCG@10':<8}{'Coverage':<10}"
        print(header)
        print("-" * len(header))
        
        # Data rows
        for algo_name in algorithms:
            metrics = detailed_metrics[algo_name]
            precision = metrics['precision_metrics']
            ranking = metrics['ranking_metrics']
            basic = metrics['basic_stats']
            
            row = f"{algo_name:<12}"
            row += f"{precision.get('precision_at_1', 0):<8.4f}"
            row += f"{precision.get('precision_at_3', 0):<8.4f}"
            row += f"{precision.get('precision_at_5', 0):<8.4f}"
            row += f"{precision.get('precision_at_10', 0):<8.4f}"
            row += f"{ranking.get('mrr', 0):<8.4f}"
            row += f"{ranking.get('map', 0):<8.4f}"
            row += f"{ranking.get('avg_dcg', 0):<8.4f}"
            row += f"{basic.get('coverage', 0):<10.4f}"
            print(row)
        
        # Algorithm rankings by different metrics
        print(f"\n{'='*40}")
        print("ALGORITHM RANKINGS")
        print(f"{'='*40}")
        
        ranking_metrics = [
            ('MRR', 'ranking_metrics', 'mrr'),
            ('MAP', 'ranking_metrics', 'map'),
            ('Precision@5', 'precision_metrics', 'precision_at_5'),
            ('DCG@10', 'ranking_metrics', 'avg_dcg')
        ]
        
        for metric_name, category, key in ranking_metrics:
            print(f"\nRanking by {metric_name}:")
            ranked = sorted(
                detailed_metrics.items(), 
                key=lambda x: x[1][category].get(key, 0), 
                reverse=True
            )
            for rank, (algo_name, metrics) in enumerate(ranked, 1):
                value = metrics[category].get(key, 0)
                print(f"  {rank}. {algo_name}: {value:.4f}")
        
        # Performance insights
        print(f"\n{'='*40}")
        print("PERFORMANCE INSIGHTS")
        print(f"{'='*40}")
        
        # Best performers
        best_mrr = max(detailed_metrics.items(), key=lambda x: x[1]['ranking_metrics'].get('mrr', 0))
        best_map = max(detailed_metrics.items(), key=lambda x: x[1]['ranking_metrics'].get('map', 0))
        best_p5 = max(detailed_metrics.items(), key=lambda x: x[1]['precision_metrics'].get('precision_at_5', 0))
        
        print(f"Best MRR: {best_mrr[0]} ({best_mrr[1]['ranking_metrics'].get('mrr', 0):.4f})")
        print(f"Best MAP: {best_map[0]} ({best_map[1]['ranking_metrics'].get('map', 0):.4f})")
        print(f"Best Precision@5: {best_p5[0]} ({best_p5[1]['precision_metrics'].get('precision_at_5', 0):.4f})")
        
        # Performance spread analysis
        mrr_scores = [metrics['ranking_metrics'].get('mrr', 0) for metrics in detailed_metrics.values()]
        if len(mrr_scores) > 1:
            mrr_range = max(mrr_scores) - min(mrr_scores)
            max_mrr = max(mrr_scores)
            if max_mrr > 0:
                print(f"MRR Performance Range: {mrr_range:.4f}")
                print(f"Relative Performance Difference: {(mrr_range/max_mrr*100):.1f}%")
    
    def _save_evaluation_results(self, detailed_metrics: Dict):
        """Save evaluation results to files for thesis analysis"""
        
        # Create results directory
        results_dir = "evaluation_results"
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = self.manager.project
        
        # Save detailed metrics as JSON
        metrics_file = f"{results_dir}/{project_name}_advanced_metrics_{timestamp}.json"
        with open(metrics_file, 'w') as f:
            # Convert numpy types to regular Python types for JSON serialization
            json_metrics = self._convert_numpy_types(detailed_metrics)
            json.dump(json_metrics, f, indent=2)
        
        # Save summary CSV if pandas is available
        try:
            import pandas as pd
            
            # Flatten metrics for CSV
            csv_data = []
            for algo_name, metrics in detailed_metrics.items():
                row = {'Algorithm': algo_name}
                
                # Add basic stats
                row.update({f"basic_{k}": v for k, v in metrics['basic_stats'].items()})
                
                # Add precision metrics
                row.update({f"precision_{k}": v for k, v in metrics['precision_metrics'].items()})
                
                # Add ranking metrics
                row.update({f"ranking_{k}": v for k, v in metrics['ranking_metrics'].items()})
                
                # Add other metrics
                row.update({f"other_{k}": v for k, v in metrics['other_metrics'].items()})
                
                # Add score distribution stats
                if metrics['score_distribution']:
                    row.update({f"score_{k}": v for k, v in metrics['score_distribution'].items()})
                
                csv_data.append(row)
            
            df = pd.DataFrame(csv_data)
            csv_file = f"{results_dir}/{project_name}_advanced_summary_{timestamp}.csv"
            df.to_csv(csv_file, index=False)
            
            print(f"\nResults saved:")
            print(f"  Detailed JSON: {metrics_file}")
            print(f"  Summary CSV: {csv_file}")
            
        except ImportError:
            print(f"\nResults saved:")
            print(f"  Detailed JSON: {metrics_file}")
            print("  (CSV export requires pandas - install with: pip install pandas)")
        
        return metrics_file
    
    def _convert_numpy_types(self, obj):
        """Convert numpy types to regular Python types for JSON serialization"""
        if isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

# Convenience function for easy usage
def run_advanced_evaluation(manager: Manager, algorithm_results: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Convenience function to run advanced evaluation
    
    Args:
        manager: The data manager
        algorithm_results: Dict with algorithm_name -> {pr_number: {dev: score}}
        
    Returns:
        Dict with detailed evaluation metrics
    """
    evaluator = AdvancedEvaluation(manager)
    return evaluator.evaluate_algorithms(algorithm_results)