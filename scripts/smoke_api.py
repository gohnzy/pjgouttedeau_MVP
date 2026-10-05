import json, requests
s = requests.Session()
s.trust_env = False  # ignore le proxy d'entreprise pour localhost
base = "http://127.0.0.1:8000"
for path in ["/health", "/predict?date=2024-07-14", "/predict?date=2024-01-20",
             "/predict?date=2030-05-01", "/predict?date=bad-date", "/model-info"]:
    r = s.get(base + path, timeout=15)
    print("###", path, "->", r.status_code)
    try:
        print(json.dumps(r.json(), ensure_ascii=False, indent=2)[:600])
    except Exception:
        print(r.text[:300])
    print()
