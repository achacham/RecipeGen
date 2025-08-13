import sqlite3
import json
from collections import Counter

class RecipeRecommender:
    def __init__(self, db_path="D:/RecipeGen_Database/processed/recipegen_master.db"):
        self.db_path = db_path
    
    def analyze_cuisine_preference(self, user_history):
        """Analyze which cuisines the user prefers"""
        cuisines = [recipe.get('cuisine') for recipe in user_history if recipe.get('cuisine')]
        cuisine_counts = Counter(cuisines)
        # Return top 3 cuisines
        return [cuisine for cuisine, count in cuisine_counts.most_common(3)]
    
    def analyze_complexity_preference(self, user_history):
        """Analyze cooking time preferences"""
        times = [recipe.get('total_time', 0) for recipe in user_history if recipe.get('total_time')]
        if times:
            avg_time = sum(times) / len(times)
            return {
                'min_time': max(10, avg_time - 30),
                'max_time': avg_time + 30
            }
        return {'min_time': 15, 'max_time': 60}  # Default
    
    def get_personalized_recommendations(self, user_history, limit=10):
        """Recommend recipes based on user's cooking history"""
        
        if not user_history:
            # No history - return top quality recipes
            return self.get_top_recipes(limit)
        
        # Analyze preferences
        cuisine_prefs = self.analyze_cuisine_preference(user_history)
        complexity_prefs = self.analyze_complexity_preference(user_history)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query based on preferences
        if cuisine_prefs:
            placeholders = ','.join(['?'] * len(cuisine_prefs))
            cursor.execute(f'''
                SELECT id, title, cuisine, dish_type, total_time, quality_score
                FROM recipes 
                WHERE cuisine IN ({placeholders})
                AND total_time BETWEEN ? AND ?
                AND quality_score > 70
                ORDER BY quality_score DESC
                LIMIT ?
            ''', cuisine_prefs + [complexity_prefs['min_time'], 
                                 complexity_prefs['max_time'], limit])
        else:
            cursor.execute('''
                SELECT id, title, cuisine, dish_type, total_time, quality_score
                FROM recipes 
                WHERE total_time BETWEEN ? AND ?
                AND quality_score > 70
                ORDER BY quality_score DESC
                LIMIT ?
            ''', [complexity_prefs['min_time'], complexity_prefs['max_time'], limit])
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_top_recipes(self, limit=10):
        """Get top recipes by quality score"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, cuisine, dish_type, total_time, quality_score
            FROM recipes 
            WHERE quality_score > 80
            ORDER BY quality_score DESC, times_served DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        return results

if __name__ == "__main__":
    # Test the recommender
    recommender = RecipeRecommender()
    print("Top 10 recipes:")
    for recipe in recommender.get_top_recipes(10):
        print(f"  - {recipe[1]} (Score: {recipe[5]})")