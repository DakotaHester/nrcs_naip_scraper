# NRCS NAIP Scraper

A Python package for downloading NAIP (National Agriculture Imagery Program) imagery data from the USDA NRCS Box folder. This tool provides both a command-line interface and programmatic API for efficiently downloading aerial imagery data organized by year and state.

## Installation

### From Source
```bash
git clone https://github.com/DakotaHester/nrcs_naip_scraper
cd nrcs_naip_scraper
pip install -e .
```

### Dependencies
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing  
- `tqdm` - Progress bars

## Quick Start

### Command Line Usage

```bash
# Download North Carolina data for 2024
naip-scraper --year 2024 --state NC

# Download all states for 2023
naip-scraper --year 2023

# Download all years for Mississippi
naip-scraper --state MS

# List available years
naip-scraper --list-years

# List available states for 2024
naip-scraper --list-states 2024
```

### Python API Usage

```python
from nrcs_naip_scraper import NAIPScraper

# Initialize scraper
scraper = NAIPScraper(output_dir="./naip_data")

# Download specific state and year
scraper.download_naip_data(year=2024, state="NC")

# Get available years
years = scraper.get_available_years()
print(f"Available years: {years}")

# Get available states for a year
states = scraper.get_available_states(2024)
print(f"States for 2024: {states}")
```

## Command Line Reference

### Basic Usage
```bash
naip-scraper [OPTIONS]
```

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--year YEAR` | Specific year to download | `--year 2024` |
| `--state STATE` | State abbreviation (2-letter) | `--state NC` |
| `--output DIR` | Output directory | `--output ./downloads` |
| `--list-years [STATE]` | List available years, optionally for specific state | `--list-years` or `--list-years MS` |
| `--list-states [YEAR]` | List available states, optionally for specific year | `--list-states` or `--list-states 2024` |
| `--no-unzip` | Keep zip files without extracting | `--no-unzip` |
| `--force` | Skip confirmation for bulk downloads | `--force` |

### Example Commands

#### Discovery Commands
```bash
# See what years are available across all states
naip-scraper --list-years

# See what years are available for Mississippi specifically
naip-scraper --list-years MS

# See what years are available for North Carolina
naip-scraper --list-years NC

# See what states are available across all years
naip-scraper --list-states

# See what states are available for 2024
naip-scraper --list-states 2024

# See what states are available for 2023
naip-scraper --list-states 2023
```

#### Targeted Downloads
```bash
# Download North Carolina 2024 data
naip-scraper --year 2024 --state NC

# Download California 2023 data  
naip-scraper --year 2023 --state CA

# Download Texas 2022 data
naip-scraper --year 2022 --state TX

# Download Virginia 2024 data to custom directory
naip-scraper --year 2024 --state VA --output ./virginia_naip
```

#### Bulk Downloads
```bash
# Download all states for 2024 (will prompt for confirmation)
naip-scraper --year 2024

# Download all states for 2023 without confirmation
naip-scraper --year 2023

# Download all years for North Carolina
naip-scraper --state NC

# Download all available data (use with caution!)
naip-scraper --force
```

#### Advanced Options
```bash
# Download without auto-extracting zip files
naip-scraper --year 2024 --state NC --no-unzip

# Download to specific directory
naip-scraper --year 2024 --state NC --output /path/to/custom/directory

# Download all 2024 data, keep zips, custom output
naip-scraper --year 2024 --no-unzip --output ./naip_archives
```
