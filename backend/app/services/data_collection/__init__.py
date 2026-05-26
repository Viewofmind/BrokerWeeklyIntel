"""
Legacy stub location.

The real Data Collection Layer now lives at:

    backend/app/data_collection/

Please import from there going forward:

    from app.data_collection.collector import DataCollector, run_weekly_collection
    from app.data_collection.models import ...

This directory is kept only for backward compatibility during the transition.
"""

from app.data_collection import *  # re-export for convenience during migration
