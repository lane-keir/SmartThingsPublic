"""Fill in the Teams manifest placeholders and build the upload-ready zip.

    python3 tools/package_teams_app.py --tenant <TENANT_GUID> --workspace <WORKSPACE_GUID> \
        --report <REPORT_GUID> --page <REPORT_PAGE_NAME> --company "Contoso"

IDs come from the report URL in the Power BI service:
  https://app.powerbi.com/groups/<WORKSPACE>/reports/<REPORT>/<PAGE_NAME>?ctid=<TENANT>
Output: teams-app/build/sqdcp-teams-app.zip  (upload in Teams > Apps > Manage your apps >
Upload an app, or hand to your Teams admin for the org catalogue).
"""
import argparse
import json
import os
import zipfile

here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "teams-app")
ap = argparse.ArgumentParser()
ap.add_argument("--tenant", required=True)
ap.add_argument("--workspace", required=True)
ap.add_argument("--report", required=True)
ap.add_argument("--page", default="")
ap.add_argument("--company", default="Operations")
a = ap.parse_args()

text = open(os.path.join(here, "manifest.json"), encoding="utf-8").read()
for key, val in {"TENANT_ID": a.tenant, "WORKSPACE_ID": a.workspace, "REPORT_ID": a.report,
                 "PAGE_NAME": a.page, "COMPANY_NAME": a.company}.items():
    text = text.replace("{{" + key + "}}", val)
if not a.page:
    text = text.replace("&pageName=", "")
json.loads(text)  # fail fast on a broken manifest

os.makedirs(os.path.join(here, "build"), exist_ok=True)
out = os.path.join(here, "build", "sqdcp-teams-app.zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("manifest.json", text)
    z.write(os.path.join(here, "color.png"), "color.png")
    z.write(os.path.join(here, "outline.png"), "outline.png")
print("Built", out)
