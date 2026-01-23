#!/usr/bin/env ruby
# Action container server for Ruby runtime (OpenWhisk /init and /run pattern)

require 'sinatra'
require 'json'

set :bind, '0.0.0.0'
set :port, 8080

$action_proc = nil

post '/init' do
  data = JSON.parse(request.body.read)
  code = data['code']
  handler = data['handler']

  # Write code to file
  File.write('/tmp/action.rb', code)

  # Load action
  require '/tmp/action'
  $action_proc = method(handler.split('.').last.to_sym)

  { status: 'ready' }.to_json
end

post '/run' do
  halt 400, { error: 'Action not initialized' }.to_json unless $action_proc

  input = JSON.parse(request.body.read)
  begin
    result = $action_proc.call(input)
    { result: result }.to_json
  rescue => e
    halt 500, { error: e.message }.to_json
  end
end
