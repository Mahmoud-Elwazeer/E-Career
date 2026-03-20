import json
from rest_framework.renderers import JSONRenderer


class CustomJSONRenderer(JSONRenderer):
    """
    Wraps every API response in a consistent envelope:
    {
        "success": true/false,
        "data": <payload>,
        "message": "...",
        "errors": null
    }
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None
        status_code = response.status_code if response else 200

        success = 200 <= status_code < 300

        # If the response is already enveloped (from our exception handler), pass it through
        if isinstance(data, dict) and "success" in data and "data" in data:
            return super().render(data, accepted_media_type, renderer_context)

        # If the response is an error dict (from DRF), put it in errors
        if not success and isinstance(data, dict):
            envelope = {
                "success": False,
                "data": None,
                "message": self._extract_message(data),
                "errors": data,
            }
        else:
            envelope = {
                "success": success,
                "data": data,
                "message": "",
                "errors": None,
            }

        return super().render(envelope, accepted_media_type, renderer_context)

    def _extract_message(self, data):
        """Extract a human-readable error message from DRF error dict."""
        if isinstance(data, dict):
            for key in ("detail", "non_field_errors", "message"):
                if key in data:
                    val = data[key]
                    if isinstance(val, list):
                        return str(val[0]) if val else "An error occurred."
                    return str(val)
        return "An error occurred."
