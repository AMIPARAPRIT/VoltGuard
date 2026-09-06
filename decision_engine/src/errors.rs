use chrono::Utc;
use crate::models::{Decision, DecisionResult, SafetyState};

pub fn build_fail_closed_result(err_msg: &str, latency_us: u64) -> DecisionResult {
    let timestamp = Utc::now().to_rfc3339();
    let reason = if err_msg.is_empty() {
        "Physical safety validation unavailable.".to_string()
    } else {
        format!("Physical safety validation unavailable. (Error: {})", err_msg)
    };

    DecisionResult {
        decision: Decision::BlockCritical,
        risk_score: 100.0,
        safety_state: SafetyState::Catastrophic,
        reason,
        timestamp,
        decision_latency_us: latency_us,
    }
}
