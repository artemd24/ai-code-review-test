import os
import json
import requests
import time

MODEL_MAP = {
    "open-ai": "openai/gpt-oss-20b:free",
    "deepseek": "deepseek/deepseek-chat-v3.1:free",
    "qwen3": "qwen/qwen3-coder:free",
    "qwen2.5": "qwen/qwen-2.5-coder-32b-instruct:free",
    "kwaipilot": "kwaipilot/kat-coder-pro:free",
    "agentica": "agentica-org/deepcoder-14b-preview:free",
    "mistral": "mistralai/mistral-small-3.2-24b-instruct:free"
}


def get_mr_data(project_id: str, mr_iid: str, token: str) -> dict:
    """Получаем данные MR, включая diff_refs для inline-комментариев."""
    api_url = f"{os.getenv('CI_SERVER_URL')}/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
    headers = {"PRIVATE-TOKEN": token}
    resp = requests.get(api_url, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f"Ошибка GitLab API: {resp.status_code} - {resp.text}")
    return resp.json()


def get_diff(project_id: str, mr_iid: str, token: str) -> str:
    """Получает diff merge request через GitLab API."""
    api_url = f"{os.getenv('CI_SERVER_URL')}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/changes"
    headers = {"PRIVATE-TOKEN": token}
    resp = requests.get(api_url, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f"Ошибка GitLab API: {resp.status_code} - {resp.text}")

    data = resp.json()
    diff_text = ""
    for change in data.get("changes", []):
        old_path = change.get("old_path", "")
        new_path = change.get("new_path", "")
        diff_text += f"--- {old_path}\n+++ {new_path}\n{change['diff']}\n"

    return diff_text.strip()


def generate_review_json(model_name: str, diff_text: str, api_key: str) -> dict:
    """Отправляет diff модели и получает JSON с комментариями и исправлениями."""
    model_id = MODEL_MAP.get(model_name)
    if not model_id:
        raise ValueError(f"Неизвестная модель: {model_name}")

    prompt = (
        "Ты — опытный инженер, делающий code review.\n"
        "Проанализируй diff и верни ответ в формате JSON:\n"
        "{\n"
        "  \"comments\": [\n"
        "    {\n"
        "      \"file\": \"<путь_к_файлу>\",\n"
        "      \"line\": <номер_строки>,\n"
        "      \"comment\": \"<markdown-комментарий>\",\n"
        "      \"suggestion\": \"<предлагаемый diff или исправление кода>\"\n"
        "    }\n"
        "  ],\n"
        "  \"summary\": \"<markdown-резюме с общими выводами>\"\n"
        "}\n\n"
        "Формат комментариев — **markdown**, чтобы они выглядели аккуратно.\n"
        "Правила для поля \"line\":"
        "- Используй только НОМЕРА СТРОК из новой версии diff (правая часть)."
        "- Только одно целое число (integer), без строк, float, массивов и диапазонов."
        "- Нельзя указывать строки, которые начинаются с '-' (удалённые)."
        "- Разрешены строки с ' ' (контекст) и '+' (добавленные)."
        "- Номер определяй по хунку @@ -a,b +c,d @@, диапазон: c..c+d-1."
        "- Если номер определить нельзя — НЕ создавай комментарий."
        " Верни строго валидный JSON без пояснений вне структуры."
        "=== BEGIN DIFF ===\n"
        f"{diff_text}\n"
        "=== END DIFF ==="
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, 4):
        # TODO: системные сообщения к модели user/tool/dev/system
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps({
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
            }),
            timeout=180,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Ошибка OpenRouter API: {response.status_code} - {response.text}"
            )

        content = response.json()["choices"][0]["message"]["content"]

        # Пробуем распарсить JSON
        try:
            review = json.loads(content)
            break
        except json.JSONDecodeError:
            print(f"[WARN] Попытка {attempt}: модель вернула невалидный JSON, пробуем снова...")
            time.sleep(1)
            # TODO: Добавить ошибку при повторной отправке промпта,
            # TODO: можно отправлять сам json и сообщение об ошибке, чтобы она исправилась
            if attempt == 3:
                raise RuntimeError(
                    f"Максимальное число попыток превышено, попыток было {attempt}"
                )

    # Сохраняем для истории
    os.makedirs("review_output", exist_ok=True)
    with open("review_output/review.json", "w", encoding="utf-8") as f:
        json.dump(review, f, ensure_ascii=False, indent=2)

    # Сохраняем markdown-отчёт
    md_lines = ["# Code Review Report\n"]
    for c in review.get("comments", []):
        md_lines.append(f"### 📝 {c['file']}:{c['line']}\n")
        md_lines.append(f"{c['comment']}\n")
        if c.get("suggestion"):
            md_lines.append(f"```diff\n{c['suggestion']}\n```\n")
    if review.get("summary"):
        md_lines.append("\n## Summary\n" + review["summary"])
    with open("review_output/review.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    return review


def post_comment_to_gitlab(project_id: str, mr_iid: str, token: str, comment_obj: dict,
                           base_sha: str, start_sha: str, head_sha: str):
    """Добавляет inline или общий markdown-комментарий."""
    api_url = f"{os.getenv('CI_SERVER_URL')}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/discussions"

    # Markdown формат комментария
    body = f"### 💬 Code Review\n{comment_obj['comment']}"
    if "suggestion" in comment_obj and comment_obj["suggestion"]:
        body += f"\n\n```diff\n{comment_obj['suggestion']}\n```"

    payload = {
        "body": body,
        "position": {
            "position_type": "text",
            "base_sha": base_sha,
            "start_sha": start_sha,
            "head_sha": head_sha,
            "new_path": comment_obj["file"],
            "new_line": comment_obj["line"],
        },
    }

    resp = requests.post(
        api_url,
        headers={"PRIVATE-TOKEN": token, "Content-Type": "application/json"},
        data=json.dumps(payload),
    )

    if resp.status_code == 400 and "new_line" in resp.text:
        # fallback — общий комментарий
        print(f"[i] Линия {comment_obj['line']} невалидна для {comment_obj['file']}, добавляем общий комментарий.")
        payload = {"body": body}
        requests.post(
            api_url,
            headers={"PRIVATE-TOKEN": token, "Content-Type": "application/json"},
            data=json.dumps(payload),
        )
    elif resp.status_code not in (200, 201):
        print(f"[!] Ошибка при добавлении комментария: {resp.status_code} - {resp.text}")


def main():
    try:
        project_id = os.getenv("CI_PROJECT_ID")
        mr_iid = os.getenv("CI_MERGE_REQUEST_IID")
        gitlab_token = os.getenv("GITLAB_TOKEN")
        openrouter_key = os.getenv("OPENROUTE_API_KEY")
        model = os.getenv("MODEL", "deepseek")

        if not all([project_id, mr_iid, gitlab_token, openrouter_key]):
            raise EnvironmentError("Не хватает переменных окружения (GITLAB_TOKEN, OPENROUTE_API_KEY и др.)")

        print(f"[i] Запуск Code Review Bot для MR !{mr_iid}")

        diff_text = get_diff(project_id, mr_iid, gitlab_token)
        if not diff_text:
            print("[i] Нет изменений для анализа.")
            return

        mr_data = get_mr_data(project_id, mr_iid, gitlab_token)
        diff_refs = mr_data.get("diff_refs", {})
        base_sha = diff_refs.get("base_sha")
        start_sha = diff_refs.get("start_sha")
        head_sha = diff_refs.get("head_sha")

        review = generate_review_json(model, diff_text, openrouter_key)
        comments = review.get("comments", [])
        summary = review.get("summary", "")

        # TODO: Если line некорретный прикреплять его как line=0

        for c in comments:
            post_comment_to_gitlab(project_id, mr_iid, gitlab_token, c, base_sha, start_sha, head_sha)

        if summary:
            post_comment_to_gitlab(
                project_id, mr_iid, gitlab_token,
                {"file": "SUMMARY", "line": 0, "comment": summary},
                base_sha, start_sha, head_sha
            )

        print(f"[✔] Добавлено {len(comments)} комментариев и итоговое резюме.")
    except Exception as e:
        print(f"[!] Ошибка Code Review: {e}")


if __name__ == "__main__":
    main()
