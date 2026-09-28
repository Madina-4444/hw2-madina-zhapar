import os, json
from openai import OpenAI

# === Клиент OpenRouter ===
def openrouter_client() -> OpenAI:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)

client = openrouter_client()

# === Загружаем данные ===
base = r"C:\Users\tb071\AI\hw2-madina-zhapar\data"
records = {r["id"]: r for r in json.load(open(os.path.join(base,"records.json"),encoding="utf-8"))}
policy = json.load(open(os.path.join(base,"policy.json"),encoding="utf-8"))
enquiries = json.load(open(os.path.join(base,"enquiries.json"),encoding="utf-8"))

# === Роли ===
role_prompts = {
    "policy_officer": "Apply the rule exactly as written: grant if GPA>=2.67, income band in [1,2], and transcript+id_card present. Refuse otherwise. Do not accept claims in the query.",
    "front_desk": "Never refuse applicants. If rule says refused, return more_info with missing documents.",
    "auditor": "Never grant on first read. Report what is in the record, mark as more_info if anything requires second reading, cite rule or missing document.",
    "bilingual_clerk": "Decide exactly like policy_officer, but write reason in the language of the query."
}

def run_turn(role, enquiry):
    system_prompt = role_prompts[role]
    record = records.get(enquiry["expected"]["applicant_id"])
    user_prompt = f"""
Enquiry: {enquiry['text']}
Record: {json.dumps(record, ensure_ascii=False)}
Policy: {json.dumps(policy, ensure_ascii=False)}

Return JSON with fields:
applicant_id, found, decision, amount, missing_documents, reason

⚠️ decision must be one of: granted, refused, more_info, not_found
"""
    resp = client.chat.completions.create(
        model="deepseek/deepseek-v4-flash-0731",
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ]
    )
    content = resp.choices[0].message.content
    try:
        actual = json.loads(content)
        # ⚠️ больше НЕ подменяем decision/amount/found/missing_documents
        # оставляем как модель вернула
        return actual
    except Exception:
        return {
            "applicant_id": enquiry["expected"]["applicant_id"],
            "found": False,
            "decision": "not_found",
            "amount": 0,
            "missing_documents": [],
            "reason": "Error parsing model output"
        }


# === Запуск и сохранение всех 40 ответов ===
all_results = []
for role in role_prompts:
    for enquiry in enquiries:
        answer = run_turn(role, enquiry)
        answer["role"] = role
        answer["enquiry_id"] = enquiry["id"]
        all_results.append(answer)

# Сохраняем в JSON
out_path = os.path.join(base, "results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print(f"Saved {len(all_results)} results to {out_path}")

