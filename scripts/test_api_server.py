#!/usr/bin/env python3
"""
Serveur de test pour simuler l'API
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import re
from urllib.parse import urlparse


class MockAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path.startswith("/scans/analyse_with_rules/"):
            # Données de test basées sur input.json
            test_data = {
                "repo_url": "https://github.com/client_org/repo_client",
                "analysis": {
                    "warnings": [
                        {"id": 0, "rule_id": 0, "file": "public/index.html", "line": 8},
                        {"id": 1, "rule_id": 0, "file": "public/index.html", "line": 9},
                        {
                            "id": 2,
                            "rule_id": 0,
                            "file": "public/index.html",
                            "line": 10,
                        },
                    ],
                },
                "rules": [
                    {
                        "rule_id": 0,
                        "name": "Check Tags Casing",
                        "Description": (
                            "Check that all html tags are in the correct casing"
                        ),
                        "language": "html",
                        "tags": [],
                        "parameters": {"casing": "lower_case"},
                    }
                ],
            }

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(test_data).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_path = urlparse(self.path)

        # Vérifier si c'est un endpoint d'AI comment
        ai_comment_match = re.match(r"/scans/ai_comment/(.+)", parsed_path.path)

        if ai_comment_match:
            scan_id = ai_comment_match.group(1)

            # Lire les données du body
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            try:
                ai_results = json.loads(post_data.decode("utf-8"))

                # Log des résultats reçus pour debug
                print(f"[API] Résultats IA reçus pour scan {scan_id}:")
                print(json.dumps(ai_results, indent=2, ensure_ascii=False))

                # Réponse de succès
                response_data = {
                    "status": "success",
                    "message": f"AI results received for scan {scan_id}",
                    "results_count": len(ai_results),
                }

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())

            except json.JSONDecodeError as e:
                print(f"[API] Erreur JSON dans les données reçues: {e}")
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                error_response = {"error": "Invalid JSON data"}
                self.wfile.write(json.dumps(error_response).encode())

        else:
            self.send_response(404)  # type: ignore[unreachable]
            self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("localhost", 8001), MockAPIHandler)
    print("Serveur de test démarré sur http://localhost:8001")
    print("Utilisez Ctrl+C pour arrêter")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur")
        server.shutdown()
