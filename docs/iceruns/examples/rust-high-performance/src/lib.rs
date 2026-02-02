use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

#[derive(Deserialize)]
pub struct Input {
    pub numbers: Option<Vec<f64>>,
    pub iterations: Option<usize>,
}

#[derive(Serialize)]
pub struct Output {
    pub count: usize,
    pub sum: f64,
    pub average: f64,
    pub min: f64,
    pub max: f64,
    pub variance: f64,
    pub std_dev: f64,
    pub result: Vec<f64>,
    pub success: bool,
}

/// High-performance numerical computation
#[no_mangle]
pub extern "C" fn handler(input: &str) -> String {
    let parsed: Value = serde_json::from_str(input).unwrap_or(json!({}));

    // Extract numbers
    let numbers: Vec<f64> = parsed["numbers"]
        .as_array()
        .unwrap_or(&vec![])
        .iter()
        .filter_map(|v| v.as_f64())
        .collect();

    if numbers.is_empty() {
        return json!({
            "error": "numbers array is empty",
            "success": false
        })
        .to_string();
    }

    // Calculate statistics
    let count = numbers.len();
    let sum: f64 = numbers.iter().sum();
    let average = sum / count as f64;

    let (min, max) = numbers
        .iter()
        .fold((f64::INFINITY, f64::NEG_INFINITY), |(min, max), &x| {
            (min.min(x), max.max(x))
        });

    // Calculate variance
    let variance: f64 = numbers
        .iter()
        .map(|&x| {
            let diff = x - average;
            diff * diff
        })
        .sum::<f64>()
        / count as f64;

    let std_dev = variance.sqrt();

    // Sort and collect results
    let mut sorted = numbers.clone();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());

    let output = Output {
        count,
        sum,
        average,
        min,
        max,
        variance,
        std_dev,
        result: sorted,
        success: true,
    };

    serde_json::to_string(&output).unwrap()
}
