param([string]$OutputPath = (Join-Path $PSScriptRoot '../evidence/network.json'))
$ErrorActionPreference = 'Stop'
$observations = foreach ($address in @('192.168.10.10', '192.168.10.11', '172.16.207.110', '172.16.207.91')) {
    $ping = [System.Net.NetworkInformation.Ping]::new()
    try {
        $reply = $ping.Send($address, 1000)
        [pscustomobject]@{ address = $address; status = [string]$reply.Status; roundtrip_ms = $reply.RoundtripTime }
    } catch {
        [pscustomobject]@{ address = $address; status = 'Error'; error = $_.Exception.Message }
    } finally { $ping.Dispose() }
}
$result = [ordered]@{
    measured_at = (Get-Date).ToString('o')
    mode = 'Read-only ICMP and local configuration; no power or firmware changes'
    ipv4 = @(Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias,IPAddress,PrefixLength)
    routes = @(Get-NetRoute -AddressFamily IPv4 | Select-Object DestinationPrefix,NextHop,InterfaceAlias,RouteMetric)
    ping = @($observations)
    neighbors = @(Get-NetNeighbor -AddressFamily IPv4 | Where-Object IPAddress -In @('192.168.10.10','192.168.10.11') | Select-Object IPAddress,LinkLayerAddress,State,InterfaceAlias)
}
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$observations | Format-Table
