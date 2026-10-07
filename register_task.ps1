# Register daily 09:00 update task (no admin needed)
$ErrorActionPreference = "Stop"
$dir  = $PSScriptRoot   # folder name has [0]; avoid wildcard path cmdlets
$bat  = Join-Path -Path $dir -ChildPath "daily_update.bat"
$logD = Join-Path -Path $dir -ChildPath "logs"
if (-not (Test-Path -LiteralPath $logD)) { New-Item -ItemType Directory -Path $logD | Out-Null }
$out  = Join-Path -Path $logD -ChildPath "task_status.txt"
try {
  $ErrorActionPreference = "Stop"
  if (-not (Test-Path -LiteralPath $bat)) { throw "daily_update.bat not found: $bat" }
  $action   = New-ScheduledTaskAction -Execute "cmd.exe" -Argument ("/c `"" + $bat + "`"") -WorkingDirectory $dir
  # 09:00 start, retry every hour until 18:00 (skips once today's update succeeded) + at logon
  $daily    = New-ScheduledTaskTrigger -Daily -At "09:00"
  $daily.Repetition = (New-ScheduledTaskTrigger -Once -At "09:00" -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Hours 9)).Repetition
  $logon    = New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
  $logon.Delay = "PT10M"
  $trigger  = @($daily, $logon)
  $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun -ExecutionTimeLimit (New-TimeSpan -Hours 1)
  $user     = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
  $principal= New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
  Register-ScheduledTask -TaskName "HeungalineDailyUpdate" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
  Write-Host "[OK] Task registered: HeungalineDailyUpdate (09:00, retry hourly until 18:00, and at logon)"
  Write-Host "     $bat"
} catch {
  Write-Host "[ERROR] $($_.Exception.Message)"
}
# status report for Claude
$t = Get-ScheduledTask -TaskName "HeungalineDailyUpdate" -ErrorAction SilentlyContinue
if ($t) {
  $i = $t | Get-ScheduledTaskInfo
  "Registered : yes" | Out-File -LiteralPath $out -Encoding utf8
  "Command    : $($t.Actions[0].Execute) $($t.Actions[0].Arguments)" | Out-File -LiteralPath $out -Append -Encoding utf8
  "Trigger    : $($t.Triggers[0].StartBoundary) every $($t.Triggers[0].Repetition.Interval) for $($t.Triggers[0].Repetition.Duration) + logon" | Out-File -LiteralPath $out -Append -Encoding utf8
  "State      : $($t.State)" | Out-File -LiteralPath $out -Append -Encoding utf8
  "LastRun    : $($i.LastRunTime)  result=$($i.LastTaskResult)" | Out-File -LiteralPath $out -Append -Encoding utf8
  "NextRun    : $($i.NextRunTime)" | Out-File -LiteralPath $out -Append -Encoding utf8
} else { "Registered : NO" | Out-File -LiteralPath $out -Encoding utf8 }
Get-Content -LiteralPath $out
