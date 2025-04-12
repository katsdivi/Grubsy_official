def find_business_urls(name: str) -> dict:
    # For now, return hardcoded URLs for testing
    return {
        "yelp": "https://www.yelp.com/biz/starbucks-tempe-50",
        "google": "https://www.google.com/maps/place/Starbucks/@33.4233252,-111.9405825,17z"
    }

# Test it
if __name__ == "__main__":
    print(find_business_urls("Starbucks Mill Avenue"))