"""Vercel serverless function — GET /api/data
Fetches Google Sheets CSV, normalises columns, returns JSON."""

from http.server import BaseHTTPRequestHandler
import json, csv, re, urllib.request, urllib.parse
from io import StringIO

SHEET_ID   = "1-H8JUnd_I05yZp0gowwqgT0Jleev87db0lLgi7hitxU"
SHEET_NAME = "ResponsesB (Filtered)"
NUMERIC    = {
    "Batismos","Datas Marcadas","Datas Mantidas","Convites","Igreja",
    "Novos","Contatos","Lições c/ Membro","Lição RCs","Igreja RCs","Frequência",
    "FBC Batismos","FBC Datas","FBC Igreja",
}

def norm(s):
    s = s.strip().replace("\n", " ")
    if re.search(r"li[cç][oõ]es\s*c/", s, re.I): return "Lições c/ Membro"
    if re.search(r"li[cç][aã]o\s*rcs",  s, re.I): return "Lição RCs"
    if "Batizadas"        in s and "Nome" in s:    return "Nome Batizados"
    if "Pessoas com Data" in s and "Nome" in s:    return "Nome Datas"
    return s

class handler(BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        try:
            url = (
                f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
                f"/export?format=csv&sheet={urllib.parse.quote(SHEET_NAME)}"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                text = r.read().decode("utf-8")

            reader = csv.DictReader(StringIO(text))
            rows = []
            for raw in reader:
                row = {norm(k): v.strip() for k, v in raw.items()}
                if not row.get("Data", "").strip():
                    continue
                for k in NUMERIC:
                    if k in row:
                        try:    row[k] = float(row[k]) if row[k] else 0
                        except: row[k] = 0
                rows.append(row)

            body = json.dumps(rows, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._cors()
            self.end_headers()
            self.wfile.write(body)

        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(body)
