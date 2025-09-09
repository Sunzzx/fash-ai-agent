#!/usr/bin/env python3
"""
Main entry point for the Clothing Search Agent
"""
import sys
import argparse
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from clothing_agent import ClothingAgent
from settings import Settings
from logger import logger


async def main():
    """Main function to run the clothing search agent"""
    parser = argparse.ArgumentParser(description="Clothing Search Agent")
    parser.add_argument(
        "--query", 
        type=str, 
        help="Search query for clothing items"
    )
    parser.add_argument(
        "--setup-preferences", 
        action="store_true",
        help="Set up user preferences"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        help="Output file for results"
    )
    parser.add_argument(
        "--social-media",
        action="store_true",
        help="Include social media trends in search results"
    )
    parser.add_argument(
        "--trending",
        action="store_true",
        help="Get trending fashion content from social media"
    )
    parser.add_argument(
        "--inspiration",
        type=str,
        help="Get fashion inspiration for specific style keywords (comma-separated)"
    )
    parser.add_argument(
        "--season",
        type=str,
        choices=['spring', 'summer', 'fall', 'winter'],
        help="Get seasonal fashion trends"
    )
    parser.add_argument(
        "--user-session",
        type=str,
        help="User session ID for personalized recommendations"
    )
    
    args = parser.parse_args()
    
    # Initialize settings and logging
    settings = Settings()
    logger.info("🚀 Application started")

    # Initialize the agent
    agent = ClothingAgent(config_path=args.config)
    
    try:
        if args.setup_preferences:
            # Interactive preference setup
            await agent.setup_user_preferences()
            logger.info("✅ User preferences have been set up successfully")
            return
        
        if args.trending:
            # Get trending fashion content
            print("🔥 Getting trending fashion content from social media...")
            results = await agent.get_trending_fashion(
                user_session_id=args.user_session,
                max_results=30
            )
            
            if results:
                print(f"\n✨ Found {len(results)} trending items:")
                for i, item in enumerate(results[:10], 1):
                    print(f"{i}. {item.title} - ${item.price} ({item.site})")
            else:
                print("❌ No trending content found")
                
        elif args.inspiration:
            # Get fashion inspiration
            keywords = [k.strip() for k in args.inspiration.split(',')]
            print(f"💡 Getting fashion inspiration for: {', '.join(keywords)}")
            results = await agent.get_fashion_inspiration(
                keywords=keywords,
                user_session_id=args.user_session,
                max_results=20
            )
            
            if results:
                print(f"\n✨ Found {len(results)} inspiration items:")
                for i, item in enumerate(results[:10], 1):
                    print(f"{i}. {item.title} - {item.site}")
            else:
                print("❌ No inspiration found")
                
        elif args.season:
            # Get seasonal trends
            print(f"🌿 Getting {args.season} fashion trends...")
            results = await agent.get_seasonal_trends(
                season=args.season,
                user_session_id=args.user_session,
                max_results=25
            )
            
            if results:
                print(f"\n✨ Found {len(results)} {args.season} trends:")
                for i, item in enumerate(results[:10], 1):
                    print(f"{i}. {item.title} - {item.site}")
            else:
                print(f"❌ No {args.season} trends found")
                
        elif args.query:
            # Regular search
            print(f"🔍 Searching for: {args.query}")
            include_social = args.social_media
            
            if include_social:
                results = await agent.search_with_social_media(
                    query=args.query,
                    user_session_id=args.user_session,
                    include_trends=True,
                    max_results=50
                )
            else:
                results = await agent.search(args.query)
            
            if results:
                print(f"\n✨ Found {len(results)} items:")
                for i, item in enumerate(results[:15], 1):
                    print(f"{i}. {item.title} - ${item.price} ({item.site})")
                
                if args.output:
                    await agent.save_results(results, args.output)
                    print(f"💾 Results saved to {args.output}")
            else:
                print("❌ No items found")
        else:
            # Interactive mode
            print("🎯 Welcome to Fash AI Agent!")
            print("Type 'help' for available commands or enter a search query.")
            print("Type 'quit' to exit.\n")
            
            while True:
                try:
                    user_input = input("👗 Search: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit']:
                        break
                    elif user_input.lower() == 'help':
                        print_help()
                    elif user_input.lower() == 'trending':
                        results = await agent.get_trending_fashion(max_results=10)
                        if results:
                            print(f"\n🔥 Trending now:")
                            for i, item in enumerate(results, 1):
                                print(f"{i}. {item.title} - {item.site}")
                        else:
                            print("❌ No trending content found")
                    elif user_input.lower().startswith('inspiration:'):
                        keywords_str = user_input[12:].strip()
                        if keywords_str:
                            keywords = [k.strip() for k in keywords_str.split(',')]
                            results = await agent.get_fashion_inspiration(keywords=keywords, max_results=10)
                            if results:
                                print(f"\n💡 Inspiration for '{keywords_str}':")
                                for i, item in enumerate(results, 1):
                                    print(f"{i}. {item.title} - {item.site}")
                            else:
                                print("❌ No inspiration found")
                        else:
                            print("❌ Please provide keywords after 'inspiration:'")
                    elif user_input:
                        results = await agent.search_with_social_media(
                            query=user_input,
                            include_trends=True,
                            max_results=10
                        )
                        if results:
                            print(f"\n✨ Found {len(results)} items:")
                            for i, item in enumerate(results, 1):
                                print(f"{i}. {item.title} - ${item.price} ({item.site})")
                        else:
                            print("❌ No items found")
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Search error: {e}")
                    print(f"❌ Search failed: {e}")
    
    except Exception as e:
        logger.critical(f"❌ Failed to run agent: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("👋 Application finished successfully")


def print_help():
    """Print help information"""
    help_text = """
Available commands:
- Type any clothing search query (e.g., "blue jeans size 32")
- 'trending' - Get trending fashion content from social media
- 'inspiration: [keywords]' - Get fashion inspiration (e.g., "inspiration: vintage bohemian")
- 'help' - Show this help message
- 'quit' or 'exit' - Exit the application

Examples:
- "red summer dress size M under $50"
- "nike running shoes size 10"
- "leather jacket black medium"
- "trending" - Get current fashion trends
- "inspiration: minimalist streetwear" - Get style inspiration
"""
    print(help_text)


if __name__ == "__main__":
    asyncio.run(main())
