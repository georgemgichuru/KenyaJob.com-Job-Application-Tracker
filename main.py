#!/usr/bin/env python3
"""
KenyaJob.com Job Application Tracker - Main Entry Point

This script orchestrates the job application tracking process for KenyaJob.com.
It uses Selenium for web automation and pandas for data management.
"""

import os
import sys
import argparse
from datetime import datetime
from kenyajob_tracker import KenyaJobTracker
import config

def setup_environment():
    """Set up the environment and check dependencies"""
    print("=" * 60)
    print("KENYAJOB.COM JOB APPLICATION TRACKER")
    print("=" * 60)
    
    # Check if output directories exist
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.SCREENSHOTS_DIR, exist_ok=True)
    
    print(f"Output directory: {os.path.abspath(config.OUTPUT_DIR)}")
    print(f"Screenshots directory: {os.path.abspath(config.SCREENSHOTS_DIR)}")
    print()

def display_configuration():
    """Display current configuration settings"""
    print("CURRENT CONFIGURATION:")
    print(f"Keywords: {', '.join(config.KEYWORDS)}")
    print(f"Location: {config.LOCATION}")
    print(f"Category: {config.CATEGORY}")
    print(f"Max Listings: {config.MAX_LISTINGS}")
    print(f"Days Recent: {config.DAYS_RECENT}")
    print(f"Headless Mode: {'Yes' if config.HEADLESS else 'No'}")
    print()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='KenyaJob.com Job Application Tracker')
    
    parser.add_argument('--keywords', nargs='+', help='Job search keywords')
    parser.add_argument('--location', help='Job location')
    parser.add_argument('--category', help='Job category')
    parser.add_argument('--max-listings', type=int, help='Maximum number of listings to extract')
    parser.add_argument('--days-recent', type=int, help='Only show jobs from last X days')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--test', action='store_true', help='Run in test mode (limited listings)')
    
    return parser.parse_args()

def update_config_from_args(args):
    """Update configuration from command line arguments"""
    if args.keywords:
        config.KEYWORDS = args.keywords
    if args.location:
        config.LOCATION = args.location
    if args.category:
        config.CATEGORY = args.category
    if args.max_listings:
        config.MAX_LISTINGS = args.max_listings
    if args.days_recent:
        config.DAYS_RECENT = args.days_recent
    if args.headless:
        config.HEADLESS = args.headless
    if args.test:
        config.MAX_LISTINGS = 5  # Limit to 5 listings for testing

def main():
    """Main function"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        update_config_from_args(args)
        
        # Setup environment
        setup_environment()
        display_configuration()
        
        # Initialize and run tracker
        print("Starting job tracking process...")
        print("-" * 40)
        
        tracker = KenyaJobTracker()
        tracker.run()
        
        print("-" * 40)
        print("Process completed!")
        print(f"Check the '{config.OUTPUT_DIR}' directory for results.")
        
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user. Exiting...")
        sys.exit(1)
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Please check your internet connection and ChromeDriver setup.")
        sys.exit(1)

if __name__ == "__main__":
    main()
