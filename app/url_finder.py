from playwright.async_api import async_playwright
import urllib.parse
import re

async def get_detailed_place_url(place_name):
    """
    Given a business name, search on Google Maps and return a detailed URL
    from the first result.
    """
    query = urllib.parse.quote(place_name)
    search_url = f"https://www.google.com/maps/search/?api=1&query={query}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(search_url)
        
        # Generic selector for a place link.
        selector = 'a.hfpxzc[aria-label][href^="https://www.google.com/maps/place/"]'
        await page.wait_for_selector(selector, timeout=15000)
        element = page.locator(selector).first
        link = await element.get_attribute("href")
        await browser.close()
        
        if link:
            return link
        else:
            raise Exception("Could not extract href from the search result.")

def convert_to_place_url(raw_url):
    """
    Convert a raw Google Maps query URL (maps?q=...) into a canonical
    Place URL of the form:
      https://www.google.com/maps/place/?q=place_id:<PLACE_ID>
    """
    match = re.search(r"maps\?q=[^,]+,[^,]+,([^&]+)", raw_url)
    if match:
        place_id = match.group(1)
        return f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    return "Invalid URL format."

def is_google_maps_url(input_str):
    """
    Returns True if the input string appears to be a Google Maps URL.
    """
    return "maps.google.com" in input_str or "www.google.com/maps" in input_str

async def get_restaurant_name(place_url):
    """
    Given a canonical place URL (for example, .../maps/place/?q=place_id:...),
    load the page and extract the restaurant's name.
    
    Adjust the selector below if needed.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(place_url)
        try:
            # Adjust the selector based on the current DOM; here we use a generic h1.
            await page.wait_for_selector("h1", timeout=15000)
            name = await page.locator("h1").first.inner_text()
        except Exception as e:
            await browser.close()
            raise Exception("Could not extract restaurant name from the page.") from e
        await browser.close()
        return name.strip()

async def resolve_input_to_place_url(input_str):
    """
    Resolves the input into a detailed Google Maps URL.
    
    - If the input is a raw query URL (contains "maps?q="):
        1. Convert it to a canonical place‑ID URL.
        2. Load that URL to extract the restaurant name.
        3. Use the restaurant name to perform a new search (as with "Starbucks at mill").
    - If the input is already a place‑ID URL (contains "place_id:"), do the same.
    - If the input is any other Google Maps URL, return it as-is.
    - Otherwise, assume it's a business name and perform a search.
    """
    if "maps?q=" in input_str:
        # Convert the raw query URL.
        canonical_url = convert_to_place_url(input_str)
        if canonical_url.startswith("Invalid"):
            return canonical_url
        # Extract the restaurant name from the canonical URL.
        restaurant_name = await get_restaurant_name(canonical_url)
        print("Extracted Restaurant Name:", restaurant_name)
        # Now, perform a search by restaurant name.
        detailed_url = await get_detailed_place_url(restaurant_name)
        return detailed_url
    elif "place_id:" in input_str:
        # If input already contains a place_id, extract the restaurant name.
        restaurant_name = await get_restaurant_name(input_str)
        print("Extracted Restaurant Name:", restaurant_name)
        detailed_url = await get_detailed_place_url(restaurant_name)
        return detailed_url
    elif is_google_maps_url(input_str):
        # If it's already a detailed URL, return as-is.
        return input_str
    else:
        # Otherwise, assume it's a business name and search directly.
        return await get_detailed_place_url(input_str)
