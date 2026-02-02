#!/usr/bin/env pwsh
<#
.SYNOPSIS
IceRuns Example: PowerShell Azure Automation

This example demonstrates Azure resource management patterns.

Handler: handler
Entrypoint: handler.ps1
#>

param([hashtable]$event)

try {
  # Extract parameters
  $resourceGroup = $event['resource_group'] ?? 'default-rg'
  $action = $event['action'] ?? 'status'
  $vmName = $event['vm_name'] ?? 'my-vm'

  # Process action
  $result = switch ($action) {
    'status' {
      @{
        resource_group = $resourceGroup
        vm_name = $vmName
        status = 'running'
        last_check = (Get-Date -Format 'u')
      }
    }

    'restart' {
      @{
        resource_group = $resourceGroup
        vm_name = $vmName
        action = 'restart_initiated'
        timestamp = (Get-Date -Format 'u')
      }
    }

    'stop' {
      @{
        resource_group = $resourceGroup
        vm_name = $vmName
        action = 'stop_initiated'
        timestamp = (Get-Date -Format 'u')
      }
    }

    default {
      @{
        error = "Unknown action: $action"
        allowed_actions = @('status', 'restart', 'stop')
      }
    }
  }

  $result['success'] = $true
  return $result
}
catch {
  return @{
    error = $_.Exception.Message
    success = $false
  }
}
