"""
Intelligent Prompt Evolution System for RecipeGen
"""
import sqlite3
import json
from typing import Tuple, Optional

class PromptEvolution:
    def __init__(self, db_path='recipegen.db'):
        self.db_path = db_path
    
    def get_best_prompt(self, provider: str, cuisine: str = None) -> Tuple[Optional[int], str]:
        """
        Get the best performing prompt for this provider/cuisine combination
        Returns: (template_id, template_text)
        """
        with sqlite3.connect(self.db_path) as conn:
            # First try cuisine-specific prompt
            if cuisine:
                cursor = conn.execute('''
                    SELECT id, template_text, success_score 
                    FROM prompt_templates 
                    WHERE provider = ? 
                    AND is_active = 1
                    AND cuisine_affinity = ?
                    ORDER BY success_score DESC 
                    LIMIT 1
                ''', (provider, cuisine))
                
                result = cursor.fetchone()
                if result:
                    template_id, template_text, score = result
                    print(f"📊 Using cuisine-specific prompt (score: {score})")
                    self._track_usage(template_id)
                    return template_id, template_text
            
            # Fall back to general high-performer
            cursor = conn.execute('''
                SELECT id, template_text, success_score 
                FROM prompt_templates 
                WHERE provider = ? 
                AND is_active = 1
                AND cuisine_affinity IS NULL
                ORDER BY success_score DESC 
                LIMIT 1
            ''', (provider,))
            
            result = cursor.fetchone()
            if result:
                template_id, template_text, score = result
                print(f"📊 Using general prompt (score: {score})")
                self._track_usage(template_id)
                return template_id, template_text
            
            # No templates found
            return None, ""
    
    def _track_usage(self, template_id: int):
        """Track that this template was used"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE prompt_templates 
                SET total_uses = total_uses + 1 
                WHERE id = ?
            ''', (template_id,))
    
    def record_video_result(self, task_id: str, template_id: int):
        """Record initial result when video generation starts"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO prompt_results (template_id, task_id)
                VALUES (?, ?)
            ''', (template_id, task_id))
    
    def update_video_success(self, task_id: str, success: bool):
        """Update when video successfully generates (or fails)"""
        if not success:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            # Get template_id from the task
            cursor = conn.execute('''
                SELECT pr.template_id 
                FROM prompt_results pr
                WHERE pr.task_id = ?
            ''', (task_id,))
            
            result = cursor.fetchone()
            if result:
                template_id = result[0]
                # Update successful video count
                conn.execute('''
                    UPDATE prompt_templates 
                    SET successful_videos = successful_videos + 1
                    WHERE id = ?
                ''', (template_id,))
                
                # Recalculate success score
                self._update_success_score(template_id)
    
    def _update_success_score(self, template_id: int):
        """Recalculate success score based on performance"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT total_uses, successful_videos, videos_purchased 
                FROM prompt_templates 
                WHERE id = ?
            ''', (template_id,))
            
            result = cursor.fetchone()
            if result:
                total_uses, successful_videos, videos_purchased = result
                
                if total_uses > 0:
                    # Simple scoring: % successful * 70 + % purchased * 30
                    success_rate = (successful_videos / total_uses) * 70
                    purchase_rate = (videos_purchased / total_uses) * 30
                    new_score = success_rate + purchase_rate
                    
                    conn.execute('''
                        UPDATE prompt_templates 
                        SET success_score = ?
                        WHERE id = ?
                    ''', (new_score, template_id))

# Global instance
prompt_evolution = PromptEvolution()