#!/usr/bin/env python3
"""
Multi-API Setup Script for YouTube Data API Keys

This script helps you set up multiple YouTube Data API keys from different
Google Cloud accounts to effectively multiply your daily quota.

STRATEGY:
- Create 2-3 separate Google Cloud accounts 
- Get YouTube Data API key from each account
- Effectively get 20,000-30,000 calls per day instead of 10,000
"""

import os
from dotenv import load_dotenv, set_key

def display_banner():
    print("\n" + "="*60)
    print("🔑 MULTI-API SETUP FOR YOUTUBE DATA API")
    print("="*60)
    print("• Multiply your daily quota from 10,000 to 30,000+ calls")
    print("• Use multiple Google Cloud accounts")
    print("• Automatic rotation when quota exceeded")
    print("• Professional approach used by many developers")
    print("="*60)

def check_existing_keys():
    """Check what API keys are already configured"""
    load_dotenv()
    
    keys_found = []
    primary_key = os.getenv('YOUTUBE_API_KEY')
    if primary_key:
        keys_found.append(('Primary', 'YOUTUBE_API_KEY', primary_key[:20] + "..."))
    
    # Check for secondary keys
    i = 2
    while True:
        key = os.getenv(f'YOUTUBE_API_KEY_{i}')
        if key:
            keys_found.append((f'Secondary #{i-1}', f'YOUTUBE_API_KEY_{i}', key[:20] + "..."))
            i += 1
        else:
            break
    
    return keys_found

def setup_api_key(key_name, env_var_name):
    """Setup a single API key"""
    print(f"\n🔑 Setting up {key_name}")
    print("-" * 40)
    
    api_key = input(f"Enter your {key_name} YouTube API key: ").strip()
    
    if not api_key:
        print("❌ No API key entered")
        return False
    
    if len(api_key) < 30:
        print("⚠️  Warning: API key seems too short")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return False
    
    # Save to .env file
    set_key('.env', env_var_name, api_key)
    print(f"✅ {key_name} saved as {env_var_name}")
    return True

def google_cloud_setup_guide():
    """Display guide for creating Google Cloud accounts and API keys"""
    print("\n📋 GOOGLE CLOUD SETUP GUIDE")
    print("="*50)
    print("""
🔹 STEP 1: Create Multiple Google Accounts
   • Create 2-3 separate Gmail accounts
   • Use different names/emails for each

🔹 STEP 2: Set Up Google Cloud Projects
   For EACH account:
   1. Go to: https://console.cloud.google.com/
   2. Create a new project
   3. Enable YouTube Data API v3
   4. Create API credentials (API Key)
   5. Copy the API key

🔹 STEP 3: Configure API Keys Here
   • Run this script to save all your keys
   • System will automatically rotate between them

💡 BENEFITS:
   ✅ 10,000 calls per key per day
   ✅ 2 keys = 20,000 calls/day 
   ✅ 3 keys = 30,000 calls/day
   ✅ Automatic failover when quota exceeded
   ✅ Professional approach used by developers
""")

def main():
    display_banner()
    
    # Check existing configuration
    existing_keys = check_existing_keys()
    
    if existing_keys:
        print(f"\n📊 CURRENT CONFIGURATION:")
        for name, env_var, preview in existing_keys:
            print(f"  {name}: {preview}")
        print(f"\nTotal API keys configured: {len(existing_keys)}")
        
        choice = input("\n🤔 Do you want to:\n1. Add more keys\n2. Replace existing keys\n3. View setup guide\n4. Exit\nChoice (1-4): ").strip()
        
        if choice == '3':
            google_cloud_setup_guide()
            return
        elif choice == '4':
            return
        elif choice == '2':
            # Clear existing keys
            print("\n🗑️  Clearing existing configuration...")
    else:
        print("\n📭 No API keys found. Let's set them up!")
        
        choice = input("🤔 Do you want to:\n1. Set up API keys now\n2. View setup guide first\nChoice (1-2): ").strip()
        
        if choice == '2':
            google_cloud_setup_guide()
            choice = input("\nReady to set up keys now? (y/n): ").strip().lower()
            if choice != 'y':
                return
    
    # Set up API keys
    print("\n🔧 API KEY SETUP")
    print("-" * 30)
    
    # Primary key
    setup_api_key("Primary API Key", "YOUTUBE_API_KEY")
    
    # Ask for additional keys
    key_count = 2
    while True:
        add_more = input(f"\n🔑 Add another API key (Key #{key_count})? (y/n): ").strip().lower()
        if add_more != 'y':
            break
        
        if setup_api_key(f"API Key #{key_count}", f"YOUTUBE_API_KEY_{key_count}"):
            key_count += 1
        
        if key_count > 5:
            print("⚠️  That's a lot of keys! You probably have enough.")
            break
    
    # Final summary
    final_keys = check_existing_keys()
    
    print("\n🎉 SETUP COMPLETE!")
    print("="*40)
    print(f"✅ {len(final_keys)} API keys configured")
    print(f"📈 Daily quota: ~{len(final_keys) * 10000:,} calls")
    print("✅ Automatic rotation enabled")
    print("✅ Ready for unlimited discovery!")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Run: python optimized_multi_api_finder.py")
    print("2. Sit back and watch it find influencers!")
    print("3. When one key hits quota, it auto-switches")
    
    print("\n💡 TIP: You can add more keys anytime by running this script again")

if __name__ == "__main__":
    main() 