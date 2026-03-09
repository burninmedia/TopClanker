#!/usr/bin/env python3
"""
TopClanker Benchmark Score Calculator

Usage:
  python calculate_scores.py

This script calculates benchmark scores for AI models based on
individual benchmark results and category weights defined in data.json
"""

import json
from typing import Dict, Optional

# Category weights (from methodology)
CATEGORY_WEIGHTS = {
    "reasoning": {
        "mmlu": 0.40,
        "gpqa": 0.30,
        "arenaElo": 0.30
    },
    "math": {
        "gsm8k": 0.40,
        "math": 0.40,
        "aime": 0.20
    },
    "research": {
        "mmlu": 0.35,
        "mmmu": 0.30,
        "citationAccuracy": 0.35
    },
    "learning": {
        "humaneval": 0.40,
        "sweBench": 0.40,
        "adaptive": 0.20
    }
}

def normalize_arena_elo(elo: int) -> float:
    """
    Normalize Arena Elo to 0-100 scale
    Typical range: 1200-1350
    """
    min_elo = 1150
    max_elo = 1350
    normalized = ((elo - min_elo) / (max_elo - min_elo)) * 100
    return max(0, min(100, normalized))

def calculate_category_score(
    benchmarks: Dict[str, float], 
    category: str
) -> Optional[float]:
    """
    Calculate weighted score for a category
    
    Args:
        benchmarks: Dict of benchmark names to scores
        category: Category name (reasoning, math, research, learning)
    
    Returns:
        Weighted score (0-100) or None if missing required benchmarks
    """
    if category not in CATEGORY_WEIGHTS:
        return None
    
    weights = CATEGORY_WEIGHTS[category]
    score = 0
    total_weight = 0
    
    for benchmark, weight in weights.items():
        if benchmark in benchmarks:
            bench_score = benchmarks[benchmark]
            
            # Special handling for Arena Elo
            if benchmark == "arenaElo":
                bench_score = normalize_arena_elo(bench_score)
            
            score += bench_score * weight
            total_weight += weight
    
    # Only return score if we have all required benchmarks
    if total_weight >= 0.9:  # Allow for small rounding errors
        return round(score, 1)
    
    return None

def apply_bonuses(score: float, privacy: str, is_open_source: bool) -> float:
    """
    Apply privacy and open-source bonuses
    
    Args:
        score: Base benchmark score
        privacy: Privacy rating (high, medium, low)
        is_open_source: Whether model is open source
    
    Returns:
        Score with bonuses applied
    """
    bonus = 0
    
    if privacy == "high":
        bonus += 5
    
    if is_open_source:
        bonus += 3
    
    # Apply bonuses as percentage increase
    final_score = score * (1 + bonus / 100)
    return round(min(100, final_score))

def calculate_all_scores(data_file: str = "data-real-benchmarks.json"):
    """
    Calculate scores for all agents in data file
    """
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    print("TopClanker Benchmark Score Calculator")
    print("=" * 50)
    print()
    
    for agent in data['agents']:
        name = agent['name']
        category = agent['category']
        benchmarks = agent.get('benchmarks', {})
        
        # Calculate base score
        base_score = calculate_category_score(benchmarks, category)
        
        if base_score is None:
            print(f"⚠️  {name} - Missing benchmarks for {category}")
            continue
        
        # Apply bonuses
        privacy = agent.get('privacy', 'medium')
        is_open = agent.get('type') == 'open-source'
        final_score = apply_bonuses(base_score, privacy, is_open)
        
        # Compare to stored score
        stored_score = agent.get('benchmarkScore', 0)
        match = "✓" if abs(final_score - stored_score) < 2 else "✗"
        
        print(f"{match} {name} ({category})")
        print(f"   Base: {base_score:.1f} | Final: {final_score:.0f} | Stored: {stored_score}")
        print(f"   Benchmarks: {benchmarks}")
        print()

def calculate_single(
    category: str,
    benchmarks: Dict[str, float],
    privacy: str = "medium",
    is_open_source: bool = False
):
    """
    Calculate score for a single model
    
    Example:
        calculate_single(
            category="reasoning",
            benchmarks={"mmlu": 86.5, "gpqa": 75.4, "arenaElo": 1300},
            privacy="high",
            is_open_source=False
        )
    """
    base_score = calculate_category_score(benchmarks, category)
    
    if base_score is None:
        print(f"❌ Missing required benchmarks for {category}")
        print(f"   Required: {list(CATEGORY_WEIGHTS[category].keys())}")
        print(f"   Provided: {list(benchmarks.keys())}")
        return None
    
    final_score = apply_bonuses(base_score, privacy, is_open_source)
    
    print(f"Category: {category}")
    print(f"Base Score: {base_score:.1f}")
    print(f"Privacy Bonus: +{5 if privacy == 'high' else 0}%")
    print(f"Open Source Bonus: +{3 if is_open_source else 0}%")
    print(f"Final Score: {final_score:.0f}")
    
    return final_score

if __name__ == "__main__":
    # Calculate all scores
    calculate_all_scores()
    
    print("\n" + "=" * 50)
    print("\nExample: Calculate score for a new model")
    print("-" * 50)
    
    # Example calculation
    calculate_single(
        category="reasoning",
        benchmarks={
            "mmlu": 88.0,
            "gpqa": 72.0,
            "arenaElo": 1287
        },
        privacy="medium",
        is_open_source=False
    )
