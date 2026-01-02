import json
from pathlib import Path
from eval_classifier import evaluate_classifier
from eval_rag import evaluate_rag

CASES_PATH = Path("evaluation/test_cases.json")
REPORT_JSON = Path("evaluation/report.json")

def main():
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    cls = evaluate_classifier(cases, runs=5)
    rag = evaluate_rag(cases)

    report = {"classifier": cls, "rag": rag}
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"✅ Evaluation completed. Report written to: {REPORT_JSON}")

    avg_groundedness = sum(x["groundedness"] for x in rag) / max(1, len(rag))
    avg_stability = sum(v["stability"] for v in cls.values()) / max(1, len(cls))
    print(f"Avg groundedness: {avg_groundedness:.3f}")
    print(f"Avg classifier stability: {avg_stability:.3f}")

if __name__ == "__main__":
    main()
