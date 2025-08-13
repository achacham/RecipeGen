#!/usr/bin/env python
"""
Run this daily to import new recipes AND improve quality
Usage: python database/daily_maintenance.py
"""

from datetime import datetime
from database_controller import DatabaseController  # No need for database. prefix
from quality_scorer import RecipeQualityScorer
from intelligent_indexer import IntelligentIndexer
from recipe_recommender import RecipeRecommender

def run_complete_maintenance():
    """Run all maintenance tasks"""
    print(f"\n{'='*60}")
    print(f"🚀 Starting RecipeGen Maintenance at {datetime.now()}")
    print('='*60)
    
    # 1. Import new recipes
    print("\n📥 STEP 1: Importing new recipes...")
    controller = DatabaseController()
    controller.connect()
    controller.import_all()
    controller.disconnect()
    
    # 2. Score all recipes
    print("\n📊 STEP 2: Updating quality scores...")
    scorer = RecipeQualityScorer()
    scorer.update_all_scores()
    
    # 3. Build search indices
    print("\n🔍 STEP 3: Building intelligent indices...")
    indexer = IntelligentIndexer()
    indexer.build_search_index()
    
    # 4. Test the recommender
    print("\n🎯 STEP 4: Testing recommendations...")
    recommender = RecipeRecommender()
    top_recipes = recommender.get_top_recipes(5)
    print("   Top 5 recipes by quality:")
    for recipe in top_recipes:
        print(f"      - {recipe[1]} (Score: {recipe[5]})")
    
    # 5. Clean up low-quality recipes
    print("\n🧹 STEP 5: Cleaning database...")
    cleanup_database()
    
    print(f"\n✅ Maintenance complete at {datetime.now()}")
    print('='*60)

def cleanup_database():
    """Remove poor quality recipes"""
    import sqlite3
    conn = sqlite3.connect("D:/RecipeGen_Database/processed/recipegen_master.db")
    cursor = conn.cursor()
    
    # Delete recipes with very low quality
    cursor.execute('''
        DELETE FROM recipes 
        WHERE quality_score < 30 
        AND times_served = 0
        AND source != 'ai_chef'
    ''')
    
    deleted = cursor.rowcount
    conn.commit()
    print(f"   🗑️ Removed {deleted} low-quality recipes")
    
    # Show database stats
    cursor.execute("SELECT COUNT(*) FROM recipes WHERE quality_score >= 70")
    high_quality = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM recipes")
    total = cursor.fetchone()[0]
    
    print(f"   📈 Database: {total:,} total recipes ({high_quality:,} high-quality)")
    conn.close()

if __name__ == "__main__":
    run_complete_maintenance()