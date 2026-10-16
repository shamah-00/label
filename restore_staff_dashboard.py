from pathlib import Path
import shutil
import django

django.setup()

from django.template.loader import get_template

source = Path(r"templates/staff/dashboard_backup_20261009_214955.html")

if not source.exists():
    print("Recovery file not found. Nothing changed.")
else:
    active_template = Path(get_template("staff/dashboard.html").origin.name)
    safety_copy = active_template.with_name(
        active_template.name + ".before_dashboard_recovery"
    )

    shutil.copy2(active_template, safety_copy)
    shutil.copy2(source, active_template)

    print("Dashboard restored from the October 9 backup.")
    print("Restored file:", active_template)
    print("Previous version saved at:", safety_copy)
