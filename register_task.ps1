# Register daily 09:00 update task (no admin needed)
$ErrorActionPreference = "Stop"
$dir  = Split-Path -LiteralPath $MyInvocation.MyCommand.Path -Parent   # LiteralPath: folder name has [0]
$bat  = Join-Path -Path $dir -ChildPath "daily_update.bat"
$logD = Join-Path -Path $dir -ChildPath "logs"
if (-not (Test-Path -LiteralPath $logD)) { New-Item -ItemType Directory -Path $logD | Out-Null }
$out  = Join-Path -Path $logD -ChildPath "task_status.txt"
try {
  if (-not (Test-Path -LiteralPath $bat)) { throw "daily_update.bat not found: $bat" }
  $action   = New-ScheduledTaskAction -Execute "cmd.exe" -Argument ("/c `"" + $bat + "`"") -WorkingDirectory $dir
  $trigger  = New-ScheduledTaskTrigger -Daily -At "09:00"
  $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun -ExecutionTimeLimit (New-TimeSpan -Hours 1)
  $user     = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
  $principal= New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
  Register-ScheduledTask -TaskName "HeungalineDailyUpdate" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
  Write-Host "[OK] Task registered: HeungalineDailyUpdate (daily 09:00, runs later if PC was off)"
  Write-Host "     $bat"
} catch {
  Write-Host "[ERROR] $($_.Exception.Message)"
}
# status report for Claude
$t = Get-ScheduledTask -TaskName "HeungalineDailyUpdate" -ErrorAction SilentlyContinue
if ($t) {
  $i = $t | Get-ScheduledTaskInfo
  "Registered : yes" | Out-File -LiteralPath $out -Encoding ascii
  "Command    : $($t.Actions[0].Execute) $($t.Actions[0].Arguments)" | Out-File -LiteralPath $out -Append -Encoding ascii
  "Trigger    : $($t.Triggers[0].StartBoundary)" | Out-File -LiteralPath $out -Append -Encoding ascii
  "State      : $($t.State)" | Out-File -LiteralPath $out -Append -Encoding ascii
  "LastRun    : $($i.LastRunTime)  result=$($i.LastTaskResult)" | Out-File -LiteralPath $out -Append -Encoding ascii
  "NextRun    : $($i.NextRunTime)" | Out-File -LiteralPath $out -Append -Encoding ascii
} else { "Registered : NO" | Out-File -LiteralPath $out -Encoding ascii }
Get-Content -LiteralPath $out
