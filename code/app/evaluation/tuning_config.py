from pydantic import BaseModel, Field

class RuleCalibrationConfig(BaseModel):
    # Rule weight tuning targets
    RULE_SAFETY_DOMAIN_MISMATCH_WEIGHT: float = Field(1.0, ge=0.0, le=1.0)
    RULE_SAFETY_HIGH_FORWARD_WEIGHT: float = Field(0.9, ge=0.0, le=1.0)
    RULE_USER_DND_ACTIVE_WEIGHT: float = Field(0.95, ge=0.0, le=1.0)
    RULE_USER_GROUP_MUTED_WEIGHT: float = Field(1.0, ge=0.0, le=1.0)
    RULE_BUSINESS_PROMO_OPT_OUT_WEIGHT: float = Field(0.9, ge=0.0, le=1.0)
    RULE_BUSINESS_VERIFIED_TRUST_WEIGHT: float = Field(0.8, ge=0.0, le=1.0)
    RULE_MEDIA_PAYMENT_REQUEST_WEIGHT: float = Field(0.9, ge=0.0, le=1.0)
    RULE_MEDIA_QR_PRESENT_WEIGHT: float = Field(0.7, ge=0.0, le=1.0)
    RULE_RELATIONSHIP_FREQUENT_WEIGHT: float = Field(0.6, ge=0.0, le=1.0)
    RULE_SYSTEM_LOAD_ALERT_WEIGHT: float = Field(0.5, ge=0.0, le=1.0)

    # Decision engine cutoffs parameters
    DECISION_NOTIFY_THRESHOLD: float = Field(0.65, ge=0.0, le=1.0)
    DECISION_DIGEST_THRESHOLD: float = Field(0.45, ge=0.0, le=1.0)

# Global active tuning configurations
tuning_config = RuleCalibrationConfig()
