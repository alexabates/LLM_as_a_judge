import json
import requests
from tqdm import tqdm
import time

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "your-model-name"  # e.g., "llama3"
INPUT_FILE = "matched_pairs.json"          # expects objects with article_text, ad_text, article_idx, ad_id
OUTPUT_FILE = "article_ad_pairs_labeled.json"

SYSTEM_PROMPT = """
You are a political ad classifier.

Your task: decide if a political ad is about, directly related to, or clearly responding to a given news article text.

Output rules:
• Output exactly one character: 1 if related, 0 if not related.
• Base your decision ONLY on the provided article text and ad text.
• Ignore IDs, dates, numbers, and any other metadata.
• If you are uncertain, output 0.
• Do not explain or add any other text.

Example of a related pair (should output 1):

Article:
Harris picks Walz for vice president. Kamala Harris chose Minnesota Governor Tim Walz as her vice-presidential running mate on August 6th highlighting his military background, progressive record on reproductive rights, gun safety, climate action, and appeal to working class and Midwestern voters ahead of the 2024 election.

Ad:
BREAKING: Vice President Kamala Harris, the presumptive Democratic nominee in the 2024 presidential race, chose Minnesota Gov. Governor Tim Walz as her running mate.

In this example, the ad is clearly about the same event described in the article, so the correct output is 1.

Example of an unrelated pair (should output 0):

Article:
Trump prolongs uproar over Puerto Rico slur by driving garbage truck around in "total fail" election stunt. Former President Trump staged a publicity stunt in Green Bay on October 30, 2024, emerging from a campaign-branded garbage truck while wearing a safety vest to mock President Biden’s "garbage" remark and draw attention to the Madison Square Garden Puerto Rico slur — an effort widely criticized as tone-deaf and backfiring amid persistent optics challenges.

Ad:
!!Know before you go!! With the election next Tuesday, do you know where your voting precinct is?

In this example, the ad is about finding a voting precint, which is unrelated to the political event in the article, so the correct output is 0.
""".strip()

def ask_ollama(article_text, ad_text, retries=2, backoff=2.0):
    user_prompt = f"""Article:
{article_text}

Ad:
{ad_text}

Response:"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        # Extra safety for determinism:
        "options": {
            "temperature": 0.0
        }
    }

    for attempt in range(retries + 1):
        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=90)
            resp.raise_for_status()
            content = resp.json()["message"]["content"].strip()

            # Normalize any accidental formatting
            content = content.replace("`", "").strip()
            # Accept only a leading 1 or 0
            if content.startswith("1"):
                return 1
            if content.startswith("0"):
                return 0
            # Fallback: be conservative
            return 0
        except Exception as e:
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
            else:
                print(f"Error after retries: {e}")
                return 0  # conservative fallback

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as infile:
        data = json.load(infile)

    for pair in tqdm(data, desc="Labeling pairs"):
        article_text = pair.get("article_text", "")
        ad_text = pair.get("ad_text", "")

        label = ask_ollama(article_text, ad_text)
        # Write to a NEW field
        pair["ollama_label"] = label

    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, indent=2, ensure_ascii=False)

    print(f"Labeled data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
