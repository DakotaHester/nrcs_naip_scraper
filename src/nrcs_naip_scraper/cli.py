"""
Command Line Interface for NRCS NAIP Scraper

This module provides the command-line interface for downloading NAIP 
(National Agriculture Imagery Program) imagery data from USDA NRCS Box folder.
Supports filtering by year and state with safety confirmations for bulk downloads.
"""

import argparse
import sys
import textwrap
from typing import NoReturn
from .scraper import NAIPScraper


def get_user_confirmation() -> bool:
    """
    Get user confirmation for downloading all NAIP data.
    
    Displays a warning about the potential size of the download and prompts
    the user to confirm they want to proceed with downloading all available data.
    
    Returns:
        True if user confirms with 'y', False if user cancels with 'n'
        
    Note:
        Will continue prompting until user enters a valid response ('y' or 'n')
    """
    print("\nWARNING: You are about to download ALL available NAIP imagery in NRCS's Box repo!")
    print("This could be a very large amount of data and may take a significant amount of time.")
    print("Are you sure you want to proceed?")
    
    while True:
        response = input("Type 'y' to continue or 'n' to cancel: ").lower().strip()
        if response == 'y':
            return True
        elif response == 'n':
            print("Download cancelled.")
            return False
        else:
            print("Please enter 'y' or 'n'.")


def main() -> NoReturn:
    """
    Main entry point for the NAIP scraper command-line interface.
    
    Parses command-line arguments and executes the appropriate download operations.
    Provides safety confirmations for bulk downloads and handles various error conditions.
    
    Command-line Arguments:
        --year: Specific year to download (optional)
        --state: Specific state abbreviation to download (optional)  
        --output: Output directory for downloads (default: 'data')
        --force: Skip confirmation prompt for bulk downloads
        --list-years: List available years and exit
        --list-states: List available states for given year and exit
        --no-unzip: Skip automatic extraction of zip files
        --overwrite: Overwrite existing files
        
    Examples:
        naip-scraper --year 2020 --state NC
        naip-scraper --list-years
        naip-scraper --list-states 2020
        naip-scraper --force --output ./downloads --overwrite
        
    Exits:
        0: Successful completion
        1: Error during execution or user cancellation
    """
    parser = argparse.ArgumentParser(
        description='Download NAIP imagery from NRCS Box folder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          %(prog)s --year 2025 --state ms    Download MS data for 2025
          %(prog)s --state ms                Download MS data for all years
          %(prog)s --year 2025               Download all states for 2025
          %(prog)s --force                   Download all data without confirmation
          %(prog)s --output ./downloads      Specify custom output directory
          %(prog)s --list-years              List all available years
          %(prog)s --list-states 2020        List states available for 2020
          %(prog)s --no-unzip --year 2020    Download 2020 data but keep zip files
        """)
    )
    
    parser.add_argument(
        '--year', 
        type=int, 
        help='Year to download (if not specified, downloads all available years)'
    )
    
    parser.add_argument(
        '--state', 
        type=str, 
        help='State abbreviation to download (if not specified, downloads all available states)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='data',
        help='Output directory for downloaded files (default: data)'
    )
    
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Skip confirmation prompt when downloading all available data'
    )
    
    parser.add_argument(
        '--list-years',
        nargs='?',
        const=None,
        metavar='STATE',
        help='List available years. Optionally specify state to see years for that state (e.g., --list-years MS)'
    )
    
    parser.add_argument(
        '--list-states',
        nargs='?',
        const=None,
        metavar='YEAR',
        help='List available states. Optionally specify year to see states for that year (e.g., --list-states 2024)'
    )
    
    parser.add_argument(
        '--no-unzip', 
        action='store_true',
        help='Do not automatically unzip downloaded files'
    )
    
    parser.add_argument(
        '--overwrite', 
        action='store_true',
        help='Overwrite existing files in the output directory'
    )
    
    parser.add_argument(
        "--cir-only",
        action="store_true",
        help="Download only CIR composites (<state>_c folders). Superseded by <state>_m if it exists."
    )
    
    parser.add_argument(
        "--rgb-only",
        action="store_true",
        help="Download only RGB composites (<state>_n folders). Superseded by <state>_m if it exists."
    )
    
    args = parser.parse_args()
    
    if args.cir_only and args.rgb_only:
        raise ValueError("Cannot use both --cir-only and --rgb-only at the same time. Please choose one.")
    
    # Initialize scraper
    scraper = NAIPScraper(
        output_dir=args.output, 
        unzip=not args.no_unzip, 
        overwrite=args.overwrite,
        cir_only=args.cir_only,
        rgb_only=args.rgb_only
    )
    
    # Handle list operations
    if args.list_years is not None:
        if args.list_years:  # State was provided
            # Use the same efficient logic as --state command
            state = args.list_years.upper()
            print(f"Getting available years for state {state}...")
            
            # Get all years first (fast)
            all_years = scraper.get_available_years()
            
            # Then check each year for the state (same as download logic)
            available_years = []
            for year in all_years:
                try:
                    year_states = scraper.get_available_states(year)
                    # Case-insensitive state matching
                    if any(s.upper() == state.upper() for s in year_states):
                        available_years.append(year)
                except Exception:
                    continue
            
            if available_years:
                print(f"Found {len(available_years)} years: {', '.join(map(str, available_years))}")
            else:
                print(f"No years found for state {state}")
        else:  # No state provided, list all years
            years = scraper.get_available_years()
            if years:
                print("Available years:")
                for year in years:
                    print(f"  {year}")
            else:
                print("No years found")
        sys.exit(0)
    
    if args.list_states is not None:
        if args.list_states:  # Year was provided
            try:
                year = int(args.list_states)
                states = scraper.get_available_states(year=year)
                if states:
                    print(f"Available states for {year}:")
                    for state in states:
                        print(f"  {state}")
                else:
                    print(f"No states found for year {year}")
            except ValueError:
                print(f"Invalid year: {args.list_states}")
                sys.exit(1)
        else:  # No year provided, list all states
            states = scraper.get_available_states()
            if states:
                print("Available states:")
                for state in states:
                    print(f"  {state}")
            else:
                print("No states found")
        sys.exit(0)
    
    # Check if we're downloading everything and need confirmation
    if args.year is None and args.state is None and not args.force:
        if not get_user_confirmation():
            sys.exit(0)
    
    try:
        print(f"Output directory: {args.output}")
        if args.state is None:
            print("No state specified. Downloading all available states...")
            
            scraper.download_all_states(year=args.year)
        else:
            scraper.download_naip_data(year=args.year, state=args.state)
            
    except KeyboardInterrupt:
        print("\nDownload interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during download: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()