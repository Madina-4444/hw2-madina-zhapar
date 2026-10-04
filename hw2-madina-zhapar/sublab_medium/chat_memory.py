import os, json
from openai import OpenAI
from jsonschema import validate

# === Клиент OpenRouter ===
def openrouter_client() -> OpenAI:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)

client = openrouter_client()

# === Загружаем данные ===
base = r"C:\Users\tb071\AI\hw2-madina-zhapar\data"
script = json.load(open(os.path.join(base, "chat_script.json"), encoding="utf-8"))
schema = json.load(open(os.path.join(base, "memory_state.schema.json"), encoding="utf-8"))

conversation = script["conversation"]
probes = script["probes"]

# === Вызов модели ===
def call_model(messages):
    resp = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=messages
    )
    return resp.choices[0].message.content

# === Сжатие истории ===
def compress(history):
    system_prompt = (
        "Summarise the conversation into a JSON object that matches memory_state.schema.json. "
        "Output ONLY the JSON object, no code fences, no explanations. "
        "Use exactly the required fields: applicant_id, topic, facts, decisions, constraints, open_questions, language. "
        "Fill missing values with null or []. Do not invent facts."
    )
    messages = [{"role": "system", "content": system_prompt}] + history
    reply = call_model(messages).strip()
    if reply.startswith("```"):
        reply = reply.strip("`").replace("json", "", 1).strip()

    try:
        state = json.loads(reply)
        validate(instance=state, schema=schema) 
        print("✅ Compression successful")
        return state
    except Exception as e:
        print("⚠️ Compression failed:", e)
        print("Model reply was:", reply)
        return None

# === Запуск скрипта ===
def run_script(compressed=False):
    history = []
    state = None
    tokens_per_call = []
    probe_results = {}

    for turn in conversation:
        if turn == "<compress>" and compressed:
            state = compress(history)
            if state:
        # сохраняем state как JSON-текст в истории
                history = [
                    {"role": "system", "content": "Memory state object:"},
                    {"role": "assistant", "content": json.dumps(state)}
                ]
            else:
                print("Keeping full history (summary invalid).")

        else:
            history.append({"role": "user", "content": turn})
        tokens_per_call.append(sum(len(m["content"].split()) for m in history))

    # probes
    for probe in probes:
        history.append({"role": "user", "content": probe["question"]})
        reply = call_model(history)
        probe_results[probe["id"]] = {
            "reply": reply,
            "retrieved": any(exp in reply for exp in probe["expect_contains"])
        }
        tokens_per_call.append(sum(len(m["content"].split()) for m in history))

    return tokens_per_call, probe_results, state

if __name__ == "__main__":
    # Прогон без компрессии
    tokens_u, probes_u, state_u = run_script(compressed=False)
    results_u = {
        "tokens": tokens_u,
        "peak": max(tokens_u),
        "probes": probes_u,
        "state": None
    }
    out_path_u = os.path.join(base, "results_uncompressed.json")
    with open(out_path_u, "w", encoding="utf-8") as f:
        json.dump(results_u, f, ensure_ascii=False, indent=2)
    print(f"Saved uncompressed run to {out_path_u}")

    # Прогон с компрессией
    tokens_c, probes_c, state_c = run_script(compressed=True)
    results_c = {
        "tokens": tokens_c,
        "peak": max(tokens_c),
        "probes": probes_c,
        "state_file": "state.json" if state_c else None
    }
    out_path_c = os.path.join(base, "results_compressed.json")
    with open(out_path_c, "w", encoding="utf-8") as f:
        json.dump(results_c, f, ensure_ascii=False, indent=2)
    print(f"Saved compressed run to {out_path_c}")

    if state_c:
        state_path = os.path.join(base, "state.json")
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state_c, f, ensure_ascii=False, indent=2)
        print(f"Saved state object to {state_path}")
