use voltguard_decision_engine::engine::DecisionEngine;
use voltguard_decision_engine::interface::read_input;

fn main() {
    let input_json = read_input();
    let result = DecisionEngine::process_json(&input_json);

    let output_json = serde_json::to_string_pretty(&result)
        .unwrap_or_else(|_| "{\"decision\":\"BLOCK_CRITICAL\",\"reason\":\"Serialization error\"}".to_string());

    println!("{}", output_json);
}
