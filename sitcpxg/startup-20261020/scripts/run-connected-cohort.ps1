param(
    [Parameter(Mandatory)][pscredential]$Credential,
    [pscredential]$SwitchCredential,
    [ValidateSet('switch_already_on','switch_after_board')][string]$Condition = 'switch_already_on',
    [ValidateRange(1,30)][int]$TrialsPerBoard = 3,
    [ValidateRange(30,300)][int]$ObservationSeconds = 60,
    [int[]]$Outlets = @(1,2),
    [string]$OutputPath = ''
)
$ErrorActionPreference = 'Stop'
if (!$OutputPath) {
    $fileName = if ($Condition -eq 'switch_already_on') {'connected-cohort.json'} else {'switch-after-board-cohort.json'}
    $OutputPath = Join-Path $PSScriptRoot "../evidence/$fileName"
}
if (Test-Path -LiteralPath $OutputPath) { throw 'Output already exists; select a new evidence filename' }
if (@($Outlets | Where-Object { $_ -notin @(1,2) }).Count) { throw 'Only board outlets 1 and 2 are supported' }
$base = 'http://172.16.207.110'
$passwordHash = [Convert]::ToHexString([Security.Cryptography.SHA1]::HashData(
    [Text.Encoding]::UTF8.GetBytes($Credential.GetNetworkCredential().Password))).ToLowerInvariant()
$loginBody = @{username=$Credential.UserName;password=$passwordHash} | ConvertTo-Json -Compress
$login = Invoke-WebRequest "$base/login.cgi" -Method Post -ContentType 'application/json' -Body $loginBody -SessionVariable powerSession -TimeoutSec 5
if (($login.Content | ConvertFrom-Json).result -ne 'ok') { throw 'Controller login failed' }
$page = Invoke-WebRequest "$base/status.htm" -WebSession $powerSession -TimeoutSec 5
$csrf = [regex]::Match($page.Content, 'id="csrftoken" value="([^"]+)"').Groups[1].Value
if (!$csrf) { throw 'Controller CSRF token missing' }
function Get-PowerState {
    $state = Invoke-RestMethod "$base/status_json.cgi" -WebSession $powerSession -TimeoutSec 5
    if (@($state.outlets).Count -ne 2) { throw 'Unexpected controller outlet count' }
    return $state
}
function Set-BoardPower([int]$Outlet, [bool]$Enabled) {
    $state = Get-PowerState
    if ([bool]$state.outlets[$Outlet-1].status -eq $Enabled) { return }
    # control=2 is the toggle used by this controller's own status-page JavaScript.
    # Never retry an ambiguous toggle. Read actual state before any further action.
    $stamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    try {
        $null = Invoke-WebRequest "$base/control.cgi?target=$Outlet&control=2&time=$stamp&csrftoken=$csrf" -WebSession $powerSession -TimeoutSec 5
    } catch {
        Write-Output "Controller request uncertain; checking actual state for outlet $Outlet"
    }
    foreach ($attempt in 1..5) {
        Start-Sleep -Seconds 1
        $state = Get-PowerState
        if ([bool]$state.outlets[$Outlet-1].status -eq $Enabled) { return }
    }
    throw "Outlet $Outlet did not reach requested power state $Enabled"
}
function Read-Identifier([string]$Address, [byte]$Sequence) {
    $client = [Net.Sockets.UdpClient]::new()
    try {
        $client.Client.ReceiveTimeout = 800
        $client.Connect($Address,4660)
        [byte[]]$request = @(255,192,$Sequence,4,255,255,255,8)
        $null = $client.Send($request,8)
        $peer = [Net.IPEndPoint]::new([Net.IPAddress]::Any,0)
        [byte[]]$response = $client.Receive([ref]$peer)
        if ($response.Length -ne 12 -or $response[0] -ne 255 -or $response[1] -ne 200) { return $false }
        foreach ($index in 2..7) { if ($response[$index] -ne $request[$index]) { return $false } }
        return [Convert]::ToHexString($response[8..11]) -eq '58544350'
    } catch { return $false } finally { $client.Dispose() }
}
function Get-SwitchPower {
    $switchPage = Invoke-WebRequest 'http://172.16.207.91/overview' -Authentication Basic -AllowUnencryptedAuthentication -Credential $SwitchCredential -TimeoutSec 5
    $match = [regex]::Match($switchPage.Content, 'name="o_sta">(On|Off)</td>')
    if (!$match.Success) { throw 'Cannot read switch outlet state' }
    if ($switchPage.Content -notmatch 'Manual Control') { throw 'Switch controller is not in manual mode' }
    return $match.Groups[1].Value -eq 'On'
}
function Set-SwitchPower([bool]$Enabled) {
    if ((Get-SwitchPower) -eq $Enabled) { return }
    $value = if ($Enabled) {'ON'} else {'OFF'}
    try {
        $null = Invoke-WebRequest "http://172.16.207.91/overview?onoff=$value" -Authentication Basic -AllowUnencryptedAuthentication -Credential $SwitchCredential -TimeoutSec 5
    } catch {
        Write-Output 'Switch request response uncertain; verifying actual outlet state'
    }
    foreach ($attempt in 1..5) {
        Start-Sleep -Seconds 1
        if ((Get-SwitchPower) -eq $Enabled) { return }
    }
    throw "Switch outlet did not reach requested state $Enabled"
}
if ($Condition -eq 'switch_after_board') {
    if (!$SwitchCredential) { throw 'SwitchCredential is required for switch power trials' }
    if (!(Get-SwitchPower)) { throw 'Switch outlet must initially be on' }
}
$initial = Get-PowerState
if ($initial.uis) { throw 'Automatic UIS power control is enabled; cannot perform controlled trials' }
if (!$initial.outlets[0].status -or !$initial.outlets[1].status) { throw 'Both board outlets must initially be on' }
$report = [ordered]@{
    started_at=(Get-Date).ToString('o'); condition=$Condition; cables='Left connected';
    firmware='Existing running images; not reprogrammed'; off_seconds=15; observation_seconds=$ObservationSeconds;
    success_criterion='3 consecutive valid SiTCP-XG identifier reads at >=1 second intervals';
    initial_power=@($initial.outlets | Select-Object name,status); trials=@(); completed=$false
}
function Save-Report { $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8 }
Save-Report
$activeOutlet = 0
try {
    foreach ($outlet in $Outlets) {
        $address = if ($outlet -eq 1) {'192.168.10.10'} else {'192.168.10.11'}
        foreach ($number in 1..$TrialsPerBoard) {
            $activeOutlet = $outlet
            $trial = [ordered]@{outlet=$outlet;address=$address;trial=$number;started_at=(Get-Date).ToString('o');samples=@();result='in_progress'}
            $report.trials += $trial
            Save-Report
            Write-Output "OUTLET $outlet TRIAL $number POWER OFF"
            Set-BoardPower $outlet $false
            $trial.off_confirmed_at=(Get-Date).ToString('o')
            Save-Report
            if ($Condition -eq 'switch_after_board') {
                Set-SwitchPower $false
                $trial.switch_off_confirmed_at=(Get-Date).ToString('o')
            }
            Save-Report
            Start-Sleep -Seconds 15
            Set-BoardPower $outlet $true
            $trial.on_confirmed_at=(Get-Date).ToString('o')
            if ($Condition -eq 'switch_after_board') {
                Start-Sleep -Seconds 15
                Set-SwitchPower $true
                $trial.switch_on_confirmed_at=(Get-Date).ToString('o')
            }
            Save-Report
            Write-Output "OUTLET $outlet TRIAL $number POWER ON; observing $address"
            $watch = [Diagnostics.Stopwatch]::StartNew()
            $consecutive = 0
            $sequence = 0
            while ($watch.Elapsed.TotalSeconds -lt $ObservationSeconds) {
                $sequence = ($sequence + 1) % 256
                $success = Read-Identifier $address ([byte]$sequence)
                $sample = [ordered]@{elapsed_seconds=[Math]::Round($watch.Elapsed.TotalSeconds,3);valid_identifier=$success}
                $trial.samples += $sample
                if ($success) {
                    if (!$trial.Contains('first_response_seconds')) { $trial.first_response_seconds=$sample.elapsed_seconds }
                    $consecutive++
                } else { $consecutive=0 }
                if ($consecutive -ge 3) { $trial.result='success'; break }
                Start-Sleep -Seconds 1
            }
            if ($trial.result -eq 'in_progress') { $trial.result="no_stable_response_within_${ObservationSeconds}_seconds" }
            $trial.final_power_on=[bool](Get-PowerState).outlets[$outlet-1].status
            $trial.finished_at=(Get-Date).ToString('o')
            Save-Report
            Write-Output "OUTLET $outlet TRIAL $number RESULT $($trial.result)"
        }
    }
    $report.completed=$true
} catch {
    if ($trial -and $trial.result -eq 'in_progress') { $trial.result='aborted_before_valid_measurement' }
    $report.error=$_.Exception.Message
    throw
} finally {
    try {
        if ($Condition -eq 'switch_after_board') { Set-SwitchPower $true }
    } catch { $report.switch_restore='unconfirmed' }
    try {
        if ($activeOutlet -ne 0) { Set-BoardPower $activeOutlet $true }
    } catch { $report.board_restore='unconfirmed' }
    finally {
        $report.finished_at=(Get-Date).ToString('o')
        Save-Report
    }
}
