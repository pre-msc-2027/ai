#!/usr/bin/env python3
"""
Serveur de test pour simuler l'API
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlparse


class TestAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path.startswith("/api/scans/analyse_with_rules/"):
            # Données de test basées sur input.json
            test_data = {
                "analysis": {
                    "repo_url": "https://github.com/client_org/repo_client",
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


if __name__ == "__main__":
    server = HTTPServer(("localhost", 8000), TestAPIHandler)
    print("Serveur de test démarré sur http://localhost:8000")
    print("Utilisez Ctrl+C pour arrêter")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur")
        server.shutdown()
