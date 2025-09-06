from typing import List, Dict, Any
from clothing_item import ClothingItem
from preferences import UserPreferences
from logger import logger

class FilterSettings:
    """Filter settings for clothing items"""
    def __init__(self):
        self.sizes = []
        self.colors = []
        self.brands = []
        self.price_ranges = {}

class FilterAgent:
    def __init__(self, settings: FilterSettings):
        self.settings = settings

    def filter_items(self, items: List[ClothingItem], preferences: UserPreferences) -> List[ClothingItem]:
        """
        Filters clothing items based on user preferences and active filters.
        """
        logger.info("Starting filtering process for %d items", len(items))
        
        filtered_items = [
            item for item in items
            if self._matches_all_criteria(item, preferences)
        ]
        
        logger.info("Filtering complete. %d items match preferences.", len(filtered_items))
        return filtered_items

    def rank_items(self, items: List[ClothingItem], preferences: UserPreferences) -> List[Dict[str, Any]]:
        """
        Ranks items based on how well they match user preferences.
        """
        logger.info("Starting ranking process for %d items", len(items))
        
        ranked_items = [
            {"item": item, "score": round(self._calculate_relevance_score(item, preferences), 2)}
            for item in items
        ]
        
        ranked_items.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info("Ranking complete. Top item score: %.2f", ranked_items[0]["score"] if ranked_items else 0)
        return ranked_items

    # -------------------------
    # Internal helper functions
    # -------------------------
    def _matches_all_criteria(self, item: ClothingItem, preferences: UserPreferences) -> bool:
        """
        Checks if item matches user preferences and filter settings.
        """
        return self._matches_preferences(item, preferences) and self._matches_filters(item)

    def _matches_preferences(self, item: ClothingItem, preferences: UserPreferences) -> bool:
        """
        Matches the clothing item against the user's saved preferences.
        """
        normalized_size = (item.size or "").upper()
        preferred_size = (preferences.preferred_size or "").upper()
        if preferred_size and normalized_size != preferred_size:
            return False

        if preferences.preferred_colors:
            item_color = (item.color or "").lower()
            if not any(color.lower() in item_color for color in preferences.preferred_colors):
                return False

        if preferences.preferred_brands:
            if (item.brand or "").lower() not in (brand.lower() for brand in preferences.preferred_brands):
                return False

        if preferences.min_price and item.price < preferences.min_price:
            return False

        if preferences.max_price and item.price > preferences.max_price:
            return False

        return True

    def _matches_filters(self, item: ClothingItem) -> bool:
        """
        Matches the clothing item against active filter settings.
        """
        # Size filter
        if self.settings.sizes:
            if (item.size or "").upper() not in [s.upper() for s in self.settings.sizes]:
                return False

        # Color filter
        if self.settings.colors:
            item_color = (item.color or "").lower()
            if not any(color.lower() in item_color for color in self.settings.colors):
                return False

        # Brand filter
        if self.settings.brands:
            if (item.brand or "").lower() not in [b.lower() for b in self.settings.brands]:
                return False

        # Price range filter
        price_ranges = getattr(self.settings, "price_ranges", {})
        if price_ranges:
            min_price = price_ranges.get("min", 0)
            max_price = price_ranges.get("max", float('inf'))
            if not (min_price <= item.price <= max_price):
                return False

        return True

    def _calculate_relevance_score(self, item: ClothingItem, preferences: UserPreferences) -> float:
        """
        Calculates a relevance score based on preference matches.
        """
        score = 0

        # Brand match
        if preferences.preferred_brands and (item.brand or "").lower() in [b.lower() for b in preferences.preferred_brands]:
            score += 2.0

        # Color match
        if preferences.preferred_colors:
            item_color = (item.color or "").lower()
            if any(color.lower() in item_color for color in preferences.preferred_colors):
                score += 1.5

        # Size match
        if preferences.preferred_size and (item.size or "").upper() == (preferences.preferred_size or "").upper():
            score += 1.0

        # Price closeness
        if preferences.min_price or preferences.max_price:
            target_price = (preferences.min_price or 0 + preferences.max_price or 100) / 2
            price_diff = abs(item.price - target_price)
            price_score = max(0, 1 - (price_diff / target_price))
            score += price_score

        # Text relevance from description/title
        preference_keywords = set(
            word.lower() for word in (
                (preferences.description_keywords or []) +
                (preferences.title_keywords or [])
            )
        )

        item_text_tokens = set(((item.title or "") + " " + (item.description or "")).lower().split())
        score += len(preference_keywords & item_text_tokens) * 1.5

        return score
