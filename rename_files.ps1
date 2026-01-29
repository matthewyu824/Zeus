$folderPath = "D:\Zeus\话术文件"
$files = Get-ChildItem -Path $folderPath -File | Sort-Object Name

$counter = 1
foreach ($file in $files) {
    $newName = "{0:000}_{1}" -f $counter, $file.Name
    $newPath = Join-Path -Path $folderPath -ChildPath $newName
    Rename-Item -Path $file.FullName -NewName $newName
    Write-Host "重命名: $($file.Name) -> $newName"
    $counter++
}