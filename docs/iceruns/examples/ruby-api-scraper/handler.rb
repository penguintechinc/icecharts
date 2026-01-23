#!/usr/bin/env ruby
#
# IceRuns Example: Ruby API Scraper
#
# This example demonstrates making HTTP requests and parsing JSON.
#
# Handler: handler
# Entrypoint: handler.rb

require 'httparty'
require 'json'

def handler(event)
  begin
    # Validate input
    url = event['url']
    raise 'url parameter required' unless url

    # Make HTTP request
    response = HTTParty.get(url, timeout: 10)

    # Check status
    unless response.success?
      return {
        error: "HTTP #{response.code}",
        success: false
      }
    end

    # Parse response
    data = if response.headers['content-type']&.include?('application/json')
      JSON.parse(response.body)
    else
      response.body
    end

    {
      status_code: response.code,
      headers: {
        content_type: response.headers['content-type'],
        content_length: response.headers['content-length']
      },
      body_preview: data.is_a?(String) ? data[0..100] : data.to_s[0..100],
      body_size: response.body.length,
      success: true
    }
  rescue StandardError => e
    {
      error: e.message,
      error_class: e.class.name,
      success: false
    }
  end
end

# Local testing
if __FILE__ == $PROGRAM_NAME
  result = handler('url' => 'https://api.github.com/users/octocat')
  puts JSON.pretty_generate(result)
end
