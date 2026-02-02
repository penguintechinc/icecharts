#!/bin/bash
#
# IceRuns Example: Bash File Converter
#
# This example demonstrates file format conversion.
#
# Handler: handler
# Entrypoint: handler.sh

# Input is passed as JSON string in $1
input_json="$1"

# Parse with jq (always available in IceRuns)
input_file=$(echo "$input_json" | jq -r '.input_file // "input.txt"')
output_format=$(echo "$input_json" | jq -r '.format // "json"')

# Validate input
if [ -z "$input_file" ]; then
  echo '{"error": "input_file required", "success": false}'
  exit 0
fi

# Perform conversion based on format
case "$output_format" in
  json)
    # Convert to JSON format
    output=$(echo "$input_json" | jq '{
      original_input: .,
      converted_format: "json",
      timestamp: now | todate,
      success: true
    }')
    echo "$output"
    ;;

  csv)
    # Simple CSV conversion
    output=$(echo "$input_json" | jq -r '[
      "key,value",
      "timestamp," + (now | todate),
      "format,csv"
    ] | join("\n")')
    echo "{\"csv_output\": $(echo "$output" | jq -Rs .), \"success\": true}"
    ;;

  xml)
    # Simple XML conversion
    output="<root><timestamp>$(date -u +%Y-%m-%dT%H:%M:%SZ)</timestamp><format>xml</format></root>"
    echo "{\"xml_output\": $(echo "$output" | jq -Rs .), \"success\": true}"
    ;;

  *)
    echo "{\"error\": \"unsupported format: $output_format\", \"success\": false}"
    exit 1
    ;;
esac
