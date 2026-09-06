use std::time::Instant;
use chrono::Utc;
use crate::models::{DecisionResult, PhysicsResultInput};
use crate::policy::DecisionPolicy;
use crate::errors::build_fail_closed_result;

pub struct DecisionEngine;

impl DecisionEngine {
    /// Process physics result JSON string input and generate high-speed DecisionResult.
    pub fn process_json(json_str: &str) -> DecisionResult {
        let start = Instant::now();
        let timestamp = Utc::now().to_rfc3339();

        if json_str.trim().is_empty() {
            let elapsed = start.elapsed().as_micros() as u64;
            eprintln!("[DECISION] physics_result=UNAVAILABLE decision=BLOCK_CRITICAL reason=Physical safety validation unavailable");
            return build_fail_closed_result("Empty input received", elapsed);
        }

        let input: PhysicsResultInput = match serde_json::from_str(json_str) {
            Ok(parsed) => parsed,
            Err(e) => {
                let elapsed = start.elapsed().as_micros() as u64;
                eprintln!("[DECISION] physics_result=MALFORMED decision=BLOCK_CRITICAL reason=Physical safety validation unavailable");
                return build_fail_closed_result(&format!("JSON parse error: {}", e), elapsed);
            }
        };

        let (decision, reason) = DecisionPolicy::evaluate(&input);
        let elapsed_us = start.elapsed().as_micros() as u64;

        eprintln!(
            "[DECISION] safety_state={} risk_score={:.1} decision={} latency_us={}",
            input.safety_state, input.risk_score, decision, elapsed_us
        );

        DecisionResult {
            decision,
            risk_score: input.risk_score,
            safety_state: input.safety_state,
            reason,
            timestamp,
            decision_latency_us: elapsed_us,
        }
    }
}
