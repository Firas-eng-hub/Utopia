"""Functional checks for a running deployment; removes its temporary account."""
import argparse
from pathlib import Path
import secrets

import httpx


def check(response, expected=200):
    if response.status_code != expected:
        raise RuntimeError(f"{response.request.method} {response.request.url.path}: "
                           f"expected {expected}, got {response.status_code}")
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", required=True, help="API origin, without /api/v1")
    parser.add_argument("--frontend", required=True, help="Frontend origin")
    args = parser.parse_args()
    frontend = args.frontend.rstrip("/")
    with httpx.Client(base_url=args.api.rstrip("/"), timeout=120) as client:
        assert check(client.get("/ready")).json()["status"] == "ready"
        assert check(client.get("/api/v1/health")).json()["database"] == "connected"
        preflight = client.options("/api/v1/auth/login", headers={
            "Origin": frontend,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        })
        assert check(preflight).headers.get("access-control-allow-origin") == frontend
        print("PASS database readiness and frontend CORS")
        email = f"deployment-check-{secrets.token_hex(8)}@example.com"
        password = secrets.token_hex(20) + "A1"
        data = check(client.post("/api/v1/auth/register", json={
            "email": email, "password": password, "full_name": "Deployment Check",
            "accepted_privacy_policy": True,
        }), 201).json()
        client.headers["Authorization"] = "Bearer " + data["access_token"]
        try:
            check(client.post("/api/v1/auth/login", data={"username": email, "password": password}))
            assert check(client.get("/api/v1/auth/me")).json()["email"] == email
            print("PASS registration, login, and authenticated profile")
            for path in ("/api/v1/jobs/list", "/api/v1/jobs/saved", "/api/v1/resumes/list",
                         "/api/v1/footprint/history", "/api/v1/interview/sessions"):
                check(client.get(path))
                print("PASS", path)
            session = check(client.post("/api/v1/interview/start", json={
                "session_type": "technical", "job_role": "Software Engineer",
                "difficulty_level": "mid", "num_questions": 3,
            })).json()
            assert session["first_question"]["question_text"]
            check(client.get(f'/api/v1/interview/{session["session_id"]}/question'))
            print("PASS interview session and question retrieval")
            sample = Path(__file__).resolve().parents[1] / "data/resumes/sample_resume.pdf"
            if sample.exists():
                with sample.open("rb") as file:
                    resume = check(client.post("/api/v1/resumes/upload", files={
                        "file": ("sample_resume.pdf", file, "application/pdf")}), 201).json()
                original = check(client.get(f'/api/v1/resumes/{resume["resume_id"]}/download'))
                assert original.content == sample.read_bytes()
                check(client.delete(f'/api/v1/resumes/{resume["resume_id"]}'))
                print("PASS PDF upload, parsing, original download, and deletion")
            else:
                print("SKIP sample PDF upload: sample file not present")
        finally:
            check(client.delete("/api/v1/auth/account"))
            print("PASS temporary account cleanup")
    with httpx.Client(base_url=frontend, timeout=30) as client:
        home = check(client.get("/"))
        assert 'id="root"' in home.text
        for path in ("/login", "/dashboard", "/dashboard/resume"):
            response = check(client.get(path))
            assert 'id="root"' in response.text
        print("PASS frontend home and SPA deep links")


if __name__ == "__main__":
    main()
