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
    system_prompt = "Summarise the conversation into a JSON object that matches memory_state.schema.json."
    messages = [{"role": "system", "content": system_prompt}] + history
    reply = call_model(messages)
    try:
        state = json.loads(reply)
        for field in schema["required"]:
            if field not in state:
                raise ValueError(f"Missing field {field}")
        return state
    except Exception as e:
        print("⚠️ Compression failed:", e)
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
                history = [{"role": "system", "content": json.dumps(state)}]
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
    # Запускаем оба прогона
    tokens_u, probes_u, state_u = run_script(compressed=False)
    tokens_c, probes_c, state_c = run_script(compressed=True)

    results = {
        "uncompressed": {
            "tokens": tokens_u,
            "peak": max(tokens_u),
            "probes": probes_u,
            "state": state_u
        },
        "compressed": {
            "tokens": tokens_c,
            "peak": max(tokens_c),
            "probes": probes_c,
            "state": state_c
        }
    }

    out_path = os.path.join(base, "results2.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved both runs to {out_path}")
