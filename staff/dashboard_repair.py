from django.apps import apps
from django.utils import timezone


def _model(app_label, name):
    try:
        return apps.get_model(app_label, name)
    except LookupError:
        return None


def _field_names(model):
    if model is None:
        return set()
    return {field.name for field in model._meta.get_fields()}


def _status_field(model):
    if model is None:
        return None
    names = _field_names(model)
    for candidate in ("status", "quote_status", "order_status", "state"):
        if candidate in names:
            return candidate
    return None


def _recent(model, limit=6):
    if model is None:
        return []
    names = _field_names(model)
    for field in (
        "created_at", "created", "date_created",
        "submitted_at", "timestamp", "updated_at", "id"
    ):
        if field in names:
            try:
                return list(model.objects.order_by("-" + field)[:limit])
            except Exception:
                pass
    try:
        return list(model.objects.all()[:limit])
    except Exception:
        return []


def _count_status(model, words):
    field = _status_field(model)
    if not field:
        return 0
    total = 0
    try:
        for value in model.objects.values_list(field, flat=True).distinct():
            normalized = str(value or "").strip().lower().replace("_", " ").replace("-", " ")
            if any(word in normalized for word in words):
                total += model.objects.filter(**{field: value}).count()
    except Exception:
        return 0
    return total


class DashboardCountsMiddleware:
    """
    Correct dashboard figures after the original view has supplied its context.
    Existing staff authentication and approval checks remain untouched.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_template_response(self, request, response):
        if request.path.rstrip("/") != "/staff":
            return response

        context = getattr(response, "context_data", None)
        if not isinstance(context, dict):
            return response

        template_names = []
        template = getattr(response, "template_name", None)
        if isinstance(template, str):
            template_names.append(template)
        elif isinstance(template, (list, tuple)):
            template_names.extend(item for item in template if isinstance(item, str))

        if template_names and not any("dashboard" in name.lower() for name in template_names):
            return response

        Product = _model("products", "Product")
        Order = _model("products", "Order")
        QuoteRequest = _model("products", "QuoteRequest")
        StaffProfile = _model("staff", "StaffProfile")
        StaffActivityLog = _model("staff", "StaffActivityLog")

        try:
            if Product:
                context["total_products"] = Product.objects.count()
                if "is_available" in _field_names(Product):
                    context["available_products"] = Product.objects.filter(is_available=True).count()
                elif "is_active" in _field_names(Product):
                    context["available_products"] = Product.objects.filter(is_active=True).count()
                else:
                    context["available_products"] = Product.objects.count()

            if QuoteRequest:
                context["total_quotes"] = QuoteRequest.objects.count()
                context["new_quotes"] = _count_status(
                    QuoteRequest, ("new", "pending", "submitted", "received")
                )
                context["reviewing_quotes"] = _count_status(
                    QuoteRequest, ("review", "in progress", "under consideration")
                )
                context["quoted_quotes"] = _count_status(
                    QuoteRequest, ("quoted", "quote sent", "quotation sent")
                )
                context["approved_quotes"] = _count_status(
                    QuoteRequest, ("approved", "accepted")
                )
                context["production_quotes"] = _count_status(
                    QuoteRequest, ("production", "printing", "manufacturing")
                )
                context["completed_quotes"] = _count_status(
                    QuoteRequest, ("completed", "complete", "delivered", "fulfilled")
                )
                context["recent_quotes"] = _recent(QuoteRequest)

            if Order:
                context["total_orders"] = Order.objects.count()

            if StaffProfile:
                context["approved_staff"] = StaffProfile.objects.filter(
                    status="approved"
                ).count() if "status" in _field_names(StaffProfile) else 0

                context["pending_staff"] = StaffProfile.objects.filter(
                    status="pending"
                ).count() if "status" in _field_names(StaffProfile) else 0

            if StaffActivityLog:
                context["recent_activity"] = _recent(StaffActivityLog, 8)

        except Exception:
            # Keep the original page available if a project-specific model differs.
            pass

        return response
