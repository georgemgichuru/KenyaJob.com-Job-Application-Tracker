import os
import time
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import config

class KenyaJobTracker:
    def __init__(self):
        self.driver = None
        self.job_listings = []
        self.applications = []
        self.setup_directories()
        
    def setup_directories(self):
        """Create output directories if they don't exist"""
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        os.makedirs(config.SCREENSHOTS_DIR, exist_ok=True)
        
    def setup_driver(self):
        """Set up Chrome WebDriver with options"""
        chrome_options = Options()
        if config.HEADLESS:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1200,800")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(config.BROWSER_TIMEOUT)
        
    def navigate_to_search(self):
        """Navigate to KenyaJob.com homepage"""
        print("Navigating to KenyaJob.com homepage...")
        self.driver.get(config.SEARCH_URL)
        
        # Wait for search form to load - wait for keywords input field
        WebDriverWait(self.driver, config.BROWSER_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Keywords']"))
        )
        
    def perform_search(self):
        """Fill out and submit search form"""
        print("Performing job search...")
        
        try:
            # Fill keywords
            keyword_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Keywords']")
            keyword_input.clear()
            keyword_input.send_keys(" ".join(config.KEYWORDS))
            
            # Skipping region and category selection due to dynamic/custom dropdowns
            
            # Submit search by clicking the search button (try multiple selectors)
            # Based on debug output, we need to find the actual search button
            # Let's try more specific selectors and also look for input elements
            search_button_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button.btn-primary",
                "button.btn",
                "input.btn",
                "input[value*='Search']",
                "input[value*='Find']",
                "input[value*='Go']",
                "button[class*='search']",
                "input[class*='search']"
            ]
            
            search_button = None
            found_selector = None
            selector_type = "CSS"
            
            # First try CSS selectors
            for selector in search_button_selectors:
                try:
                    search_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_button:
                        found_selector = selector
                        print(f"Found search button using CSS selector: {selector}")
                        break
                except Exception as e:
                    print(f"CSS selector '{selector}' failed: {e}")
                    continue
            
            # If CSS selectors fail, try XPath selectors for text content
            if not search_button:
                xpath_selectors = [
                    "//button[contains(text(), 'Search')]",
                    "//button[contains(text(), 'Find')]",
                    "//input[@type='submit' and contains(@value, 'Search')]",
                    "//input[@type='submit' and contains(@value, 'Find')]",
                    "//input[@type='button' and contains(@value, 'Search')]",
                    "//input[@type='button' and contains(@value, 'Find')]"
                ]
                
                for selector in xpath_selectors:
                    try:
                        search_button = self.driver.find_element(By.XPATH, selector)
                        if search_button:
                            found_selector = selector
                            selector_type = "XPath"
                            print(f"Found search button using XPath selector: {selector}")
                            break
                    except Exception as e:
                        print(f"XPath selector '{selector}' failed: {e}")
                        continue
            
            if not search_button:
                # Debug: print all buttons on the page to help identify the correct selector
                print("Debug: Listing all buttons on the page...")
                try:
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for i, button in enumerate(all_buttons):
                        try:
                            text = button.text.strip()
                            aria_label = button.get_attribute("aria-label") or ""
                            title = button.get_attribute("title") or ""
                            class_name = button.get_attribute("class") or ""
                            print(f"Button {i+1}: text='{text}', aria-label='{aria_label}', title='{title}', class='{class_name}'")
                        except:
                            print(f"Button {i+1}: Could not get details")
                except Exception as debug_e:
                    print(f"Debug error: {debug_e}")
                
                raise Exception("Search button not found with any known selector. Check debug output above.")
            
            search_button.click()
            
            # Wait for search results page to load - wait for job cards with longer timeout
            WebDriverWait(self.driver, config.BROWSER_TIMEOUT * 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-card, .job-listing, .job-item, [class*='job'], [class*='listing']"))
            )
            
        except Exception as e:
            print(f"Error during search: {e}")
            self.capture_screenshot("search_error")
            raise
            
    def extract_job_listings(self):
        """Extract job listings from search results"""
        print("Extracting job listings...")
        
        try:
            # Try multiple selectors for job listing elements
            job_selectors = [
                ".job-card",
                ".job-listing",
                ".job-item",
                ".job",
                "[class*='job']",
                "[class*='listing']",
                "div[data-job]"
            ]
            
            job_elements = []
            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        job_elements = elements
                        print(f"Found {len(job_elements)} job elements using selector: {selector}")
                        break
                except:
                    continue
            
            if not job_elements:
                print("No job elements found with any selector")
                self.capture_screenshot("no_jobs_found")
                return
            
            for i, job_element in enumerate(job_elements[:config.MAX_LISTINGS]):
                try:
                    job_data = self.extract_job_details(job_element)
                    if job_data and self.is_recent_job(job_data):
                        self.job_listings.append(job_data)
                        print(f"Extracted job {i+1}: {job_data.get('title', 'Unknown')}")
                        
                except Exception as e:
                    print(f"Error extracting job {i+1}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error extracting job listings: {e}")
            self.capture_screenshot("extraction_error")
            
            
    def extract_job_details(self, job_element):
        """Extract details from a single job listing element"""
        try:
            job_data = {
                'title': self.get_text_safe(job_element, "h3.job-title, h2.job-title, a.job-title"),
                'company': self.get_text_safe(job_element, ".company-name, .employer-name"),
                'location': self.get_text_safe(job_element, ".job-location"),
                'posted_date': self.get_text_safe(job_element, ".posted-date"),
                'description': self.get_text_safe(job_element, ".job-description, .description"),
                'url': self.get_attribute_safe(job_element, "a.job-title", "href"),
                'extracted_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Clean and process data
            job_data['url'] = config.BASE_URL + job_data['url'] if job_data['url'] and not job_data['url'].startswith('http') else job_data['url']
            
            return job_data
            
        except Exception as e:
            print(f"Error extracting job details: {e}")
            return None
            
    def is_recent_job(self, job_data):
        """Check if job was posted within the specified recent days"""
        if not job_data.get('posted_date'):
            return True
            
        posted_date = job_data['posted_date'].lower()
        current_date = datetime.now()
        
        # Parse relative dates like "2 days ago", "1 week ago", etc.
        if 'hour' in posted_date or 'today' in posted_date:
            return True
        elif 'day' in posted_date:
            try:
                days_ago = int(''.join(filter(str.isdigit, posted_date)))
                return days_ago <= config.DAYS_RECENT
            except:
                return True
        elif 'week' in posted_date:
            try:
                weeks_ago = int(''.join(filter(str.isdigit, posted_date)))
                return weeks_ago == 1  # Only show jobs from this week
            except:
                return False
        else:
            # For absolute dates, we'd need more complex parsing
            return True
            
    def get_text_safe(self, element, selector):
        """Safely get text from element with selector"""
        try:
            target = element.find_element(By.CSS_SELECTOR, selector)
            return target.text.strip()
        except:
            return ""
            
    def get_attribute_safe(self, element, selector, attribute):
        """Safely get attribute from element with selector"""
        try:
            target = element.find_element(By.CSS_SELECTOR, selector)
            return target.get_attribute(attribute)
        except:
            return ""
            
    def track_application(self, job_data, status="Not Applied"):
        """Track a job application"""
        application = {
            'job_title': job_data.get('title', ''),
            'company': job_data.get('company', ''),
            'location': job_data.get('location', ''),
            'job_url': job_data.get('url', ''),
            'status': status,
            'applied_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status == "Applied" else "",
            'notes': "",
            'tracked_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.applications.append(application)
        
    def save_to_csv(self):
        """Save job listings and applications to CSV files"""
        try:
            # Save job listings
            if self.job_listings:
                listings_df = pd.DataFrame(self.job_listings)
                listings_path = os.path.join(config.OUTPUT_DIR, config.LISTINGS_CSV)
                listings_df.to_csv(listings_path, index=False)
                print(f"Saved {len(self.job_listings)} job listings to {listings_path}")
            
            # Save applications
            if self.applications:
                apps_df = pd.DataFrame(self.applications)
                apps_path = os.path.join(config.OUTPUT_DIR, config.APPLICATIONS_CSV)
                apps_df.to_csv(apps_path, index=False)
                print(f"Saved {len(self.applications)} applications to {apps_path}")
                
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            
    def capture_screenshot(self, filename):
        """Capture screenshot for debugging"""
        try:
            screenshot_path = os.path.join(config.SCREENSHOTS_DIR, f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            self.driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            
    def run(self):
        """Main execution method"""
        try:
            self.setup_driver()
            self.navigate_to_search()
            self.perform_search()
            self.extract_job_listings()
            
            # Track all extracted jobs as "Not Applied" initially
            for job in self.job_listings:
                self.track_application(job, "Not Applied")
                
            self.save_to_csv()
            print("Job tracking completed successfully!")
            
        except Exception as e:
            print(f"Error during execution: {e}")
            self.capture_screenshot("execution_error")
            
        finally:
            if self.driver:
                self.driver.quit()
                
if __name__ == "__main__":
    tracker = KenyaJobTracker()
    tracker.run()
