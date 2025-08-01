"""
Main clothing search agent that coordinates all search activities
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    import openai
except ImportError:
    openai = None

from base_agent import BaseAgent
from filter_agent import FilterAgent
from clothing_item import ClothingItem
from preferences import UserPreferences
# from scrapers.amazon_scraper import AmazonScraper
# from scrapers.ebay_scraper import EbayScraper
# from scrapers.etsy_scraper import EtsyScraper
# from scrapers.asos_scraper import AsosScraper
# from services.storage_service import StorageService
# from services.notification_service import NotificationService
# from utils.helpers import extract_search_terms, format_price

# Stub classes for missing modules
class AmazonScraper:
    def __init__(self, settings):
        self.settings = settings
    
    async def search(self, query, filters=None):
        return []

class EbayScraper:
    def __init__(self, settings):
        self.settings = settings
    
    async def search(self, query, filters=None):
        return []

class EtsyScraper:
    def __init__(self, settings):
        self.settings = settings
    
    async def search(self, query, filters=None):
        return []

class AsosScraper:
    def __init__(self, settings):
        self.settings = settings
    
    async def search(self, query, filters=None):
        return []

class StorageService:
    def __init__(self, settings):
        self.settings = settings
    
    def load_preferences(self):
        return None
    
    def save_preferences(self, prefs):
        pass
    
    async def store_search_results(self, query, results):
        pass

class NotificationService:
    def __init__(self, settings):
        self.settings = settings
    
    def send_notification(self, message):
        pass

def extract_search_terms(query):
    return query

def format_price(price):
    return f"${price}"


class ClothingAgent(BaseAgent):
    """Main agent for searching and finding clothing items"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the clothing agent"""
        super().__init__(config_path)
        
        # Validate required settings
        # self.validate_required_settings(['openai_api_key'])  # Commented out for testing
        
        # Initialize OpenAI if available
        if openai and self.settings.openai_api_key:
            openai.api_key = self.settings.openai_api_key
        
        # Initialize components
        self.filter_agent = FilterAgent(config_path)
        self.storage_service = StorageService(self.settings)
        self.notification_service = NotificationService(self.settings)
        
        # Initialize scrapers
        self.scrapers = self._initialize_scrapers()
        
        # User preferences
        self.user_preferences: Optional[UserPreferences] = None
        self._load_user_preferences()
    
    def _initialize_scrapers(self) -> Dict[str, Any]:
        """Initialize all enabled scrapers"""
        scrapers = {}
        
        for site in self.settings.enabled_sites:
            try:
                if site == "amazon":
                    scrapers[site] = AmazonScraper(self.settings)
                elif site == "ebay":
                    scrapers[site] = EbayScraper(self.settings)
                elif site == "etsy":
                    scrapers[site] = EtsyScraper(self.settings)
                elif site == "asos":
                    scrapers[site] = AsosScraper(self.settings)
                
                self.log_info(f"Initialized {site} scraper")
            except Exception as e:
                self.log_error(f"Failed to initialize {site} scraper", e)
        
        return scrapers
    
    def _load_user_preferences(self) -> None:
        """Load user preferences from storage"""
        try:
            prefs_data = self.storage_service.load_preferences()
            if prefs_data:
                self.user_preferences = UserPreferences(**prefs_data)
                self.log_info("Loaded user preferences")
            else:
                self.log_info("No user preferences found")
        except Exception as e:
            self.log_error("Failed to load user preferences", e)
    
    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[ClothingItem]:
        """
        Search for clothing items across all enabled sites
        
        Args:
            query: Natural language search query
            filters: Optional filters to apply
            
        Returns:
            List of clothing items found
        """
        self.log_info(f"Starting search for: {query}")
        
        try:
            # Process the query with AI if available
            processed_query = await self._process_query_with_ai(query)
            
            # Extract search terms and filters from the query
            search_terms = extract_search_terms(processed_query or query)
            auto_filters = await self._extract_filters_from_query(query)
            
            # Combine auto-extracted filters with provided filters
            combined_filters = {**(auto_filters or {}), **(filters or {})}
            
            # Search across all enabled scrapers
            search_tasks = []
            for site, scraper in self.scrapers.items():
                task = self._search_site(scraper, search_terms, combined_filters)
                search_tasks.append(task)
            
            # Execute searches concurrently
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine and process results
            all_items = []
            for i, result in enumerate(search_results):
                site = list(self.scrapers.keys())[i]
                if isinstance(result, Exception):
                    self.log_error(f"Search failed for {site}", result)
                elif isinstance(result, list):
                    all_items.extend(result)
                    self.log_info(f"Found {len(result)} items from {site}")
            
            # Apply intelligent filtering
            if self.user_preferences:
                filtered_items = await self.filter_agent.filter_by_preferences(
                    all_items, self.user_preferences
                )
            else:
                filtered_items = all_items
            
            # Apply additional filters
            if combined_filters:
                filtered_items = await self.filter_agent.apply_filters(
                    filtered_items, combined_filters
                )
            
            # Sort by relevance and price
            sorted_items = await self._sort_results(filtered_items, query)
            
            # Limit results
            max_results = self.settings.search.max_total_results
            final_results = sorted_items[:max_results]
            
            # Store results for future reference
            await self.storage_service.store_search_results(query, final_results)
            
            self.log_info(f"Search completed. Found {len(final_results)} items.")
            
            return final_results
            
        except Exception as e:
            self.log_error(f"Search failed for query: {query}", e)
            return []
    
    async def _search_site(self, scraper, search_terms: str, filters: Dict[str, Any]) -> List[ClothingItem]:
        """Search a specific site using its scraper"""
        try:
            return await scraper.search(search_terms, filters)
        except Exception as e:
            self.log_error(f"Search failed for {scraper.__class__.__name__}", e)
            return []
    
    async def _process_query_with_ai(self, query: str) -> Optional[str]:
        """Process natural language query with AI to improve search terms"""
        if not openai or not self.settings.openai_api_key:
            return None
        
        try:
            prompt = f"""
            Convert this natural language clothing search query into optimized search terms:
            Query: "{query}"
            
            Extract the key clothing items, brands, sizes, colors, and style preferences.
            Return only the optimized search terms, nothing else.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self.settings.ai.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.settings.ai.temperature,
                max_tokens=100
            )
            
            processed_query = response.choices[0].message.content.strip()
            self.log_debug(f"AI processed query: {processed_query}")
            return processed_query
            
        except Exception as e:
            self.log_error("Failed to process query with AI", e)
            return None
    
    async def _extract_filters_from_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract filters from natural language query"""
        if not openai or not self.settings.openai_api_key:
            return None
        
        try:
            available_sizes = self.settings.available_sizes
            available_colors = self.settings.available_colors
            price_ranges = self.settings.price_ranges
            
            prompt = f"""
            Extract filtering information from this clothing search query:
            Query: "{query}"
            
            Available sizes: {available_sizes}
            Available colors: {available_colors}
            Price ranges: {price_ranges}
            
            Return a JSON object with any of these keys if mentioned:
            - "size": size if mentioned (from available sizes)
            - "color": color if mentioned (from available colors)
            - "price_min": minimum price if mentioned
            - "price_max": maximum price if mentioned
            - "brand": brand name if mentioned
            
            Return only the JSON object, nothing else.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self.settings.ai.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            filters_text = response.choices[0].message.content.strip()
            try:
                filters = json.loads(filters_text)
                self.log_debug(f"Extracted filters: {filters}")
                return filters
            except json.JSONDecodeError:
                self.log_warning(f"Could not parse AI filter response: {filters_text}")
                return None
                
        except Exception as e:
            self.log_error("Failed to extract filters with AI", e)
            return None
    
    async def _sort_results(self, items: List[ClothingItem], query: str) -> List[ClothingItem]:
        """Sort results by relevance and other criteria"""
        # Simple sorting by price for now
        # In a real implementation, you'd use more sophisticated relevance scoring
        return sorted(items, key=lambda x: x.price if x.price else float('inf'))
    
    async def setup_user_preferences(self) -> None:
        """Interactive setup of user preferences"""
        print("🛍️  Setting up your clothing preferences...")
        
        preferences = {}
        
        # Size preference
        print(f"\nAvailable sizes: {', '.join(self.settings.available_sizes)}")
        size = input("What's your preferred size? ").strip().upper()
        if size in self.settings.available_sizes:
            preferences['preferred_size'] = size
        
        # Color preferences
        print(f"\nAvailable colors: {', '.join(self.settings.available_colors)}")
        colors = input("What are your favorite colors? (comma-separated): ").strip()
        if colors:
            color_list = [c.strip().lower() for c in colors.split(',')]
            preferences['preferred_colors'] = color_list
        
        # Price range
        print(f"\nPrice ranges: {self.settings.price_ranges}")
        price_range = input("What's your preferred price range? (budget/moderate/premium/luxury): ").strip().lower()
        if price_range in self.settings.price_ranges:
            preferences['price_range'] = price_range
        
        # Categories
        print(f"\nCategories: {', '.join(self.settings.categories)}")
        categories = input("What clothing categories are you interested in? (comma-separated): ").strip()
        if categories:
            category_list = [c.strip().lower() for c in categories.split(',')]
            preferences['preferred_categories'] = category_list
        
        # Brand preferences
        brands = input("Any preferred brands? (comma-separated): ").strip()
        if brands:
            brand_list = [b.strip() for b in brands.split(',')]
            preferences['preferred_brands'] = brand_list
        
        # Save preferences
        self.user_preferences = UserPreferences(**preferences)
        await self.storage_service.save_preferences(preferences)
        
        print("✅ Preferences saved successfully!")
    
    async def save_results(self, items: List[ClothingItem], filename: str) -> None:
        """Save search results to a file"""
        try:
            output_path = Path(filename)
            
            # Convert items to dict format
            items_data = [item.dict() for item in items]
            
            if output_path.suffix.lower() == '.json':
                with open(output_path, 'w') as f:
                    json.dump(items_data, f, indent=2)
            elif output_path.suffix.lower() == '.csv':
                import pandas as pd
                df = pd.DataFrame(items_data)
                df.to_csv(output_path, index=False)
            else:
                # Default to JSON
                with open(output_path.with_suffix('.json'), 'w') as f:
                    json.dump(items_data, f, indent=2)
            
            self.log_info(f"Results saved to {output_path}")
            
        except Exception as e:
            self.log_error(f"Failed to save results to {filename}", e)
    
    async def process(self, query: str, **kwargs) -> List[ClothingItem]:
        """Implementation of base agent process method"""
        return await self.search(query, kwargs.get('filters'))
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        # Close scrapers
        for scraper in self.scrapers.values():
            if hasattr(scraper, 'cleanup'):
                await scraper.cleanup()
        
        # Close services
        if hasattr(self.storage_service, 'cleanup'):
            await self.storage_service.cleanup()
        
        await super().cleanup()
