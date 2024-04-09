merge all .tsv file like this:
Get-ChildItem -Path . -Recurse -Include *.tsv -Exclude eval_names\* | ForEach-Object {
    Get-Content $_.FullName
} | Set-Content training_names.tsv