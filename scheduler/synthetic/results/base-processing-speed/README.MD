These results are only relevant per system, if running on a new system, the base processing speed should be gathered
again for that system. This is done by running automated data gathering by setting the following settings
in the [`settings.toml`](../../../settings.toml) file
```toml
AUTOMATED_DATA_GATHERING = true
AUTOMATED_DATA_GATHERING_STEP = "get-system-base-processing-speed"
```

Also, the results are dependent on the maximum concurrency setting in the 
[`settings.toml`](../../../settings.toml) file.
```toml
MAX_CONCURRENT_PROCESSORS = 4
```
