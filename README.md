[![DOI](https://zenodo.org/badge/1052296465.svg)](https://doi.org/10.5281/zenodo.20777989)
# GitHub Reviewer Recommender System

An advanced reviewer recommendation system that analyzes GitHub repository data to suggest appropriate code reviewers using multiple machine learning algorithms. This system provides comprehensive evaluation metrics suitable for academic research and thesis work.

## Features

- **Multiple Recommendation Algorithms**: RevFinder, ChRev, TurnoverRec, and Sofia
- **Interactive Interface**: User-friendly menu system for repository and algorithm selection
- **Advanced Evaluation Metrics**: Precision@K, Recall@K, MRR, MAP, DCG, and more
- **Comprehensive Analysis**: Detailed performance comparisons and statistical insights
- **Thesis-Ready Output**: Exportable results in JSON and CSV formats for academic analysis
- **Debug Capabilities**: Built-in debugging tools for data structure validation

## Prerequisites

- Python 3.7 or higher
- pip package manager
- Git

## Installation

### 1. Clone and Setup Data Crawler

First, clone the GitHub crawler repository to fetch repository data:

```bash
git clone https://github.com/Ehsan200/Github-crawler
cd Github-crawler
```

Follow the crawler's documentation to fetch repository data. The crawler will create a `crawled-data` directory with repository information.

### 2. Setup Environment Variable

Set the `DATA_BASE_DIR` environment variable to point to your crawled data:

```bash
export DATA_BASE_DIR=/path/to/Github-crawler/crawled-data
```

For permanent setup, add this to your shell profile:
```bash
echo 'export DATA_BASE_DIR=/path/to/Github-crawler/crawled-data' >> ~/.bashrc
source ~/.bashrc
```

### 3. Clone and Install Reviewer Recommender

```bash
git clone https://github.com/Abidstic/Reviewer-Recommender-Analysis
cd Reviewer-Recommender-Analysis
pip install -r requirements.txt
```

## Usage

The system provides multiple ways to run algorithms and evaluations:

### Interactive Mode (Recommended)

Launch the interactive interface for easy repository and algorithm selection:

```bash
python3 interactive_manager.py
```

The interactive mode provides:
- Automatic repository discovery
- Repository data quality validation
- Single algorithm analysis with detailed metrics
- Comprehensive multi-algorithm evaluation
- Built-in debugging capabilities

### Command Line Mode

For scripted execution, use the traditional command line interface:

#### Run Single Algorithm
```bash
python manager.py --r_owner <owner> --r_name <repo> algo-<algorithm>
```

Available algorithms:
- `algo-revFinder`: File similarity-based recommendations
- `algo-chRev`: Comment and contribution history-based recommendations  
- `algo-turnoverRec`: Learning opportunity and retention-based recommendations
- `algo-sofia`: Hybrid approach combining ChRev and TurnoverRec

#### Run Evaluation
```bash
python manager.py evaluate --r_owner <owner> --r_name <repo>
```

#### Disable Cache
Add `--no-cache` to force fresh calculations:
```bash
python manager.py --r_owner <owner> --r_name <repo> algo-revFinder --no-cache
```

## Evaluation Metrics

The system provides comprehensive evaluation metrics suitable for academic research:

### Precision Metrics
- **Precision@1, @3, @5, @10**: Accuracy of top-K recommendations
- **Hit Rate@K**: Percentage of successful recommendations at rank K

### Ranking Metrics
- **MRR (Mean Reciprocal Rank)**: Average reciprocal rank of first relevant result
- **MAP (Mean Average Precision)**: Mean of precision scores at relevant ranks
- **DCG (Discounted Cumulative Gain)**: Weighted ranking quality measure

### Coverage Metrics
- **Algorithm Coverage**: Percentage of PRs successfully processed
- **Ground Truth Coverage**: Percentage of PRs with available evaluation data

### Statistical Analysis
- **Score Distribution**: Mean, median, standard deviation of recommendation scores
- **Performance Comparisons**: Relative algorithm performance analysis
- **Success Rate**: Percentage of PRs with successful recommendations

## Data Structure

The system expects crawled data in the following structure:

```
crawled-data/
└── {owner}-{repo}/
    ├── pull/
    │   ├── all_data.json              # All pull requests
    │   └── {pr_number}/               # Individual PR data
    │       ├── files/all_data.json    # Changed files
    │       ├── reviews/all_data.json  # Code reviews
    │       ├── comments/all_data.json # Review comments
    │       └── commits/all_data.json  # PR commits
    ├── commit/
    │   ├── all_data.json              # Repository commits
    │   └── all/                       # Individual commit details
    │       └── {commit_sha}.json
    └── logs/
        └── unified_crawler_{timestamp}.log
```

## Debugging

The system includes comprehensive debugging tools:

### Data Structure Validation
```bash
python3 debug_data_system.py
```

### Algorithm-Level Debugging
```bash
python3 algorithm_debug.py
```

These tools help identify:
- Data loading issues
- Path mismatches
- Algorithm simulation problems
- Performance bottlenecks

## Output Files

Results are automatically saved to the `evaluation_results/` directory:

- **`{project}_advanced_metrics_{timestamp}.json`**: Detailed evaluation metrics
- **`{project}_advanced_summary_{timestamp}.csv`**: Summary table for spreadsheet analysis
- **`logs/{timestamp}.info.log`**: Execution logs

## Caching

The system uses intelligent caching to improve performance:
- **Algorithm results** are cached to avoid recomputation
- **File similarity scores** are pre-calculated and cached
- **Manager objects** are cached for faster data access

Cache files are stored in the `.cache/` directory and can be cleared by removing this directory.

## Supported Repositories

The system has been tested with:
- **Express.js** (2112 PRs, 87.4% review coverage)
- **jQuery** (3108 PRs, 19.9% review coverage)  
- **Transformers.js** (546 PRs, 16.8% review coverage)

## Performance Considerations

- **Large repositories** (>2000 PRs) may require significant processing time
- **Sofia algorithm** may be slow on very large datasets due to hybrid calculations
- **File similarity computation** is CPU-intensive but cached after first run
- **Memory usage** scales with repository size and number of developers

## Research Applications

This system is designed for academic research and provides:
- **Publication-quality metrics** suitable for peer review
- **Statistical significance testing** capabilities
- **Comparative analysis** across multiple algorithms
- **Reproducible results** with detailed methodology
- **Exportable data** for further statistical analysis

## Troubleshooting

### Common Issues

1. **"No repositories found"**: Check `DATA_BASE_DIR` environment variable
2. **"Division by zero"**: Repository may have insufficient review data
3. **"Directory not empty" cache errors**: Clear `.cache/` directory
4. **Slow performance**: Use `--no-cache` or debug with smaller datasets

### Debug Mode

Use the interactive debug mode to diagnose issues:
```bash
python3 debug_data_system.py
```

## Dependencies

Key Python packages:
- `numpy`: Numerical computations
- `ranx`: Ranking evaluation metrics
- `pandas`: Data analysis (optional, for CSV export)
- `scipy`: Statistical functions

## What This System Offers

This reviewer recommender system provides:

### **Advanced Algorithm Comparison**
- Four distinct recommendation algorithms with different approaches
- Comprehensive performance evaluation across multiple metrics
- Statistical analysis suitable for research and thesis work

### **Interactive Analysis Interface**
- User-friendly menu system for repository selection
- Real-time data quality validation
- Step-by-step algorithm execution with progress tracking

### **Research-Grade Evaluation**
- 15+ evaluation metrics including Precision@K, MRR, MAP, DCG
- Comparative rankings and performance insights
- Exportable results in JSON and CSV formats for further analysis

### **Debugging and Validation Tools**
- Data structure compatibility checking
- Algorithm-level debugging capabilities
- Performance bottleneck identification

### **Production-Ready Features**
- Intelligent caching system for improved performance
- Comprehensive error handling and logging
- Support for large-scale repository analysis

This system is designed for researchers, students, and practitioners who need reliable, measurable, and comparable reviewer recommendation algorithms with detailed evaluation capabilities.

## Algorithm Fidelity and Documented Deviations

Each algorithm follows its original paper. The implementation makes a few
deliberate, documented choices that a thesis should disclose:

- **cHRev** uses the original recency term `1/gap` (calendar days, `gap = 0 → 1`),
  not Mirsaeedi & Rigby's re-implementation `1/(gap + 1)`. Expertise is computed
  at the file level and falls back to the containing package, then the top-level
  system, when no reviewer has commented at the finer level.
- **RevFinder** fixes `LCSuff`: the longest common suffix is compared from the
  *end* of both paths. The authors' released script compared components by index
  from the front, which is wrong for paths of different depth. The four
  techniques are fused with Borda count giving `M − rank + 1` points per list, and
  a candidate absent from a list scores `0` (not `−∞`).
- **Knowledge model** (TurnoverRec, Sofia): a developer *knows* a file once they
  have committed to it or reviewed a PR containing it; commits/PRs touching ≥ 100
  files ("mega" changes) are ignored.
- **Sofia** routes a review to TurnoverRec when any file under review has ≤ 2
  knowledgeable developers, otherwise to cHRev (paper Eq. 10, whose two cases are
  swapped as printed; `d = 2`). When TurnoverRec yields no candidate for an
  at-risk PR, we fall back to cHRev — this fallback is our own decision.
- **Shared rules**: all algorithms use only events strictly before the target PR,
  exclude the PR author and bot accounts from both recommendations and ground
  truth, and break score ties deterministically.

Known limitations (not addressed): cHRev uses inline comments only; PR file lists
are the final set, not the first patch set; there is no merged-PR filter; commits
with no GitHub login fall back to email addresses; and the ICSE 2020 ΔExpertise /
ΔCoreWorkload / ΔFaR turnover simulation is not implemented.

## Citation

If you use this system in your research, please cite:

```bibtex
@software{mahmud_github_reviewer_recommender,
  title={Reviewer Recommender Analysis: A GitHub Reviewer Recommendation System with Advanced Evaluation},
  author={Mahmud, Abid Al},
  year={2026},
  doi={10.5281/zenodo.20777989},
  url={https://github.com/Abidstic/Reviewer-Recommender-Analysis}
}
```

The four recommendation algorithms implement the following published approaches. If you use them, please also cite the original papers:

- **RevFinder** — P. Thongtanunam, C. Tantithamthavorn, R. G. Kula, N. Yoshida, H. Iida, and K. Matsumoto, "Who Should Review My Code? A File Location-Based Code-Reviewer Recommendation Approach for Modern Code Review," SANER 2015.
- **cHRev** — M. B. Zanjani, H. Kagdi, and C. Bird, "Automatically Recommending Peer Reviewers in Modern Code Review," IEEE Transactions on Software Engineering, 2016.
- **TurnoverRec & Sofia** — E. Mirsaeedi and P. C. Rigby, "Mitigating Turnover with Code Review Recommendation: Balancing Expertise, Workload, and Knowledge Distribution," ICSE 2020.
