import collections
import requests

CLASSIFY_URL = "http://localhost:8002/classify"

def evaluate_classifier(cases, runs=5, timeout=30):
    """Runs /classify multiple times per case and measures output stability."""
    results = {}

    for case in cases:
        outputs = []
        for _ in range(runs):
            r = requests.post(CLASSIFY_URL, json={"text": case["text"]}, timeout=timeout)
            r.raise_for_status()
            j = r.json()
            outputs.append((j.get("product_area"), j.get("urgency")))

        counter = collections.Counter(outputs)
        most_common, count = counter.most_common(1)[0]
        stability = count / runs

        results[case["id"]] = {
            "most_common": {"product_area": most_common[0], "urgency": most_common[1]},
            "stability": stability,
            "distribution": {f"{k[0]}|{k[1]}": v for k, v in counter.items()},
        }

    return results
