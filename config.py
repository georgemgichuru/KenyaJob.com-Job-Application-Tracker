# KenyaJob.com Job Search Configuration

# Search Criteria
KEYWORDS = ["software developer", "python developer", "web developer"]
LOCATION = "Nairobi"
CATEGORY = "IT & Telecoms"

# Search Parameters
MAX_LISTINGS = 50  # Maximum number of job listings to extract
DAYS_RECENT = 7    # Only show jobs posted in the last X days

# Output Settings
OUTPUT_DIR = "output"
LISTINGS_CSV = "job_listings.csv"
APPLICATIONS_CSV = "applications_tracker.csv"
SCREENSHOTS_DIR = "screenshots"

# Browser Settings
HEADLESS = False  # Set to True to run browser in background
BROWSER_TIMEOUT = 30  # Seconds to wait for page elements

# KenyaJob.com URLs
BASE_URL = "https://www.kenyajob.com"
SEARCH_URL = BASE_URL
