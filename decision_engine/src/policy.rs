use crate::models::{Decision, PhysicsResultInput, SafetyState};

pub struct DecisionPolicy;

impl DecisionPolicy {
    /// Evaluate security policy on PhysicsResultInput.
    /// Returns (Decision, Reason string).
    pub fn evaluate(input: &PhysicsResultInput) -> (Decision, String) {
        let (decision, base_reason) = match input.safety_state {
            SafetyState::Safe => (
                Decision::Allow,
                format!("Physical parameters within safe boundaries. (Risk Score: {:.1})", input.risk_score),
            ),
            SafetyState::Warning => (
                Decision::Monitor,
                format!("Physical parameters approaching safety limits. Elevated monitoring required. (Risk Score: {:.1})", input.risk_score),
            ),
            SafetyState::Critical => (
                Decision::Block,
                format!("CRITICAL PHYSICAL SAFETY BREACH: Safety limits approaching threshold. Command execution blocked. (Risk Score: {:.1})", input.risk_score),
            ),
            SafetyState::Catastrophic => (
                Decision::BlockCritical,
                format!("CATASTROPHIC PHYSICAL THREAT: Severe safety limit violation detected. Emergency block initiated. (Risk Score: {:.1})", input.risk_score),
            ),
            SafetyState::Unknown => (
                Decision::BlockCritical,
                "Physical safety validation status UNKNOWN. Default fail-closed policy enforced.".to_string(),
            ),
        };

        // Append explicit physical violation details if available
        let reason = if !input.violations.is_empty() {
            let mut violation_msgs = Vec::new();
            for v in &input.violations {
                let desc = v.description.as_deref().unwrap_or("Limit exceeded");
                violation_msgs.push(format!("{}: actual={:.2}, limit={:.2} ({})", v.parameter.to_uppercase(), v.value, v.limit, desc));
            }
            format!("{} Violations: [{}]", base_reason, violation_msgs.join(" | "))
        } else if let Some(explanation) = &input.explanation {
            if !explanation.is_empty() {
                format!("{} Detail: {}", base_reason, explanation)
            } else {
                base_reason
            }
        } else {
            base_reason
        };

        (decision, reason)
    }
}
