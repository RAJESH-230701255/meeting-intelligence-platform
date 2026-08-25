def calculate_extraction_metrics(expected_items: list, extracted_items: list):
    """
    Calculate Precision, Recall, and F1 Score for extracted action items or decisions.

    This is a simplified exact/partial string matching approach for evaluation.
    In a real research scenario, semantic similarity (e.g., BERTScore) might be used.
    """
    true_positives = 0

    # We copy the extracted list so we can remove matched items and avoid double-counting
    extracted_pool = list(extracted_items)

    for expected in expected_items:
        match_found = False
        for extracted in extracted_pool:
            # Simple substring/inclusion check (case-insensitive)
            # A more robust script would use embedding similarity.
            if expected.lower() in extracted.lower() or extracted.lower() in expected.lower():
                true_positives += 1
                extracted_pool.remove(extracted)
                match_found = True
                break

    false_negatives = len(expected_items) - true_positives
    false_positives = len(extracted_items) - true_positives

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score
    }

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Calculate Extraction Metrics")
    parser.add_argument("--expected", type=str, required=True, help="JSON file with expected items (list of strings)")
    parser.add_argument("--extracted", type=str, required=True, help="JSON file with extracted items (list of strings)")

    args = parser.parse_args()

    try:
        with open(args.expected, "r", encoding="utf-8") as f:
            expected = json.load(f)
        with open(args.extracted, "r", encoding="utf-8") as f:
            extracted = json.load(f)

        results = calculate_extraction_metrics(expected, extracted)
        print(f"Precision: {results['precision']:.2f}")
        print(f"Recall: {results['recall']:.2f}")
        print(f"F1 Score: {results['f1_score']:.2f}")
    except Exception as e:
        print(f"Error: {e}")
