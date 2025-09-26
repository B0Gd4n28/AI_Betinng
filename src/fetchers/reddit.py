"""
Reddit sentiment analysis for football matches
Analyzes r/soccer and r/sportsbook discussions for match sentiment
"""
from __future__ import annotations
import requests
import logging
from typing import Dict, Any, List, Optional
import re
import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.cache import cache
from utils.config import settings

logger = logging.getLogger(__name__)

# Simple sentiment analysis without external dependencies
# Maps positive/negative words to sentiment scores
POSITIVE_WORDS = {
    'good', 'great', 'excellent', 'amazing', 'fantastic', 'wonderful', 'brilliant',
    'win', 'victory', 'success', 'strong', 'confident', 'best', 'top', 'quality',
    'form', 'impressive', 'dominant', 'solid', 'reliable', 'consistent'
}

NEGATIVE_WORDS = {
    'bad', 'terrible', 'awful', 'horrible', 'disappointing', 'weak', 'poor',
    'lose', 'loss', 'defeat', 'struggle', 'difficult', 'worst', 'bottom',
    'inconsistent', 'unreliable', 'shaky', 'vulnerable', 'injury', 'injured'
}

class RedditSentimentAPI:
    """
    Reddit sentiment analysis using public Reddit API
    """
    
    def __init__(self):
        self.reddit_base = "https://www.reddit.com"
        self.user_agent = settings.reddit_user_agent or "PariuSmart-Bot/1.0"
    
    def _simple_sentiment_score(self, text: str) -> float:
        """
        Simple rule-based sentiment analysis
        Returns score between -1.0 (negative) and 1.0 (positive)
        """
        if not text:
            return 0.0
        
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        positive_count = sum(1 for word in words if word in POSITIVE_WORDS)
        negative_count = sum(1 for word in words if word in NEGATIVE_WORDS)
        
        total_words = len(words)
        if total_words == 0:
            return 0.0
        
        # Calculate sentiment score
        sentiment = (positive_count - negative_count) / total_words
        return max(-1.0, min(1.0, sentiment))
    
    def _search_reddit_posts(self, query: str, subreddit: str = "soccer", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search Reddit posts using public API
        """
        try:
            url = f"{self.reddit_base}/r/{subreddit}/search.json"
            params = {
                "q": query,
                "sort": "new",
                "limit": limit,
                "t": "week"  # Past week
            }
            
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, params=params, headers=headers, timeout=20)
            
            if response.status_code != 200:
                logger.error(f"Reddit search error {response.status_code}")
                return []
            
            data = response.json()
            posts = []
            
            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})
                posts.append({
                    "title": post_data.get("title", ""),
                    "selftext": post_data.get("selftext", ""),
                    "score": post_data.get("score", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "created_utc": post_data.get("created_utc", 0)
                })
            
            return posts
            
        except requests.RequestException as e:
            logger.error(f"Reddit search request failed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected Reddit search error: {str(e)}")
            return []
    
    def get_match_sentiment(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """
        Get sentiment analysis for a match from Reddit discussions
        
        Args:
            home_team: Home team name
            away_team: Away team name
            
        Returns:
            dict: {
                "label": "positive|neutral|negative",
                "score": float,  # -1.0 to 1.0
                "confidence": float,  # 0.0 to 1.0
                "sources": int  # Number of posts analyzed
            }
        """
        cache_key = f"reddit_sentiment_{home_team}_{away_team}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Using cached Reddit sentiment for {home_team} vs {away_team}")
            return cached_result
        
        # If Reddit API is not configured, return neutral
        if not settings.has_reddit():
            logger.debug("Reddit API not configured, returning neutral sentiment")
            return {
                "label": "neutral",
                "score": 0.0,
                "confidence": 0.0,
                "sources": 0
            }
        
        # Search for match discussions
        queries = [
            f"{home_team} vs {away_team}",
            f"{home_team} {away_team}",
            f"{away_team} vs {home_team}"
        ]
        
        all_posts = []
        
        # Search in r/soccer and r/sportsbook
        for subreddit in ["soccer", "sportsbook"]:
            for query in queries:
                posts = self._search_reddit_posts(query, subreddit, limit=5)
                all_posts.extend(posts)
                
                if len(all_posts) >= 20:  # Limit total posts to analyze
                    break
            
            if len(all_posts) >= 20:
                break
        
        if not all_posts:
            return {
                "label": "neutral",
                "score": 0.0,
                "confidence": 0.0,
                "sources": 0
            }
        
        # Analyze sentiment of posts
        sentiment_scores = []
        
        for post in all_posts[:20]:  # Limit to 20 posts max
            # Combine title and text for analysis
            text = f"{post['title']} {post['selftext']}"
            score = self._simple_sentiment_score(text)
            
            # Weight by post score (upvotes)
            weight = max(1, post.get('score', 1))
            sentiment_scores.extend([score] * min(weight, 10))  # Cap weight at 10
        
        if not sentiment_scores:
            return {
                "label": "neutral",
                "score": 0.0,
                "confidence": 0.0,
                "sources": len(all_posts)
            }
        
        # Calculate average sentiment
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        
        # Calculate confidence based on consistency and number of sources
        consistency = 1.0 - (len(set(sentiment_scores)) / len(sentiment_scores))
        source_confidence = min(1.0, len(all_posts) / 10)
        confidence = (consistency + source_confidence) / 2
        
        # Determine label
        if avg_sentiment > 0.1:
            label = "positive"
        elif avg_sentiment < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        result = {
            "label": label,
            "score": round(avg_sentiment, 3),
            "confidence": round(confidence, 3),
            "sources": len(all_posts)
        }
        
        # Cache for 2 hours
        cache.set(cache_key, result, ttl=7200)
        
        return result


# Global instance
reddit_api = RedditSentimentAPI()

# Convenience function for backward compatibility
def get_match_sentiment(home_team: str, away_team: str) -> Dict[str, Any]:
    """Get sentiment analysis for a match from Reddit discussions"""
    return reddit_api.get_match_sentiment(home_team, away_team)