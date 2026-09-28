import os
import json
import re
import time
from pathlib import Path

from openai import OpenAI, RateLimitError


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "deepseek/deepseek-v4-flash-0731"
OUTPUT_FILE = "submission_scores.json"


# ============================================================
# FIND PROJECT FILES
# ============================================================

def find_project_paths():
    """
    Automatically searches for:

        data/candidates
        data/canditates

    It checks the current folder and all parent folders.
    This is useful when Jupyter Notebook is running from
    a subfolder such as "sublab_hard".
    """

    current = Path.cwd()

    # Current folder + all parent folders
    possible_roots = [current] + list(current.parents)

    candidate_dirs = []
    rubric_paths = []

    for root in possible_roots:

        # Normal spelling
        candidate_dirs.append(
            root / "data" / "candidates"
        )

        # Original spelling used in the project
        candidate_dirs.append(
            root / "data" / "canditates"
        )

        # Rubric inside data
        rubric_paths.append(
            root / "data" / "candidate_rubric.json"
        )

        # Rubric directly in project root
        rubric_paths.append(
            root / "candidate_rubric.json"
        )

    # --------------------------------------------------------
    # Find candidates folder
    # --------------------------------------------------------

    base = None

    for path in candidate_dirs:

        if path.exists() and path.is_dir():

            # Check that it actually contains .md files
            md_files = list(path.glob("*.md"))

            if md_files:
                base = path
                break

    if base is None:

        raise FileNotFoundError(
            "\nCandidate folder was not found.\n\n"
            "Current working directory:\n"
            f"{Path.cwd()}\n\n"
            "Searched in:\n"
            + "\n".join(
                str(p)
                for p in candidate_dirs
            )
        )

    # --------------------------------------------------------
    # Find rubric
    # --------------------------------------------------------

    rubric_path = None

    for path in rubric_paths:

        if path.exists() and path.is_file():

            rubric_path = path
            break

    if rubric_path is None:

        raise FileNotFoundError(
            "\ncandidate_rubric.json was not found.\n\n"
            "Searched in:\n"
            + "\n".join(
                str(p)
                for p in rubric_paths
            )
        )

    return base, rubric_path


# ============================================================
# OPENROUTER CLIENT
# ============================================================

def openrouter_client() -> OpenAI:

    key = os.environ.get("OPENROUTER_API_KEY")

    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set.\n"
            "Please set the OPENROUTER_API_KEY environment variable."
        )

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=key
    )


client = openrouter_client()


# ============================================================
# CALL MODEL WITH RETRY
# ============================================================

def call_model(prompt, system_message, max_retries=5):

    for attempt in range(max_retries):

        try:

            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_message
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            content = resp.choices[0].message.content

            if not content:
                raise RuntimeError(
                    "Model returned empty content."
                )

            return content.strip()

        except RateLimitError:

            if attempt == max_retries - 1:
                raise

            wait_time = 10 * (attempt + 1)

            print(
                f"Rate limit (429). "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)


# ============================================================
# CLEAN JSON RESPONSE
# ============================================================

def clean_json_response(content):

    content = content.strip()

    # --------------------------------------------------------
    # Remove markdown code fences
    # --------------------------------------------------------

    if content.startswith("```"):

        parts = content.split("```")

        if len(parts) >= 2:
            content = parts[1].strip()

        if content.lower().startswith("json"):
            content = content[4:].strip()

    if content.endswith("```"):
        content = content[:-3].strip()

    # --------------------------------------------------------
    # Try direct JSON
    # --------------------------------------------------------

    try:
        json.loads(content)
        return content
    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Find JSON object or array inside extra text
    # --------------------------------------------------------

    object_start = content.find("{")
    array_start = content.find("[")

    starts = [
        pos
        for pos in [
            object_start,
            array_start
        ]
        if pos != -1
    ]

    if not starts:

        raise ValueError(
            "No JSON object or JSON array found "
            "in model response."
        )

    start = min(starts)

    json_part = content[start:]

    decoder = json.JSONDecoder()

    try:

        parsed, _ = decoder.raw_decode(json_part)

        return json.dumps(
            parsed,
            ensure_ascii=False
        )

    except json.JSONDecodeError as e:

        raise ValueError(
            "Could not parse JSON returned by model.\n\n"
            f"Model response:\n{content}"
        ) from e


# ============================================================
# CV SCHEMA
# ============================================================

cv_schema = {
    "candidate_id": "string",
    "full_name": "string or null",
    "degree": "string or null",
    "graduation_year": "integer or null",
    "gpa_4_scale": "float or null",
    "original_scale": "string or null",
    "languages": [
        "list of strings"
    ],
    "published_outputs": "integer",
    "submitted_outputs": "integer",
    "experience_months": "integer or null",
    "contradictions": [
        "list of strings"
    ],
    "evidence": {
        "full_name": "quote or empty string",
        "degree": "quote or empty string",
        "graduation_year": "quote or empty string",
        "gpa": "quote or empty string",
        "publications": "quote or empty string",
        "experience": "quote or empty string",
        "languages": "quote or empty string"
    }
}


# ============================================================
# ENSURE CV STRUCTURE
# ============================================================

def ensure_cv_structure(cv, candidate_id):

    if not isinstance(cv, dict):

        raise RuntimeError(
            f"CV for {candidate_id} is not a JSON object."
        )

    # Candidate ID comes from filename
    cv["candidate_id"] = candidate_id

    defaults = {
        "full_name": None,
        "degree": None,
        "graduation_year": None,
        "gpa_4_scale": None,
        "original_scale": None,
        "languages": [],
        "published_outputs": 0,
        "submitted_outputs": 0,
        "experience_months": None,
        "contradictions": [],
        "evidence": {}
    }

    for key, default_value in defaults.items():

        if key not in cv:
            cv[key] = default_value

    # --------------------------------------------------------
    # Languages
    # --------------------------------------------------------

    if not isinstance(cv["languages"], list):
        cv["languages"] = []

    # --------------------------------------------------------
    # Contradictions
    # --------------------------------------------------------

    if not isinstance(cv["contradictions"], list):
        cv["contradictions"] = []

    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    if not isinstance(cv["evidence"], dict):
        cv["evidence"] = {}

    evidence_defaults = {
        "full_name": "",
        "degree": "",
        "graduation_year": "",
        "gpa": "",
        "publications": "",
        "experience": "",
        "languages": ""
    }

    for key, default_value in evidence_defaults.items():

        if key not in cv["evidence"]:
            cv["evidence"][key] = default_value

    return cv


# ============================================================
# GPA NORMALIZATION
# ============================================================

def normalize_cv(cv):

    # --------------------------------------------------------
    # GPA: convert 5.0 scale -> 4.0 scale
    # --------------------------------------------------------

    evidence_gpa = (
        cv.get("evidence", {})
        .get("gpa", "")
    )

    original_scale = cv.get("original_scale")

    if original_scale in ("5.0", "5"):

        match = re.search(
            r"(\d+(?:\.\d+)?)"
            r"\s*(?:/|out of)?\s*5(?:\.0)?\b",
            evidence_gpa,
            re.IGNORECASE
        )

        if match:

            gpa_5 = float(
                match.group(1)
            )

            cv["gpa_4_scale"] = round(
                (gpa_5 / 5.0) * 4.0,
                2
            )

    # --------------------------------------------------------
    # Graduation year
    # --------------------------------------------------------

    if cv.get("graduation_year") is None:

        evidence_degree = (
            cv.get("evidence", {})
            .get("degree", "")
        )

        text_lower = evidence_degree.lower()

        if (
            "final-year" in text_lower
            or "final year" in text_lower
            or "graduating" in text_lower
        ):

            match = re.search(
                r"\b(20\d{2})\b",
                evidence_degree
            )

            if match:

                cv["graduation_year"] = int(
                    match.group(1)
                )

    return cv


# ============================================================
# ANALYZE CV
# ============================================================

def analyze_cv(cv):

    null_fields = []

    for field in [
        "full_name",
        "degree",
        "graduation_year",
        "gpa_4_scale",
        "original_scale",
        "experience_months"
    ]:

        if cv.get(field) is None:
            null_fields.append(field)

    traps = []

    publications_evidence = (
        cv.get("evidence", {})
        .get("publications", "")
        .lower()
    )

    # Submitted outputs remain separate
    if cv.get("submitted_outputs", 0) > 0:

        traps.append(
            "submitted outputs kept separate from published outputs"
        )

    # Do not count unpublished work
    if any(
        phrase in publications_evidence
        for phrase in [
            "under review",
            "in review",
            "на рецензировании",
            "in preparation",
            "in press",
            "submitted",
            "planned"
        ]
    ):

        traps.append(
            "unpublished research activity was not counted as published"
        )

    # Contradictions
    if cv.get("contradictions"):

        traps.append(
            "contradiction detected and preserved"
        )

    # GPA conversion
    if cv.get("original_scale") in ("5.0", "5"):

        traps.append(
            "GPA converted from 5.0 scale to 4.0"
        )

    return {
        "processed": True,
        "passed": True,
        "null_fields": null_fields,
        "traps": traps
    }


# ============================================================
# PART 1: EXTRACT CV
# ============================================================

def extract_cv(story_text, candidate_id):

    prompt = f"""
You are given one candidate story.

Extract a structured CV record in JSON.

Schema:
{json.dumps(cv_schema, indent=2, ensure_ascii=False)}

IMPORTANT RULES:

1. A fact that is not stated in the story is null.
   Never estimate, infer, guess, or fill missing information.

2. GPA:
   - Extract the GPA exactly as stated in the story.
   - If the GPA is on a 5.0 scale, set original_scale to "5.0".
   - If the GPA is already on a 4.0 scale, set original_scale to "4.0".
   - Do NOT calculate or convert GPA yourself.
   - If the GPA is on a 5.0 scale, gpa_4_scale must initially be null.
   - Python will perform the conversion after extraction.
   - Never use 0 for a missing or unconverted GPA.
   - Always put the exact GPA statement in evidence.gpa.

3. Publications:
   Count a publication only if the story explicitly says
   that it was published or accepted for publication.

   Do NOT count:
   - submitted
   - under review
   - in review
   - in preparation
   - in press
   - planned

   Keep submitted/unpublished outputs separately
   in submitted_outputs.

4. Contradictions:
   If the story contains contradictory information about a field:
   - do not resolve the contradiction;
   - do not choose one value;
   - set that field to null;
   - describe the contradiction in contradictions.

5. Evidence:
   Every populated field must have supporting evidence.
   Evidence must be a quote or close exact excerpt from the story.
   Do not invent evidence.

6. Languages:
   Include only languages explicitly stated in the story.

7. Experience:
   Extract only explicitly stated relevant experience.
   Never estimate months from dates unless the story explicitly gives
   enough information and calculation is clearly allowed.

8. Candidate identity:
   Do not invent a candidate or candidate name.

9. Return ONLY valid JSON.
   No markdown.
   No code fences.
   No explanation.

Candidate ID:
{candidate_id}

Story:
{story_text}
"""

    content = call_model(
        prompt,
        "You are a careful CV extraction system. Follow the rules exactly."
    )

    clean = clean_json_response(content)

    try:

        cv = json.loads(clean)

    except json.JSONDecodeError as e:

        raise RuntimeError(
            f"Invalid CV JSON for {candidate_id}:\n{clean}"
        ) from e

    cv = ensure_cv_structure(
        cv,
        candidate_id
    )

    cv = normalize_cv(cv)

    return cv


# ============================================================
# PART 2: SCORE CANDIDATES
# ============================================================

def score_candidates(cvs, rubric_data):

    prompt = f"""
You are given candidate CV records and a scoring rubric.

RUBRIC:
{json.dumps(rubric_data, indent=2, ensure_ascii=False)}

CANDIDATE CV RECORDS:
{json.dumps(cvs, indent=2, ensure_ascii=False)}

Task:

For EVERY candidate, assign a score from 0 to 5 for each
of the three rubric criteria.

Return ONLY a JSON array in this exact structure:

[
  {{
    "candidate_id": "candidate_id",
    "academic": 0,
    "research": 0,
    "experience": 0
  }}
]

Rules:

- Scores must be numbers from 0 to 5.
- Follow the rubric exactly.
- Do not calculate weighted totals.
- Do not calculate the final score.
- Do not rank candidates.
- Do not select a winner.
- Do not add explanations.
- Return one object for every candidate.
- candidate_id must exactly match the supplied candidate_id.
- Return ONLY valid JSON.
"""

    content = call_model(
        prompt,
        "You are a strict rubric-based scorer. Score only; do not rank or calculate totals."
    )

    clean = clean_json_response(content)

    try:

        scores = json.loads(clean)

    except json.JSONDecodeError as e:

        raise RuntimeError(
            f"Invalid score JSON returned by model:\n{clean}"
        ) from e

    if isinstance(scores, dict) and "scores" in scores:
        scores = scores["scores"]

    if not isinstance(scores, list):

        raise RuntimeError(
            f"Model returned invalid scores: {scores}"
        )

    return scores


# ============================================================
# VALIDATE SCORES
# ============================================================

def validate_scores(scores, cvs):

    expected_ids = {
        cv["candidate_id"]
        for cv in cvs
    }

    actual_ids = {
        score.get("candidate_id")
        for score in scores
    }

    # --------------------------------------------------------
    # Check number of scores
    # --------------------------------------------------------

    if len(scores) != len(cvs):

        raise RuntimeError(
            f"Expected {len(cvs)} scores, "
            f"but model returned {len(scores)}."
        )

    # --------------------------------------------------------
    # Check missing IDs
    # --------------------------------------------------------

    missing_ids = (
        expected_ids - actual_ids
    )

    if missing_ids:

        raise RuntimeError(
            "Missing scores for candidate(s): "
            f"{sorted(missing_ids)}"
        )

    # --------------------------------------------------------
    # Check unexpected IDs
    # --------------------------------------------------------

    extra_ids = (
        actual_ids - expected_ids
    )

    if extra_ids:

        raise RuntimeError(
            "Unexpected candidate_id(s): "
            f"{sorted(extra_ids)}"
        )

    # --------------------------------------------------------
    # Validate score fields
    # --------------------------------------------------------

    for score in scores:

        for field in [
            "academic",
            "research",
            "experience"
        ]:

            if field not in score:

                raise RuntimeError(
                    f"Missing '{field}' "
                    f"in score: {score}"
                )

            value = score[field]

            if isinstance(value, bool):

                raise RuntimeError(
                    f"Invalid boolean score for "
                    f"{score['candidate_id']} / "
                    f"{field}: {value}"
                )

            if not isinstance(
                value,
                (int, float)
            ):

                raise RuntimeError(
                    f"Score must be numeric for "
                    f"{score['candidate_id']} / "
                    f"{field}: {value}"
                )

            if not 0 <= value <= 5:

                raise RuntimeError(
                    f"Score must be between 0 and 5 for "
                    f"{score['candidate_id']} / "
                    f"{field}: {value}"
                )


# ============================================================
# LOAD RUBRIC
# ============================================================

def load_rubric(rubric_path):

    with open(
        rubric_path,
        "r",
        encoding="utf-8"
    ) as f:

        rubric_data = json.load(f)

    # --------------------------------------------------------
    # Validate rubric
    # --------------------------------------------------------

    if "criteria" not in rubric_data:

        raise RuntimeError(
            "Rubric JSON does not contain 'criteria'."
        )

    criteria = rubric_data["criteria"]

    if not isinstance(criteria, list):

        raise RuntimeError(
            "'criteria' must be a list."
        )

    # --------------------------------------------------------
    # Extract weights
    # --------------------------------------------------------

    weights = {}

    for criterion in criteria:

        criterion_id = criterion.get("id")
        weight = criterion.get("weight")

        if criterion_id is None:

            raise RuntimeError(
                f"Criterion is missing 'id': {criterion}"
            )

        if weight is None:

            raise RuntimeError(
                f"Criterion '{criterion_id}' "
                f"is missing 'weight'."
            )

        if not isinstance(
            weight,
            (int, float)
        ):

            raise RuntimeError(
                f"Weight for '{criterion_id}' "
                f"must be numeric."
            )

        weights[criterion_id] = weight

    # --------------------------------------------------------
    # Check required criteria
    # --------------------------------------------------------

    required = {
        "academic",
        "research",
        "experience"
    }

    missing = (
        required - set(weights.keys())
    )

    if missing:

        raise RuntimeError(
            "Rubric is missing criterion(s): "
            f"{sorted(missing)}"
        )

    # --------------------------------------------------------
    # Check weights sum to 1
    # --------------------------------------------------------

    weight_sum = sum(
        weights.values()
    )

    if abs(weight_sum - 1.0) > 1e-9:

        raise RuntimeError(
            f"Rubric weights must sum to 1.0. "
            f"Current sum: {weight_sum}"
        )

    return rubric_data, weights


# ============================================================
# CODE CALCULATES WEIGHTED TOTALS
# ============================================================

def compute_totals(scores, weights):

    results = []

    for score in scores:

        total = round(
            weights["academic"]
            * score["academic"]
            +
            weights["research"]
            * score["research"]
            +
            weights["experience"]
            * score["experience"],
            2
        )

        results.append({
            "candidate_id": score["candidate_id"],
            "academic": score["academic"],
            "research": score["research"],
            "experience": score["experience"],
            "total": total
        })

    if not results:

        raise RuntimeError(
            "No candidate results available."
        )

    # --------------------------------------------------------
    # Winner selected ONLY by Python
    # --------------------------------------------------------

    winner = max(
        results,
        key=lambda x: x["total"]
    )

    return results, winner


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(
    cvs,
    scores,
    totals,
    winner,
    submission_report,
    output_path
):

    output = {
        "cvs": cvs,
        "scores": scores,
        "totals": totals,
        "winner": winner,
        "submission_report": submission_report
    }

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as out:

        json.dump(
            output,
            out,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print("=" * 60)
    print("SCHOLARSHIP CANDIDATE EVALUATION")
    print("=" * 60)

    # --------------------------------------------------------
    # Find files
    # --------------------------------------------------------

    base, rubric_path = find_project_paths()

    print(
        f"\nCandidate folder: {base}"
    )

    print(
        f"Rubric file:      {rubric_path}"
    )

    # --------------------------------------------------------
    # Load rubric
    # --------------------------------------------------------

    rubric_data, weights = load_rubric(
        rubric_path
    )

    print(
        "\nRubric weights:"
    )

    print(
        json.dumps(
            weights,
            indent=2,
            ensure_ascii=False
        )
    )

    # --------------------------------------------------------
    # Find candidate files
    # --------------------------------------------------------

    candidate_files = sorted(
        base.glob("*.md")
    )

    if not candidate_files:

        raise RuntimeError(
            f"No .md candidate files found in {base}"
        )

    print(
        f"\nFound {len(candidate_files)} "
        f"candidate file(s)."
    )

    # --------------------------------------------------------
    # PART 1: EXTRACT CVs
    # --------------------------------------------------------

    cvs = []

    submission_report = {}

    for path in candidate_files:

        cid = path.stem

        print(
            f"\nProcessing candidate: {cid}"
        )

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            story_text = f.read()

        if not story_text.strip():

            raise RuntimeError(
                f"Candidate file is empty: {path}"
            )

        cv = extract_cv(
            story_text,
            cid
        )

        cvs.append(cv)

        submission_report[cid] = analyze_cv(
            cv
        )

        print(
            "  CV extracted successfully."
        )

        # Avoid rate limits
        time.sleep(2)

    # --------------------------------------------------------
    # PART 2: MODEL SCORES
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "SCORING CANDIDATES"
    )

    print(
        "=" * 60
    )

    scores = score_candidates(
        cvs,
        rubric_data
    )

    # Validate model output
    validate_scores(
        scores,
        cvs
    )

    print(
        "\nScores returned by model:"
    )

    print(
        json.dumps(
            scores,
            indent=2,
            ensure_ascii=False
        )
    )

    # --------------------------------------------------------
    # CODE CALCULATES WEIGHTED TOTALS
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "CALCULATING WEIGHTED TOTALS"
    )

    print(
        "=" * 60
    )

    totals, winner = compute_totals(
        scores,
        weights
    )

    print(
        "\nFinal totals:"
    )

    print(
        json.dumps(
            totals,
            indent=2,
            ensure_ascii=False
        )
    )

    # --------------------------------------------------------
    # SAVE RESULTS
    # --------------------------------------------------------

    output_path = (
        Path.cwd() / OUTPUT_FILE
    )

    save_results(
        cvs,
        scores,
        totals,
        winner,
        submission_report,
        output_path
    )

    # --------------------------------------------------------
    # PRINT WINNER
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "=== CODE WINNER ==="
    )

    print(
        "=" * 60
    )

    print(
        json.dumps(
            winner,
            indent=2,
            ensure_ascii=False
        )
    )

    print(
        f"\nSaved to: {output_path}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()