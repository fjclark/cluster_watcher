# Cluster Watcher

Script to monitor GPU failures on the cluster, and send slack messages when these occur.

## Installation
```
pipx install git+https://github.com/fjclark/cluster_watcher.git
```

## Use
First, ensure that you specify `SLACK_OAUTH_TOKEN` and `SLACK_CHANNEL_ID` in a `.env` file. Then, run the following on the command line to check for GPU failures:

On the command line:
```
gpu_check
```