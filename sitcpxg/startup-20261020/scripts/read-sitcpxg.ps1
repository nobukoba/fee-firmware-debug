param([string[]]$Addresses = @('192.168.10.10','192.168.10.11'),
      [string]$OutputPath = (Join-Path $PSScriptRoot '../evidence/rbcp.json'))
$ErrorActionPreference = 'Stop'
# Read only the SiTCP-XG identifier at 0xFFFFFF08; never write registers.
$results = foreach ($address in $Addresses) {
    $client = [Net.Sockets.UdpClient]::new()
    try {
        $client.Client.ReceiveTimeout = 1000
        $client.Connect($address, 4660)
        [byte[]]$request = @(0xff,0xc0,1,4,0xff,0xff,0xff,8)
        $null = $client.Send($request, $request.Length)
        $peer = [Net.IPEndPoint]::new([Net.IPAddress]::Any,0)
        [byte[]]$response = $client.Receive([ref]$peer)
        $valid = $response.Length -eq 12
        if ($valid) {
            $valid = $response[0] -eq 0xff -and $response[1] -eq 0xc8
            foreach ($index in 2..7) { $valid = $valid -and $response[$index] -eq $request[$index] }
        }
        if (!$valid) { throw 'Invalid RBCP read acknowledgement' }
        $identifier = [Convert]::ToHexString($response[8..11])
        [pscustomobject]@{address=$address; status='ReadAcknowledged'; identifier=$identifier; sitcpxg=($identifier -eq '58544350')}
    } catch {
        [pscustomobject]@{address=$address; status='ReadFailed'; error=$_.Exception.Message}
    } finally { $client.Dispose() }
}
[ordered]@{measured_at=(Get-Date).ToString('o'); register='0xFFFFFF08'; operation='RBCP read only'; results=@($results)} |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$results | Format-Table
