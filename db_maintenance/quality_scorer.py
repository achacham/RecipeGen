import sqlite3
import json

class RecipeQualityScorer:
    def __init__(self, db_path="D:/RecipeGen_Database/processed/recipegen_master.db"):
        self.db_path = db_path
    
    def score_recipe(self, recipe):
        """Score recipe from 0-100 based on completeness and quality"""
        score = 0
        
        # COMPLETENESS CHECKS (50 points)
        if recipe['instructions'] and len(recipe['instructions']) >= 5:
            score += 15  # Detailed instructions
        elif len(recipe['instructions']) >= 3:
            score += 8
            
        if recipe['ingredients'] and len(recipe['ingredients']) >= 5:
            score += 10  # Reasonable ingredient list
            
        if recipe['total_time'] and recipe['total_time'] > 0:
            score += 5  # Has timing info
            
        if recipe['image_url']:
            score += 10  # Has image
            
        if recipe['cuisine'] and recipe['dish_type']:
            score += 10  # Properly categorized
            
        # QUALITY INDICATORS (30 points)
        instructions_text = ' '.join([s.get('instruction', '') for s in recipe['instructions']])
        
        # Check for detailed instructions
        if any(word in instructions_text.lower() for word in 
               ['temperature', 'degrees', 'minutes', 'until golden', 'until tender']):
            score += 10  # Specific cooking guidance
            
        # Check for technique descriptions
        if any(word in instructions_text.lower() for word in 
               ['dice', 'julienne', 'sauté', 'simmer', 'fold', 'whisk']):
            score += 10  # Professional techniques
            
        # Reasonable cooking time
        if 10 <= recipe.get('total_time', 0) <= 180:  # 10 mins to 3 hours
            score += 10  # Realistic time
            
        # POPULARITY/VERIFICATION (20 points)
        if recipe.get('times_served', 0) > 0:
            score += min(recipe['times_served'] * 2, 10)  # User popularity
            
        if recipe.get('source') in ['tasty', 'spoonacular']:  # Verified sources
            score += 10
            
        return min(score, 100)  # Cap at 100
    
    def update_all_scores(self):
        """Recalculate all recipe quality scores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("   📊 Calculating quality scores for all recipes...")
        
        cursor.execute("""
            SELECT id, ingredients, instructions, total_time, image_url, 
                   cuisine, dish_type, source, times_served 
            FROM recipes
        """)
        
        recipes_updated = 0
        for row in cursor.fetchall():
            try:
                recipe = {
                    'id': row[0],
                    'ingredients': json.loads(row[1]) if row[1] else [],
                    'instructions': json.loads(row[2]) if row[2] else [],
                    'total_time': row[3],
                    'image_url': row[4],
                    'cuisine': row[5],
                    'dish_type': row[6],
                    'source': row[7],
                    'times_served': row[8] or 0
                }
                
                new_score = self.score_recipe(recipe)
                cursor.execute("UPDATE recipes SET quality_score = ? WHERE id = ?", 
                              (new_score, recipe['id']))
                recipes_updated += 1
                
                if recipes_updated % 500 == 0:
                    print(f"      ✅ Updated {recipes_updated} recipes...")
                    
            except Exception as e:
                print(f"      ⚠️ Error scoring recipe {row[0]}: {e}")
                continue
        
        conn.commit()
        conn.close()
        print(f"   ✅ Updated quality scores for {recipes_updated} recipes")

if __name__ == "__main__":
    # Test the scorer
    scorer = RecipeQualityScorer()
    scorer.update_all_scores()