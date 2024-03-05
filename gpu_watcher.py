"""Script to check for GPU failures and respond if necessary."""

from dataclasses import dataclass, field
import os
import subprocess
from typing import Tuple, List
import requests
import json
from dotenv import load_dotenv, set_key


class EnvVarError(Exception):
    """Raised when an environment variable is not found."""

    ...


def run_remote_cmd(node_name: str, cmd: List[str]) -> Tuple[str, str]:
    """Run a command on a node in the cluster and return the stdout and stderr."""
    cmd = ["ssh", node_name] + cmd
    # Get both stdout and stderr
    stdout, stderr = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()
    return stdout.decode("utf-8"), stderr.decode("utf-8")


@dataclass
class Node:
    """A node in the GPU cluster."""

    name: str
    functional: bool = True
    error_information: dict = field(default_factory=dict)

    def check_gpus_functional(self) -> bool:
        """Check if the GPUs on this node are functional."""
        cmd = ["nvidia-smi"]
        stdout, stderr = run_remote_cmd(self.name, cmd)
        self.functional = not bool(stderr)
        # If there is an issue, save the error information
        if not self.functional:
            self.error_information["nvidia-smi"] = stderr
            # Also collect information with dmesg
            # cmd = ["sudo", "dmesg", "-T", "-l", "warn,err,crit"]
            # stdout, stderr = run_remote_cmd(self.name, cmd)
            # self.error_information["dmesg"] = stdout
        return self.functional


def load_from_env(name: str) -> str:
    """Load a value from the dotenv file."""
    load_dotenv()
    value = os.environ[name]
    if not value:
        raise EnvVarError(f"Environment variable {name} not found.")
    return value


def write_to_env(name: str, value: str) -> None:
    """Write a value to the dotenv file."""
    load_dotenv()
    set_key(".env", name, value)


def send_slack_message(token: str, channel: str, message: str) -> None:
    """Send a message to a Slack channel."""
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    data = {"channel": channel, "text": message}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Error: {response.text}")


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Check the nodes in the cluster for GPU issues."
    )
    # Option to reset the notification
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the notification flag to allow sending messages again.",
    )
    return parser.parse_args()


def main():
    """Check the nodes in the cluster for GPU issues."""
    # Check if we just want to reset the notification
    args = parse_args()
    if args.reset:
        write_to_env("NOTIFIED", "False")
        return

    # Check if we have already notified about the failure. If so
    # don't notify again.
    notified = load_from_env("NOTIFIED")
    if notified == "True":
        return

    # Check the nodes for GPU issues
    nodes = [Node(f"node0{i}") for i in range(1, 8)]
    failing_nodes = [node for node in nodes if not node.check_gpus_functional()]

    # Send slack message if there are failing nodes
    if failing_nodes:
        slack_token = load_from_env("SLACK_OAUTH_TOKEN")
        slack_channel = load_from_env("SLACK_CHANNEL_ID")
        # Send overall warning message.
        send_slack_message(slack_token, slack_channel, "GPU cluster failure detected!")
        # Send detailed message for each node.
        for node in failing_nodes:
            send_slack_message(
                slack_token,
                slack_channel,
                f"Node {node.name} failed with error: {node.error_information}",
            )
        # Set the environment variable to avoid sending multiple messages
        write_to_env("NOTIFIED", "True")


if __name__ == "__main__":
    main()
