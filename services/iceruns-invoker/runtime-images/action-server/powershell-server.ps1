#!/usr/bin/env pwsh
# Action container server for PowerShell runtime (OpenWhisk /init and /run pattern)

$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add("http://*:8080/")
$listener.Start()

Write-Host "Action server listening on port 8080"

$actionScript = $null

while ($listener.IsListening) {
    $context = $listener.GetContext()
    $request = $context.Request
    $response = $context.Response

    if ($request.Url.AbsolutePath -eq "/init" -and $request.HttpMethod -eq "POST") {
        $reader = [System.IO.StreamReader]::new($request.InputStream)
        $body = $reader.ReadToEnd() | ConvertFrom-Json
        $actionScript = $body.code

        $output = @{ status = "ready" } | ConvertTo-Json
        $buffer = [System.Text.Encoding]::UTF8.GetBytes($output)
        $response.ContentLength64 = $buffer.Length
        $response.OutputStream.Write($buffer, 0, $buffer.Length)
    }
    elseif ($request.Url.AbsolutePath -eq "/run" -and $request.HttpMethod -eq "POST") {
        $reader = [System.IO.StreamReader]::new($request.InputStream)
        $input = $reader.ReadToEnd() | ConvertFrom-Json

        try {
            $result = Invoke-Expression $actionScript
            $output = @{ result = $result } | ConvertTo-Json
        }
        catch {
            $output = @{ error = $_.Exception.Message } | ConvertTo-Json
        }

        $buffer = [System.Text.Encoding]::UTF8.GetBytes($output)
        $response.ContentLength64 = $buffer.Length
        $response.OutputStream.Write($buffer, 0, $buffer.Length)
    }

    $response.Close()
}
