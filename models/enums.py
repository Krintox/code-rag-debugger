# backend/models/enums.py
from enum import Enum

class SubscriptionPlan(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
