import time
from ddgs import DDGS

def search_web(query, retries=3):
    for attempt in range(retries):
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=4):
                    results.append(f"Title: {r['title']}\nContent: {r['body']}\nSource: {r['href']}\n")

            if results:
                return "\n".join(results)

        except Exception as e:
            print(f"[Search retry {attempt+1}] Network blocked... retrying")
            time.sleep(2)

    return "No reliable web results found."