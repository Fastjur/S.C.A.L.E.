from django.shortcuts import render

from config import settings


def index(request):
    return render(
        request,
        "frontend/index.html",
        context={
            "auto_scale_charts": settings.get("MOCK_ENTSOE_API_CLIENT", False)
            == "squeezed",
        },
    )
