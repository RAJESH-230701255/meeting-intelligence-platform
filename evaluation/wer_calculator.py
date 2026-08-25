def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Calculate Word Error Rate (WER) between a reference string and a hypothesis string.

    Formula: WER = (Substitutions + Deletions + Insertions) / Total Words in Reference
    """
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()

    # Create a distance matrix
    d = [[0 for _ in range(len(hyp_words) + 1)] for _ in range(len(ref_words) + 1)]

    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                cost = 0
            else:
                cost = 1

            d[i][j] = min(
                d[i - 1][j] + 1,      # Deletion
                d[i][j - 1] + 1,      # Insertion
                d[i - 1][j - 1] + cost # Substitution
            )

    wer = d[len(ref_words)][len(hyp_words)] / max(len(ref_words), 1)
    return wer

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Calculate WER")
    parser.add_argument("--ref", type=str, required=True, help="Reference text file")
    parser.add_argument("--hyp", type=str, required=True, help="Hypothesis (system output) text file")

    args = parser.parse_args()

    try:
        with open(args.ref, "r", encoding="utf-8") as f:
            ref_text = f.read()
        with open(args.hyp, "r", encoding="utf-8") as f:
            hyp_text = f.read()

        wer_score = calculate_wer(ref_text, hyp_text)
        print(f"Word Error Rate (WER): {wer_score:.2%}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
