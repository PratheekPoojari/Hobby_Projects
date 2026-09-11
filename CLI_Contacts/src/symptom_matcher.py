# An industrial/Professional Grade Library for N.L.P tasks.
import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc
from pathlib import Path
import csv

DISEASES_PATH = Path(__file__).resolve().parent.parent / "data" / "diseases.csv"
diseases_csv:list[dict] = []
with open(DISEASES_PATH, "r") as file:
    reader:csv.DictReader = csv.DictReader(file)
    for row in reader:
        diseases_csv.append(row)

# Loads a whole pipeline of N.L.P tasks such as tokenization, POS_Tagging, stemming, lemmatization.
# using nlp("text") runs the entire pipeline, but we only need tokenization.
nlp = spacy.load("en_core_web_sm")

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

for value in diseases_csv:
    disease_patterns:list[Doc] = []
    phrases:list[str] = value["keywords"].split(";")
    for phrase in phrases:
        # Returns a doc object of tokenized input text. Skips all the other functions in the pipeline, unlike "nlp()".
        disease_patterns.append(nlp.make_doc(phrase))
    # matcher -> an instance of the PhraseMatcher class. This is like the 'Dictionary' of Phrases,with a label for each phrase.
    # The attr="LOWER", helps by making it so that every string is in lower case, hence being case insensitive.
    matcher.add(value["code"], disease_patterns)

def allocate_code(symptoms:str) -> str:
    # Calls the entire text pre-processing pipeline on the 'symptoms_text'
    tokenized:Doc = nlp(symptoms)
    # matcher(doc) -> returns a tuple of (match_id, start, end) for every phrase found.
    # match_id -> the hashed version of the 'label'(value["code"]) used. 'start' is the index where the phrase was
    # first matched and 'end' is the last index of that phrase. Use print(matches) for an example.
    matches:list[tuple] = matcher(tokenized)
    tally:dict[str, int] = {}
    for id in matches:
        # nlp.vocab -> spaCy stores the words as integer 'hashes' and has a lookup table 'vocab.strings' for them.
        # This table matches the strings and hashes in both directions. This is done for memory/speed optimization.
        code:str = nlp.vocab.strings[id[0]]
        # dict.get(key, default) -> returns the value of 'key' if it exists, else returns the default value.
        tally[code] = tally.get(code, 0) + 1
    if not tally:
        return "0"
    # Find the highest hit-count among all matched diseases.
    max_hits:int = max(tally.values())
    # Keep only the disease codes that reached that highest hit-count (could be one, could be several tied).
    top_candidates:list[str] = [code for code, count in tally.items() if count == max_hits]
    # Among only the tied top candidates, look up their priority.
    matched_priorities:dict[str, int] = {}
    for row in diseases_csv:
        if row["code"] in top_candidates:
            matched_priorities[row["code"]] = int(row["priority"])
    # Priority now only decides between diseases that are ALREADY tied on hit-count.
    # lambda used instead of matched_priorities.get directly, since .get is an overloaded
    # method and confuses static type checkers (like Pyright) when passed bare into key=.
    winner:str = max(matched_priorities, key=lambda code: matched_priorities[code])
    return winner

# Testing block: only runs when this file is executed directly (python3 symptom_matcher.py),
# not when it's imported elsewhere (e.g. from symptom_matcher import allocate_code in main.py).
if __name__ == "__main__":
    SYMPTOMS_PATH = Path(__file__).resolve().parent.parent / "data" / "symptoms.csv"
    with open(SYMPTOMS_PATH, "r") as file:
        reader:csv.DictReader = csv.DictReader(file)
        for row in reader:
            symptoms_text:str = row["symptoms"]
            alloted_code = allocate_code(symptoms_text)
            print(alloted_code)
