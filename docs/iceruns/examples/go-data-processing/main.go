package main

import (
	"encoding/json"
	"fmt"
	"sort"
)

// Input represents the function input
type Input struct {
	Numbers []float64 `json:"numbers"`
	Action  string    `json:"action"`
}

// Output represents the function output
type Output struct {
	Count    int64   `json:"count"`
	Sum      float64 `json:"sum"`
	Average  float64 `json:"average"`
	Min      float64 `json:"min"`
	Max      float64 `json:"max"`
	Median   float64 `json:"median"`
	StdDev   float64 `json:"std_dev"`
	Sorted   []float64 `json:"sorted"`
	Success  bool    `json:"success"`
}

// Handler processes numeric data
func Handler(input Input) (Output, error) {
	// Validate input
	if len(input.Numbers) == 0 {
		return Output{Success: false}, fmt.Errorf("numbers array is empty")
	}

	output := Output{
		Count:   int64(len(input.Numbers)),
		Success: true,
	}

	// Calculate sum
	sum := 0.0
	for _, num := range input.Numbers {
		sum += num
	}
	output.Sum = sum
	output.Average = sum / float64(len(input.Numbers))

	// Find min and max
	min, max := input.Numbers[0], input.Numbers[0]
	for _, num := range input.Numbers {
		if num < min {
			min = num
		}
		if num > max {
			max = num
		}
	}
	output.Min = min
	output.Max = max

	// Sort numbers
	sorted := make([]float64, len(input.Numbers))
	copy(sorted, input.Numbers)
	sort.Float64s(sorted)
	output.Sorted = sorted

	// Calculate median
	if len(sorted)%2 == 0 {
		output.Median = (sorted[len(sorted)/2-1] + sorted[len(sorted)/2]) / 2
	} else {
		output.Median = sorted[len(sorted)/2]
	}

	// Calculate standard deviation
	variance := 0.0
	for _, num := range input.Numbers {
		diff := num - output.Average
		variance += diff * diff
	}
	variance /= float64(len(input.Numbers))
	output.StdDev = math.Sqrt(variance)

	return output, nil
}

// Required for IceRuns runtime
import "math"
