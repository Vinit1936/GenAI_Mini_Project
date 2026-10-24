"""One-time extraction of the training artifact zips into ml-service/artifacts_extracted/.
Idempotent: skips zips that are already extracted, so replacing a zip (e.g. a retrained
NER model) is picked up automatically on the next service start."""
import os
import zipfile

from . import config

EXPECTED = {
    "role_classifier_artifacts.zip": "role_classifier",
    "resume_ner_artifacts.zip": "resume_ner",
    "section_classifier_artifacts.zip": "section_classifier",
}


def extract_all(force: bool = False) -> dict:
    """Unpack every artifact zip that has not been unpacked yet. Returns status per model."""
    os.makedirs(config.EXTRACT_DIR, exist_ok=True)
    status = {}
    for zip_name, folder in EXPECTED.items():
        zip_path = os.path.join(config.ARTIFACT_ZIPS, zip_name)
        dest = os.path.join(config.EXTRACT_DIR, folder)
        marker = os.path.join(dest, ".extracted_from")
        if not os.path.exists(zip_path):
            status[folder] = "zip missing"
            continue
        if os.path.exists(marker) and not force:
            with open(marker) as f:
                src = f.read().strip()
            if src == os.path.abspath(zip_path) and os.path.getmtime(zip_path) < os.path.getmtime(marker):
                status[folder] = "already extracted"
                continue
        if os.path.isdir(dest):
            import shutil
            shutil.rmtree(dest)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dest)
        with open(marker, "w") as f:
            f.write(os.path.abspath(zip_path))
        status[folder] = "extracted"
    return status
