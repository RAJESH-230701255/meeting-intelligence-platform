# Research Evaluation

This directory contains scripts and guidelines for measuring the performance of the AI-Powered Meeting Intelligence Platform, intended for research paper experimentation.

## Dataset Preparation
To conduct valid experiments, prepare a dataset consisting of:
1. **Audio Samples**: Various meeting lengths and audio qualities (e.g., `.wav` or `.mp3`).
2. **Reference Transcripts**: Human-verified, 100% accurate transcripts corresponding to the audio samples.
3. **Reference Annotations**: Human-verified lists of expected Action Items and Decisions for each meeting.

## Evaluation Scripts

### 1. Word Error Rate (WER)
Calculates the accuracy of the Whisper Speech-to-Text extraction.
```bash
python evaluation/wer_calculator.py --ref path/to/reference.txt --hyp path/to/system_output.txt
```

### 2. Extraction Metrics
Calculates Precision, Recall, and F1 Score for action items and decisions.
```bash
python evaluation/extraction_metrics.py --expected path/to/expected.json --extracted path/to/system_output.json
```
**JSON Format:** Both files should contain a flat JSON list of strings (e.g., `["Task 1", "Task 2"]`).

## Collecting Processing Time
Processing time can be evaluated manually or extracted from the application logs (timestamps of upload completion vs. AI completion).
- **Transcription Time**: The duration required to process audio into text.
- **AI Processing Time**: The duration required for the LLM to analyze the text.

## Note on Experimental Results
DO NOT fabricate experimental results. Run the scripts strictly on your collected dataset to generate valid metrics for your final year project paper.
