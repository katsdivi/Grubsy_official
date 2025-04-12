from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import asyncio
import requests

# Adjust these imports to match your project structure.
from .google_trigger import run_node_scraper
from .insights import generate_actionable_insights, generate_actionable_summaries
from .url_finder import resolve_input_to_place_url

app = FastAPI()

class ReviewRequest(BaseModel):
    url: str

@app.get("/")
def home():
    return {"message": "Use POST /analyze with a Google Maps URL to generate a business summary."}

@app.post("/analyze")
async def analyze_reviews(request: ReviewRequest):
    input_url = request.url
    try:
        # Resolve the input (business name, raw query URL, or detailed URL)
       # processed_url = await resolve_input_to_place_url(input_url)
        print(f"🔍 Scraping: {input_url}")
        
        # Step 1: Scrape Reviews (run_node_scraper is synchronous, so use asyncio.to_thread)
        reviews, ratings = await asyncio.to_thread(run_node_scraper, input_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing URL or scraping reviews: {e}")
    
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this URL.")
    
    try:
        # Step 2: NLP Insights from the scraped reviews
        latest_reviews = reviews[:5]  # or sort by timestamp
        weighted_reviews = reviews + latest_reviews * 3

        insights, strengths = generate_actionable_insights(weighted_reviews)
        latest_reviews = reviews[:5]  # Or reviews[:5] depending on sort order

        print("🆕 Latest 5 Reviews:")
        for i, review in enumerate(latest_reviews, start=1):
            print(f"{i}. {review}")

        recommendations = generate_actionable_summaries(insights)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing review insights: {e}")
    
    # Build a summary structure for further processing
    summary_input = {
        "strengths": strengths,
        "insights": insights,
        "recommendations": recommendations
    }
    
    # Step 3: Construct an AI prompt for Mistral via Ollama
    prompt = f"""
You are an AI assistant summarizing customer review analysis for a business owner.

Given the following structured review data:
{json.dumps(summary_input, indent=2)}

Please return your output in this clean JSON format:

{{
  "qualities": ["short, clear bullet points of what customers liked..."],
  "weaknesses": ["short, clear bullet points of what customers disliked..."],
  "recommendations": ["clear, actionable suggestions the business should consider..."]
}}

✦ Be concise and professional.  
✦ Do not mention sentiment scores or quote the keywords.  
✦ Avoid repeating similar points.  
✦ Keep bullet points under 20 words if possible.
"""
    mistral_payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }
    
    # Step 4: Call the Ollama API and post-process the response.
    try:
        ollama_response = requests.post("http://localhost:11434/api/generate", json=mistral_payload)
        if ollama_response.status_code != 200:
            raise Exception(f"Ollama error: {ollama_response.text}")
        
        ai_response = ollama_response.json().get("response", "")
        
        # Attempt to parse the AI response as JSON.
        try:
            summary = json.loads(ai_response)
            # Utility function to clean up bullet lists.
            def clean_list(items):
                return [item.strip().replace("\n", " ").replace("  ", " ") for item in items]
            
            from fastapi.responses import FileResponse
            import tempfile

            cleaned_output = {
                "avg_rating": sum(ratings) / len(ratings),
                "qualities": clean_list(summary.get("qualities", [])),
                "weaknesses": clean_list(summary.get("weaknesses", [])),
                "recommendations": clean_list(summary.get("recommendations", []))
            }

    # Write to a temporary JSON file
            with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as tmp_file:
                json.dump(cleaned_output, tmp_file, indent=2)
                tmp_file_path = tmp_file.name

            # Send the file as a response
            return FileResponse(
                path=tmp_file_path,
                filename="summary_output.json",
                media_type="application/json"
            )

        except json.JSONDecodeError:
            # If the AI returns plain text, just return it.
            return {"ai_summary": ai_response.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate AI summary: {e}")
