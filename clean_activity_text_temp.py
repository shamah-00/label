import html
from staff.models import StaffActivityLog

updated = 0

for log in StaffActivityLog.objects.all().iterator():
    fields_to_update = []

    for field in ("description", "action"):
        if hasattr(log, field):
            value = getattr(log, field)
            if isinstance(value, str):
                cleaned = html.unescape(value)

                if cleaned != value:
                    setattr(log, field, cleaned)
                    fields_to_update.append(field)

    if fields_to_update:
        log.save(update_fields=fields_to_update)
        updated += 1

print(f"SUCCESS: Cleaned {updated} activity records.")
