"""Vercel serverless function — POST /api/analyze
Calls Claude API and returns missionary analysis."""

from http.server import BaseHTTPRequestHandler
import json, os

class handler(BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            length  = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length))

            import anthropic
            client = anthropic.Anthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY", "")
            )

            zone_lines = []
            for zone, metrics in payload.get("zonas", {}).items():
                parts = [
                    f"{m}: {v['r']}/{v['m']:.0f} ({v['p']:.0f}%)"
                    for m, v in metrics.items()
                ]
                zone_lines.append(f"  {zone}: " + " | ".join(parts))

            prompt = (
                "Você é consultor sênior de liderança missionária SUD, "
                "especialista no PME (Pregar Meu Evangelho) Cap. 8 e 9.\n\n"
                f"Padrões/semana/companherismo: Batismos 2/mês | Datas 3 | "
                "Convites 6 | Sacramental 5 | Contatos 120 | Novos 10 | Lições 3\n\n"
                f"Período: {payload.get('periodo','—')}\n"
                f"Áreas ativas: {payload.get('areas','?')} | "
                f"Semanas: {payload.get('semanas','?')}\n\n"
                "Dados por zona (indicador: realizado/meta pct%):\n"
                + "\n".join(zone_lines) + "\n\n"
                "Análise executiva (máx 380 palavras, pt-BR, markdown):\n\n"
                "**PANORAMA GERAL** (2-3 frases diretas)\n\n"
                "**POR ZONA** (1 frase diagnóstico + 1 ação PME por zona)\n\n"
                "**TOP 3 PRIORIDADES** (bullet points, 1 linha cada)\n\n"
                "**RISCO PRINCIPAL** (1 parágrafo)"
            )

            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=700,
                messages=[{"role": "user", "content": prompt}],
            )
            body = json.dumps(
                {"analysis": msg.content[0].text}, ensure_ascii=False
            ).encode("utf-8")

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
