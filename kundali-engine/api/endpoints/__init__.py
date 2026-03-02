"""
API endpoint modules - routers for different functional areas
"""
from .common import router as common_router
from .kundli import router as kundli_router
from .charts import router as charts_router
from .calculators import router as calculators_router
from .specialized import router as specialized_router
from .dasha import router as dasha_router
from .gochar import router as gochar_router

__all__ = [
    'common_router',
    'kundli_router',
    'charts_router',
    'calculators_router',
    'specialized_router',
    'dasha_router',
    'gochar_router',
]
