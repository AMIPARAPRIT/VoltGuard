use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Decision {
    Allow,
    Monitor,
    Block,
    BlockCritical,
}

impl std::fmt::Display for Decision {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Decision::Allow => write!(f, "ALLOW"),
            Decision::Monitor => write!(f, "MONITOR"),
            Decision::Block => write!(f, "BLOCK"),
            Decision::BlockCritical => write!(f, "BLOCK_CRITICAL"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum SafetyState {
    Safe,
    Warning,
    Critical,
    Catastrophic,
    Unknown,
}

impl std::fmt::Display for SafetyState {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SafetyState::Safe => write!(f, "SAFE"),
            SafetyState::Warning => write!(f, "WARNING"),
            SafetyState::Critical => write!(f, "CRITICAL"),
            SafetyState::Catastrophic => write!(f, "CATASTROPHIC"),
            SafetyState::Unknown => write!(f, "UNKNOWN"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ViolationDetail {
    pub parameter: String,
    pub value: f64,
    pub limit: f64,
    #[serde(default)]
    pub ratio: Option<f64>,
    #[serde(default)]
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhysicsResultInput {
    #[serde(default)]
    pub pump_rpm: Option<f64>,
    #[serde(default)]
    pub valve_position: Option<f64>,
    #[serde(default)]
    pub predicted_pressure: Option<f64>,
    #[serde(default)]
    pub predicted_flow: Option<f64>,
    #[serde(default)]
    pub predicted_temperature: Option<f64>,
    #[serde(default)]
    pub system_stress: Option<f64>,
    pub risk_score: f64,
    pub safety_state: SafetyState,
    #[serde(default)]
    pub violations: Vec<ViolationDetail>,
    #[serde(default)]
    pub explanation: Option<String>,
    #[serde(default)]
    pub simulation_time_ms: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecisionResult {
    pub decision: Decision,
    pub risk_score: f64,
    pub safety_state: SafetyState,
    pub reason: String,
    pub timestamp: String,
    pub decision_latency_us: u64,
}
