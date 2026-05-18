import re
from typing import Dict, Any

def format_sms_message(template: str, data: Dict[str, Any]) -> str:
    """
    Safely replace placeholders in a template with data.
    """
    try:
        return template.format(**data)
    except KeyError as e:
        import logging
        logging.getLogger(__name__).warning(f"Missing key for SMS template format: {e}")
        # Very basic fallback string replace if format fails
        result = template
        for k, v in data.items():
            result = result.replace("{" + k + "}", str(v))
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error formatting SMS template: {e}")
        return template
