"""
Filter agent for applying intelligent filtering to search results
"""

from typing import Dict, List, Any, Optional
import re

from base_agent import BaseAgent
from clothing_item import ClothingItem
from preferences import UserPreferences


class FilterAgent(BaseAgent):
    """Agent responsible for filtering and ranking clothing items"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the filter agent"""
        super().__init__(config_path)
    
    async def filter_by_preferences(
        self, 
        items: List[ClothingItem], 
        preferences: UserPreferences
    ) -> List[ClothingItem]:
        """
        Filter items based on user preferences
        
        Args:
            items: List of clothing items to filter
            preferences: User preferences to apply
            
        Returns:
            Filtered list of clothing items
        """
        filtered_items = []
        
        for item in items:
            if self._matches_preferences(item, preferences):
                # Calculate preference score
                item.preference_score = self._calculate_preference_score(item, preferences)
                filtered_items.append(item)
        
        # Sort by preference score (higher is better)
        filtered_items.sort(key=lambda x: x.preference_score or 0, reverse=True)
        
        self.log_info(f"Filtered {len(items)} items to {len(filtered_items)} based on preferences")
        return filtered_items
    
    async def apply_filters(
        self, 
        items: List[ClothingItem], 
        filters: Dict[str, Any]
    ) -> List[ClothingItem]:
        """
        Apply specific filters to items
        
        Args:
            items: List of clothing items to filter
            filters: Dictionary of filters to apply
            
        Returns:
            Filtered list of clothing items
        """
        filtered_items = []
        
        for item in items:
            if self._matches_filters(item, filters):
                filtered_items.append(item)
        
        self.log_info(f"Applied filters to {len(items)} items, {len(filtered_items)} remaining")
        return filtered_items
    
    def _matches_preferences(self, item: ClothingItem, preferences: UserPreferences) -> bool:
        """Check if an item matches user preferences"""
        
        # Size preference
        if preferences.preferred_size and item.size:
            if item.size.upper() != preferences.preferred_size.upper():
                return False
        
        # Color preference
        if preferences.preferred_colors and item.color:
            item_color = item.color.lower()
            if not any(color.lower() in item_color for color in preferences.preferred_colors):
                return False
        
        # Price range preference
        if preferences.price_range and item.price:
            price_ranges = self.settings.price_ranges
            if preferences.price_range in price_ranges:
                min_price, max_price = price_ranges[preferences.price_range]
                if not (min_price <= item.price <= max_price):
                    return False
        
        # Category preference
        if preferences.preferred_categories and item.category:
            item_category = item.category.lower()
            if not any(cat.lower() in item_category for cat in preferences.preferred_categories):
                return False
        
        # Brand preference
        if preferences.preferred_brands and item.brand:
            item_brand = item.brand.lower()
            if not any(brand.lower() in item_brand for brand in preferences.preferred_brands):
                return False
        
        return True
    
    def _matches_filters(self, item: ClothingItem, filters: Dict[str, Any]) -> bool:
        """Check if an item matches specific filters"""
        
        # Size filter
        if 'size' in filters and item.size:
            if item.size.upper() != filters['size'].upper():
                return False
        
        # Color filter
        if 'color' in filters and item.color:
            filter_color = filters['color'].lower()
            item_color = item.color.lower()
            if filter_color not in item_color:
                return False
        
        # Price filters
        if 'price_min' in filters and item.price:
            if item.price < filters['price_min']:
                return False
        
        if 'price_max' in filters and item.price:
            if item.price > filters['price_max']:
                return False
        
        # Brand filter
        if 'brand' in filters and item.brand:
            filter_brand = filters['brand'].lower()
            item_brand = item.brand.lower()
            if filter_brand not in item_brand:
                return False
        
        # Category filter
        if 'category' in filters and item.category:
            filter_category = filters['category'].lower()
            item_category = item.category.lower()
            if filter_category not in item_category:
                return False
        
        # Keywords filter
        if 'keywords' in filters:
            keywords = filters['keywords']
            if isinstance(keywords, str):
                keywords = [keywords]
            
            item_text = f"{item.title} {item.description or ''}".lower()
            if not any(keyword.lower() in item_text for keyword in keywords):
                return False
        
        # Exclude keywords filter
        if 'exclude_keywords' in filters:
            exclude_keywords = filters['exclude_keywords']
            if isinstance(exclude_keywords, str):
                exclude_keywords = [exclude_keywords]
            
            item_text = f"{item.title} {item.description or ''}".lower()
            if any(keyword.lower() in item_text for keyword in exclude_keywords):
                return False
        
        return True
    
    def _calculate_preference_score(self, item: ClothingItem, preferences: UserPreferences) -> float:
        """Calculate a preference score for an item (0.0 to 1.0)"""
        score = 0.0
        total_factors = 0
        
        # Size match (high weight)
        if preferences.preferred_size:
            total_factors += 3
            if item.size and item.size.upper() == preferences.preferred_size.upper():
                score += 3
        
        # Color match (medium weight)
        if preferences.preferred_colors and item.color:
            total_factors += 2
            item_color = item.color.lower()
            for color in preferences.preferred_colors:
                if color.lower() in item_color:
                    score += 2
                    break
        
        # Price range match (medium weight)
        if preferences.price_range and item.price:
            total_factors += 2
            price_ranges = self.settings.price_ranges
            if preferences.price_range in price_ranges:
                min_price, max_price = price_ranges[preferences.price_range]
                if min_price <= item.price <= max_price:
                    score += 2
                    # Bonus for being in the lower half of the range
                    mid_price = (min_price + max_price) / 2
                    if item.price <= mid_price:
                        score += 0.5
        
        # Category match (medium weight)
        if preferences.preferred_categories and item.category:
            total_factors += 2
            item_category = item.category.lower()
            for category in preferences.preferred_categories:
                if category.lower() in item_category:
                    score += 2
                    break
        
        # Brand match (low weight)
        if preferences.preferred_brands and item.brand:
            total_factors += 1
            item_brand = item.brand.lower()
            for brand in preferences.preferred_brands:
                if brand.lower() in item_brand:
                    score += 1
                    break
        
        # Avoid division by zero
        if total_factors == 0:
            return 0.5  # Neutral score
        
        return min(score / total_factors, 1.0)
    
    async def rank_by_relevance(
        self, 
        items: List[ClothingItem], 
        query: str
    ) -> List[ClothingItem]:
        """
        Rank items by relevance to the search query
        
        Args:
            items: List of clothing items to rank
            query: Original search query
            
        Returns:
            Items sorted by relevance score
        """
        query_words = set(query.lower().split())
        
        for item in items:
            relevance_score = self._calculate_relevance_score(item, query_words)
            item.relevance_score = relevance_score
        
        # Sort by relevance score (higher is better)
        items.sort(key=lambda x: x.relevance_score or 0, reverse=True)
        
        return items
    
    def _calculate_relevance_score(self, item: ClothingItem, query_words: set) -> float:
        """Calculate relevance score based on query terms"""
        score = 0.0
        
        # Title relevance (high weight)
        title_words = set(item.title.lower().split()) if item.title else set()
        title_matches = len(query_words.intersection(title_words))
        score += title_matches * 3
        
        # Description relevance (medium weight)
        if item.description:
            desc_words = set(item.description.lower().split())
            desc_matches = len(query_words.intersection(desc_words))
            score += desc_matches * 1.5
        
        # Brand relevance (medium weight)
        if item.brand:
            brand_words = set(item.brand.lower().split())
            brand_matches = len(query_words.intersection(brand_words))
            score += brand_matches * 2
        
        # Category relevance (low weight)
        if item.category:
            category_words = set(item.category.lower().split())
            category_matches = len(query_words.intersection(category_words))
            score += category_matches * 1
        
        # Normalize by query length
        max_possible_score = len(query_words) * 3  # All words in title
        if max_possible_score > 0:
            score = score / max_possible_score
        
        return min(score, 1.0)
    
    async def remove_duplicates(self, items: List[ClothingItem]) -> List[ClothingItem]:
        """Remove duplicate items based on similarity"""
        unique_items = []
        seen_items = set()
        
        for item in items:
            # Create a signature for the item
            signature = self._create_item_signature(item)
            
            if signature not in seen_items:
                seen_items.add(signature)
                unique_items.append(item)
            else:
                self.log_debug(f"Removed duplicate item: {item.title}")
        
        self.log_info(f"Removed {len(items) - len(unique_items)} duplicate items")
        return unique_items
    
    def _create_item_signature(self, item: ClothingItem) -> str:
        """Create a signature for an item to detect duplicates"""
        # Normalize title
        title = re.sub(r'[^\w\s]', '', item.title.lower()) if item.title else ''
        title = ' '.join(title.split())  # Normalize whitespace
        
        # Include key attributes
        brand = item.brand.lower() if item.brand else 'unknown'
        price = str(item.price) if item.price else '0'
        
        return f"{title}|{brand}|{price}"
    
    async def process(self, items: List[ClothingItem], **kwargs) -> List[ClothingItem]:
        """Implementation of base agent process method"""
        filters = kwargs.get('filters', {})
        preferences = kwargs.get('preferences')
        query = kwargs.get('query', '')
        
        # Apply filters
        if filters:
            items = await self.apply_filters(items, filters)
        
        # Apply preferences
        if preferences:
            items = await self.filter_by_preferences(items, preferences)
        
        # Rank by relevance
        if query:
            items = await self.rank_by_relevance(items, query)
        
        # Remove duplicates
        items = await self.remove_duplicates(items)
        
        return items
