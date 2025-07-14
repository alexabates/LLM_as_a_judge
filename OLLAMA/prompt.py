import ollama
import json

# Load article content from the scraped JSON file
with open("Article_Contents_Output.json", "r") as f:
    articles = json.load(f)

results = []

for idx, article in enumerate(articles):
    title = article['title']
    content = article['content']
    date = article.get('publish_date', 'Unknown')
    
    if not content.strip():
        print(f"⚠️ Skipping article {idx+1} (no content)")
        continue

    print(f"Extracting keywords from: {title[:50]}...")

    prompt = f"""Extract the 5 most important keywords from the following news article. 
    Return the keywords as a JSON list of strings.
    Article: \"\"\"{content}\"\"\"
    """

    try:
        response = ollama.chat(
            model='llama3.2',  # or another local model you've downloaded
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        output = response['message']['content'].strip()
        try:
            keywords = json.loads(output)  # parse LLM output into list
        except json.JSONDecodeError:
            keywords = [output]  # fallback

    except Exception as e:
        print(f"Failed to process article '{title}': {e}")
        keywords = []

    results.append({
        'title': title,
        'publish_date': date,
        'keywords': keywords
    })

# Save results to new JSON file
with open("Extracted_Keywords.json", "w") as f:
    json.dump(results, f, indent=2)

print("Done! Keywords saved to Extracted_Keywords.json")