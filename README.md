# Cluster Watcher

Script to monitor GPU failures on the cluster, and send slack messages when these occur.

## Installation

First, pull the repo.
```
git clone https://github.com/fjclark/cluster_watcher.git
cd cluster_watcher
```

Now, create a .env file with the following contents:
```
SLACK_OAUTH_TOKEN=your_slack_oauth_token
SLACK_CHANNEL_ID=your_slack_channel_id
NOTIFIED="False"
```
The `NOTIFIED` variable is used to track whether a notification has been sent following a GPU failure, and avoids spamming the channel with repeated messages.

Finally, install globally with
```
pipx install .
```

## Use

To run on the command line:
```
gpu_check
```

More likely, you will want to run this as a cron job. To do this, open the crontab with
```
crontab -e
```
and add the following line to the end of the file to run it every 10 minutes:
```
*/10 * * * * <path to your gpu_check command>
```

After a failure is detected, it will set the .env variable `NOTIFIED` to "True", and will not send another message until this is reset to "False". After you've fixed the issue, reset this to False with
```
gpu_check --reset
```