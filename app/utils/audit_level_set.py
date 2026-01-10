from app.models.audit_log_model import LogLevel


def level_from_status(code: int) -> LogLevel:
    if code >= 500:
        return LogLevel.CRITICAL
    if code >= 400:
        return LogLevel.ERROR
    if code >= 300:
        return LogLevel.WARNING
    return LogLevel.INFO
