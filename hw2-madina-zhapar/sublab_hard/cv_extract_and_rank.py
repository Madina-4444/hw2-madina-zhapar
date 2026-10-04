import os, json, time
from pathlib import Path
from openai import OpenAI

# === Пути к данным ===
base = r"C:\Users\tb071\AI\hw2-madina-zhapar\data"
candidates_dir = os.path.join(base, "canditates")
rubric_path = os.path.join(base, "candidate_rubric.json")

# === Клиент OpenRouter ===
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

MODEL = "deepseek/deepseek-v4-flash-0731"

def call_model(prompt, system):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"system","content":system},
                  {"role":"user","content":prompt}]
    )
    return resp.choices[0].message.content.strip()

# === Извлечение CV ===
def extract_cv(story, cid):
    schema = {
        "candidate_id": cid,
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
    prompt = f"""
Extract CV in JSON with schema:
{json.dumps(schema,indent=2)}

STRICT RULES — FOLLOW EXACTLY:

1. Missing facts:
   - If the story does not explicitly state a fact, set the field to null.
   - Never estimate, infer, or guess. 
   - No GPA means gpa_4_scale = null. Do not invent one.

2. GPA:
   - Record GPA exactly as written in the story.
   - If GPA is on another scale (e.g. 5.0), you MUST convert it to a 4.0 scale.
   - Always record the original scale beside it.
   - Example: "4.6/5.0" → gpa_4_scale = 3.68, original_scale = "5.0".
   - If GPA is missing, leave null. Never infer from diploma or wording.

3. Publications:
   - Count a publication ONLY if the story explicitly says "published" or "accepted".
   - Do NOT count: submitted, under review, in review, in preparation, in press, planned.
   - These must be recorded separately in submitted_outputs.

4. Contradictions:
   - If the story contradicts itself (e.g. two different GPAs, two different graduation years):
     - Do NOT resolve or average.
     - Set the field to null.
     - Record the contradiction text in contradictions[].

5. Evidence:
   - Every non-null field MUST have supporting evidence.
   - Evidence must be a direct quote or close excerpt from the story.
   - Never invent evidence.

6. Languages:
   - Include ONLY languages explicitly stated in the story.

7. Experience:
   - Count only explicitly stated months of relevant work or internships.
   - Overlapping periods count once.
   - If no dates are given, do not count months. Record but leave experience_months = null.

8. Candidate identity:
   - Candidate_id comes from filename.
   - Do not invent or alter names.

Return ONLY valid JSON. No markdown, no code fences, no explanations.
Story ({cid}):
{story}
"""
    return json.loads(call_model(prompt,"CV extraction"))

# === Оценка по рубрике ===
def score_candidates(cvs, rubric):
    prompt = f"""
Score each candidate 0–5 on rubric criteria.
Rubric:
{json.dumps(rubric,indent=2)}
CVs:
{json.dumps(cvs,indent=2)}
Return JSON array:
[{{"candidate_id":"...","academic":0,"research":0,"experience":0}}]
"""
    return json.loads(call_model(prompt,"Rubric scoring"))

# === Итоговый подсчёт ===
def compute_totals(scores, weights):
    results=[]
    for s in scores:
        total=round(weights["academic"]*s["academic"]+
                    weights["research"]*s["research"]+
                    weights["experience"]*s["experience"],2)
        results.append({**s,"total":total})
    winner=max(results,key=lambda x:x["total"])
    return results,winner

def main():
    rubric=json.load(open(rubric_path,encoding="utf-8"))
    weights={c["id"]:c["weight"] for c in rubric["criteria"]}
    cvs=[]
    for f in sorted(Path(candidates_dir).glob("*.md")):
        story=open(f,encoding="utf-8").read()
        cvs.append(extract_cv(story,f.stem))
        time.sleep(2)
    scores=score_candidates(cvs,rubric)
    totals,winner=compute_totals(scores,weights)
    out=os.path.join(base,"submission_scores.json")
    json.dump({"cvs":cvs,"scores":scores,"totals":totals,"winner":winner},
              open(out,"w",encoding="utf-8"),indent=2,ensure_ascii=False)
    print("Winner:",winner)

if __name__=="__main__":
    main()
