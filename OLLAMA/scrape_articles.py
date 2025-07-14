import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import json

# Load your CSV file (make sure it's in the same folder or provide the correct path)
df = pd.read_csv('Articles.csv')  # Update path if needed

def extract_article_data(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = "\n".join([p.get_text() for p in paragraphs])

        date = None
        for meta_tag in soup.find_all('meta'):
            if meta_tag.get('property') in ['article:published_time', 'og:pubdate'] or \
               meta_tag.get('name') in ['pubdate', 'publishdate', 'date']:
                date = meta_tag.get('content')
                break

        return text.strip(), date
    except Exception as e:
        return "", f"ERROR: {str(e)}"

results = []

for idx, row in df.iterrows():
    title = row['Article_Title']
    url = row['URL']

    print(f"🔍 Scraping: {title}")
    content, publish_date = extract_article_data(url)

    results.append({
        'title': title,
        'url': url,
        'publish_date': publish_date,
        'content': content
    })

    time.sleep(random.uniform(1, 2))  # Be polite to servers

# Save to JSON
with open('Article_Contents_Output.json', 'w') as f:
    json.dump(results, f, indent=2)

print("✅ Done! File saved as Article_Contents_Output.json")