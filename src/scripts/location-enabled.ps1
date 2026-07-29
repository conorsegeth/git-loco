# 1. Group Policy Check
$policyPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors"
$policy = Get-ItemProperty -Path $policyPath -Name "DisableLocation" -ErrorAction SilentlyContinue
if ($policy -and $policy.DisableLocation -eq 1) {
    Write-Output "POLICY_DISABLED"
    exit 1
}

# 2. Master System Toggle (HKLM)
$hklmPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location"
$hklmVal = Get-ItemPropertyValue -Path $hklmPath -Name "Value" -ErrorAction SilentlyContinue
if ($hklmVal -eq "Deny") {
    Write-Output "MASTER_DISABLED"
    exit 2
}

# 3. User Apps Toggle (HKCU)
$hkcuPath = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location"
$hkcuVal = Get-ItemPropertyValue -Path $hkcuPath -Name "Value" -ErrorAction SilentlyContinue
if ($hkcuVal -eq "Deny") {
    Write-Output "APPS_DISABLED"
    exit 3
}

# 4. Desktop Apps Toggle (HKCU NonPackaged)
$desktopPath = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location\NonPackaged"
$desktopVal = Get-ItemPropertyValue -Path $desktopPath -Name "Value" -ErrorAction SilentlyContinue
if ($desktopVal -eq "Deny") {
    Write-Output "DESKTOP_DISABLED"
    exit 4
}

# All toggles passed
Write-Output "ENABLED"
exit 0