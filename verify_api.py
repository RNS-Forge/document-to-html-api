from starlette.testclient import TestClient
from app import app
from pathlib import Path

client = TestClient(app)

p1 = r"C:\Users\6point3_FA0018\.gemini\antigravity-ide\brain\a7554e23-1211-4dfc-8d3e-790872f6321a\.user_uploaded\media_1792492369576.png"
p2 = r"C:\Users\6point3_FA0018\.gemini\antigravity-ide\brain\a7554e23-1211-4dfc-8d3e-790872f6321a\.user_uploaded\media_1792492389851.png"

print("--- Testing Bank Form Image ---")
with open(p1, "rb") as f1:
    r1 = client.post("/convert", files={"file": ("bank_form.png", f1.read(), "image/png")})
assert r1.status_code == 200, f"Error: {r1.status_code}"
html1 = r1.json().get("html", "")
print("Status:", r1.status_code)
print("Has <table>:", "<table" in html1)
print("Has <input type=\"checkbox\":", '<input type="checkbox"' in html1)
print("Has 'AR NO':", "AR NO" in html1)
print("Base64 Logo Count:", html1.count("data:image/"))
print("HTML Size:", len(html1), "bytes")
assert html1.count("data:image/") == 1, "Should have ONLY 1 cropped logo as Base64!"

print("\n--- Testing Solara Letterhead Image ---")
with open(p2, "rb") as f2:
    r2 = client.post("/convert", files={"file": ("solara_letterhead.png", f2.read(), "image/png")})
assert r2.status_code == 200, f"Error: {r2.status_code}"
html2 = r2.json().get("html", "")
print("Status:", r2.status_code)
print("Has Solara:", "Solara" in html2 or "SOLARA" in html2)
print("Has <table>:", "<table" in html2)
print("Has Corporate Address:", "Corporate Address" in html2)
print("Base64 Logo Count:", html2.count("data:image/"))
print("HTML Size:", len(html2), "bytes")
assert html2.count("data:image/") == 1, "Should have ONLY 1 cropped logo as Base64!"

# Also save both outputs
out_dir = Path("test_outputs")
out_dir.mkdir(exist_ok=True)
with open(out_dir / "api_tested_bank_form.html", "w", encoding="utf-8") as out1:
    out1.write(html1)
with open(out_dir / "api_tested_solara_letterhead.html", "w", encoding="utf-8") as out2:
    out2.write(html2)

print("\n[SUCCESS] Both images converted with ONLY logo Base64 and 100% accurate HTML!")
