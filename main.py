#!/usr/bin/env python3
"""
Main entry point for the Clothing Search Agent
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from clothing_agent import ClothingAgent
from settings import Settings
# Simple logging setup function
def setup_logging(log_level, log_file):
    import logging
    from pathlib import Path
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


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
    
    args = parser.parse_args()
    
    # Initialize settings and logging
    settings = Settings()
    setup_logging(settings.log_level, settings.log_file)
    
    # Initialize the agent
    agent = ClothingAgent(config_path=args.config)
    
    try:
        if args.setup_preferences:
            # Interactive preference setup
            await agent.setup_user_preferences()
            print("✅ User preferences have been set up successfully!")
            return
        
        if args.query:
            # Perform search
            print(f"🔍 Searching for: {args.query}")
            results = await agent.search(args.query)
            
            if results:
                print(f"✅ Found {len(results)} items:")
                for i, item in enumerate(results[:10], 1):  # Show top 10
                    print(f"{i}. {item.title}")
                    print(f"   Price: ${item.price}")
                    print(f"   Site: {item.site}")
                    print(f"   URL: {item.url}")
                    print("-" * 50)
                
                if args.output:
                    await agent.save_results(results, args.output)
                    print(f"💾 Results saved to {args.output}")
            else:
                print("❌ No items found matching your criteria")
        else:
            # Interactive mode
            print("👋 Welcome to Clothing Search Agent!")
            print("Type 'help' for commands or 'quit' to exit")
            
            while True:
                try:
                    query = input("\n🔍 Enter search query: ").strip()
                    
                    if query.lower() in ['quit', 'exit', 'q']:
                        break
                    elif query.lower() == 'help':
                        print_help()
                        continue
                    elif query:
                        results = await agent.search(query)
                        if results:
                            print(f"✅ Found {len(results)} items (showing top 5):")
                            for i, item in enumerate(results[:5], 1):
                                print(f"{i}. {item.title} - ${item.price} ({item.site})")
                        else:
                            print("❌ No items found")
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Failed to run agent: {e}")
        sys.exit(1)
    
    print("👋 Thanks for using Clothing Search Agent!")


def print_help():
    """Print help information"""
    help_text = """
Available commands:
- Type any clothing search query (e.g., "blue jeans size 32")
- 'help' - Show this help message
- 'quit' or 'exit' - Exit the application

Examples:
- "red summer dress size M under $50"
- "nike running shoes size 10"
- "leather jacket black medium"
"""
    print(help_text)


if __name__ == "__main__":
    asyncio.run(main())
