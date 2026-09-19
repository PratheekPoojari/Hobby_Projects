"""
Implements NLP symptom parsing using spaCy's PhraseMatcher.
Maps unstructured patient symptoms to official disease diagnostic codes.
"""

import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc
from pathlib import Path
import csv

DISEASES_PATH = Path(__file__).resolve().parent.parent / "data" / "diseases.csv"

# Pre-parse the CSV into a lookup dictionary for O(1) access later.
# Format: {"CA": {"keywords": "lump;mass", "priority": 6}, ...}
diseases_db: dict[str, dict] = {}
with open(DISEASES_PATH, "r", encoding="utf-8") as file:
    for row in csv.DictReader(file):
        diseases_db[row["code"]] = {
            "keywords": row["keywords"],
            "priority": int(row["priority"])
        }

# OPTIMIZATION: We only need tokenization for PhraseMatcher with attr="LOWER".
# Disabling the tagger, parser, ner, and lemmatizer cuts inference time massively
# on 750-word symptom inputs, saving CPU cycles.
nlp = spacy.load("en_core_web_sm", disable=["tagger", "parser", "ner", "lemmatizer", "textcat"])

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

for code, data in diseases_db.items():
    disease_patterns: list[Doc] = []
    phrases: list[str] = data["keywords"].split(";")
    for phrase in phrases:
        disease_patterns.append(nlp.make_doc(phrase))
    matcher.add(code, disease_patterns)

def allocate_code(symptoms: str) -> str:
    # Because we disabled the heavy pipeline components, this is now a highly
    # optimized pure-tokenization step.
    tokenized: Doc = nlp(symptoms)
    matches: list[tuple] = matcher(tokenized)
    
    tally: dict[str, int] = {}
    for match_id, start, end in matches:
        code: str = nlp.vocab.strings[match_id]
        tally[code] = tally.get(code, 0) + 1
        
    if not tally:
        return "0"
        
    # Find the highest hit-count among all matched diseases.
    max_hits: int = max(tally.values())
    
    # Keep only the disease codes that reached that highest hit-count
    top_candidates: list[str] = [code for code, count in tally.items() if count == max_hits]
    
    # Priority now only decides between diseases that are ALREADY tied on hit-count.
    # O(1) lookup against our diseases_db instead of looping the CSV list.
    winner: str = max(top_candidates, key=lambda code: diseases_db[code]["priority"])
    return winner

