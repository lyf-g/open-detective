import structlog
import logging
import sys
from asgi_correlation_id import correlation_id

def add_correlation(logger, log_method, event_dict):
    if request_id := correlation_id.get():
        event_dict["request_id"] = request_id
    return event_dict

def configure_logger():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_correlation,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    
    # Add correlation ID filter to standard logging
    class CorrelationIdFilter(logging.Filter):
        def filter(self, record):
            cid = correlation_id.get()
            record.request_id = cid if cid else ""
            return True

    handler.addFilter(CorrelationIdFilter())
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s'
    ))

    root_logger = logging.getLogger()
    # Avoid duplicate logs if handler already exists
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

logger = structlog.get_logger()
