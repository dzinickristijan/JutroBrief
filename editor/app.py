"""Lokalni web editor za draftove (pokreni: python editor/app.py).

Otvara http://127.0.0.1:5050 — pregled priča, zamjena s B-liste, spremanje drafta.
"""

import os
import sys
from datetime import datetime

from flask import Flask, redirect, render_template_string, request, url_for

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.chdir(ROOT)

from issue_parser import list_stories, parse_issue, serialize_issue, swap_story  # noqa: E402

app = Flask(__name__)

LAYOUT = """
<!doctype html>
<html lang="hr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jutarnji brief — editor</title>
<style>
  :root { --paper:#FAF7F1; --ink:#262019; --sun:#E8A11C; --line:#E4DCCF; }
  body { font-family: Inter, system-ui, sans-serif; background: var(--paper); color: var(--ink);
         margin: 0; padding: 24px; line-height: 1.5; }
  .wrap { max-width: 900px; margin: 0 auto; }
  h1 { font-size: 1.5rem; margin-bottom: 8px; }
  .nav { margin-bottom: 20px; display: flex; gap: 12px; flex-wrap: wrap; }
  a, button { font: inherit; }
  a { color: var(--ink); }
  textarea { width: 100%; min-height: 420px; font-family: ui-monospace, monospace;
             font-size: 14px; padding: 12px; border: 1px solid var(--line); border-radius: 6px; }
  pre { background: #fff; border: 1px solid var(--line); padding: 12px; border-radius: 6px;
        overflow-x: auto; font-size: 13px; }
  .card { background: #fff; border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin: 16px 0; }
  .row { display: flex; gap: 8px; align-items: end; flex-wrap: wrap; }
  input[type=number] { width: 64px; padding: 6px; }
  button { background: var(--ink); color: #fff; border: 0; padding: 8px 14px; border-radius: 6px; cursor: pointer; }
  button.secondary { background: #fff; color: var(--ink); border: 1px solid var(--line); }
  .msg { background: #F1E6CE; padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; }
</style>
</head>
<body><div class="wrap">
  <h1>Jutarnji brief — editor</h1>
  <div class="nav">
    <a href="{{ url_for('index') }}">Početna</a>
    <a href="{{ url_for('edit', date=date) }}">Uredi draft</a>
    <a href="{{ url_for('swap', date=date) }}">Zamjena (B-lista)</a>
  </div>
  {% if msg %}<div class="msg">{{ msg }}</div>{% endif %}
  {% block body %}{% endblock %}
</div></body></html>
"""


def draft_path(date_str: str) -> str:
    p = os.path.join("drafts", f"{date_str}.md")
    if os.path.exists(p):
        return p
    posts = os.path.join("posts", f"{date_str}.md")
    if os.path.exists(posts):
        return posts
    raise FileNotFoundError(date_str)


@app.route("/")
def index():
    dates = []
    for folder in ("drafts", "posts"):
        if not os.path.isdir(folder):
            continue
        for f in os.listdir(folder):
            if f.endswith(".md") and f[:4].isdigit():
                dates.append(f.replace(".md", ""))
    dates = sorted(set(dates), reverse=True)
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template_string(
        LAYOUT + "{% block body %}<p>Izdanja:</p><ul>{% for d in dates %}"
        "<li><a href=\"{{ url_for('edit', date=d) }}\">{{ d }}</a></li>{% endfor %}</ul>"
        "<p><a href=\"{{ url_for('edit', date=today) }}\">Današnji draft</a></p>{% endblock %}",
        dates=dates,
        today=today,
        date=today,
        msg=None,
    )


@app.route("/edit/<date>", methods=["GET", "POST"])
def edit(date: str):
    path = draft_path(date)
    msg = None
    if request.method == "POST":
        text = request.form.get("content", "")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        msg = f"Spremljeno: {path}"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    tpl = LAYOUT + """{% block body %}
    <form method="post">
      <p><strong>{{ path }}</strong></p>
      <textarea name="content">{{ content }}</textarea>
      <p style="margin-top:12px">
        <button type="submit">Spremi</button>
        <button type="submit" class="secondary" formaction="{{ url_for('publish', date=date) }}">Objavi (posts + docs)</button>
      </p>
    </form>{% endblock %}"""
    return render_template_string(tpl, path=path, content=content, date=date, msg=msg)


@app.route("/swap/<date>", methods=["GET", "POST"])
def swap(date: str):
    path = draft_path(date)
    msg = None
    with open(path, "r", encoding="utf-8") as f:
        doc = parse_issue(f.read())

    if request.method == "POST":
        out_i = int(request.form["out"])
        in_i = int(request.form["in_idx"])
        doc = swap_story(doc, out_i, in_i)
        with open(path, "w", encoding="utf-8") as f:
            f.write(serialize_issue(doc))
        msg = f"Zamijenjeno: priča #{out_i} ← B-lista #{in_i}. Dopuni sažetak u Uredi draft."
        with open(path, "r", encoding="utf-8") as f:
            doc = parse_issue(f.read())

    tpl = LAYOUT + """{% block body %}
    <div class="card"><pre>{{ listing }}</pre></div>
    <form method="post" class="card row">
      <label>Priča # <input type="number" name="out" min="1" required></label>
      <label>B-lista # <input type="number" name="in_idx" min="1" required></label>
      <button type="submit">Zamijeni</button>
    </form>{% endblock %}"""
    return render_template_string(
        tpl, listing=list_stories(doc), date=date, msg=msg
    )


@app.route("/publish/<date>", methods=["POST"])
def publish(date: str):
    import shutil
    from publish import main as publish_main

    src = draft_path(date)
    dst = os.path.join("posts", f"{date}.md")
    shutil.copy2(src, dst)
    publish_main()
    return redirect(url_for("edit", date=date) + "?published=1")


if __name__ == "__main__":
    print("Editor: http://127.0.0.1:5050")
    app.run(host="127.0.0.1", port=5050, debug=True)
