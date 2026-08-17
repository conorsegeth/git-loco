[Windows.Devices.Geolocation.Geolocator, Windows.Devices.Geolocation, ContentType=WindowsRuntime] | Out-Null
Add-Type -AssemblyName System.Runtime.WindowsRuntime

function Write-Result($obj) {
    $obj | ConvertTo-Json -Compress
    exit 0
}

try {
    $Locator = New-Object Windows.Devices.Geolocation.Geolocator
    $Locator.DesiredAccuracyInMeters = 10

    $AsyncOp = $Locator.GetGeopositionAsync()

    $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and
        $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
    })[0]
    $asTaskSpecific = $asTaskGeneric.MakeGenericMethod([Windows.Devices.Geolocation.Geoposition])
    $Task = $asTaskSpecific.Invoke($null, @($AsyncOp))

    if (-not $Task.Wait(15000)) {
        Write-Result @{ Status = "Timeout" }
    }

    $Position = $Task.Result
    Write-Result @{
        Status    = "Success"
        Latitude  = $Position.Coordinate.Point.Position.Latitude
        Longitude = $Position.Coordinate.Point.Position.Longitude
        Accuracy  = $Position.Coordinate.Accuracy
    }
}
catch {
    # .Wait() wraps the real exception in an AggregateException
    $inner = $_.Exception
    if ($inner.InnerException) { $inner = $inner.InnerException }

    if ($inner -is [System.UnauthorizedAccessException] -or
        $inner.GetType().Name -eq 'UnauthorizedAccessException') {
        Write-Result @{ Status = "PermissionDenied"; Message = "Location services are off or access is denied for this app." }
    }
    else {
        Write-Result @{ Status = "Error"; Message = $inner.Message }
    }
}