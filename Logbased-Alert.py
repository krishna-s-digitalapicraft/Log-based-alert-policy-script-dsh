import os
import requests
import json
from google.cloud import logging, monitoring_v3
from google.protobuf.duration_pb2 import Duration
from dotenv import load_dotenv
from pathlib import Path
dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)
# Authenticate with Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./Authentication.json"

# Initialize the logging client
client = logging.Client()

def fetch_private_file_from_github(repo_owner, repo_name, file_path, branch="main", token=None):
    """
    Fetches a file from a private GitHub repository using an access token.
    """
    if not token or len(token) < 20:
        raise Exception("Invalid GitHub token. Ensure it is set and correct.")
    
    # Construct the raw URL for the file
    raw_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/{file_path}"
    
    # Add the authorization header
    headers = {"Authorization": f"Bearer {token}"}

    # Send GET request to fetch the file
    response = requests.get(raw_url, headers=headers)

    if response.status_code == 200:
        return response.text
    elif response.status_code == 404:
        raise Exception(f"File not found at: {raw_url}. Check the repository, branch, or file path.")
    elif response.status_code == 401:
        raise Exception("Unauthorized. Check your token permissions.")
    else:
        raise Exception(f"Failed to fetch file: {response.status_code}, {response.text}")


def generate_error_log_filters(log_pattern):
    """
    Generate GCP log filters string only for error logs (severity = DEFAULT).
    """
    try:
        log_data = json.loads(log_pattern)
        if "logs" not in log_data or not isinstance(log_data["logs"], list):
            raise ValueError("Invalid JSON: Missing 'logs' array or it is not a list.")

        # Generate conditions for error logs
        error_filters = set()
        for log in log_data["logs"]:
            if log.get("severity") == "DEFAULT" and "textPayload" in log:
                text_payload = log["textPayload"]
                # Construct the filter condition for each error log
                error_filters.add(
                    'resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"dac-analytics-api\" AND resource.labels.location=\"europe-west4\"'
                )   

        return list(error_filters)

        response.raise_for_status()  # Automatically raises an HTTPError for bad responses.
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON log pattern.") from e
    
# Create GCP alert policy for error logs
def create_log_alert_policy(project_id, log_filters, alert_policy_name, notification_channel_id):
    """
    Creates a GCP log-based alert policy with multiple conditions for error logs.
    """
    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{project_id}"

def delete_existing_alert_policies(client, project_id, alert_policy_name):
    """
    Deletes existing alert policies with the given name.
    """
    project_name = f"projects/{project_id}"
    
    # List all alert policies
    policies = client.list_alert_policies(name=project_name)
    
    for policy in policies:
        if policy.display_name == alert_policy_name:
            client.delete_alert_policy(name=policy.name)
            print(f"Deleted existing alert policy: {policy.name}")

def create_log_alert_policy(project_id, log_filters, alert_policy_name, notification_channel_id):
    """
    Deletes existing alert policies with the same name and creates a new one.
    """
    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{project_id}"

    # Step 1: Delete existing policies with the same name
    delete_existing_alert_policies(client, project_id, alert_policy_name)
        
    # Create a condition for each error log filter
    conditions = []
    for idx, log_filter in enumerate(log_filters['logs']):
            condition = monitoring_v3.AlertPolicy.Condition(
                display_name=f"Error Log Condition {idx + 1}",
                condition_matched_log=monitoring_v3.AlertPolicy.Condition.LogMatch(
                    filter=f'SEARCH(\"{log_filters["logs"][idx]["textPayload"]}\")', # Trigger if any matching log entry is found
                )
            )
            conditions = [condition]
            duration = Duration()
            duration.seconds = 3600 
                # Define the alert policy
            alert_strategy = monitoring_v3.AlertPolicy.AlertStrategy(
                    notification_rate_limit=monitoring_v3.AlertPolicy.AlertStrategy.NotificationRateLimit(
                        period=duration
                    )
                )
            alert_policy = monitoring_v3.AlertPolicy(
                    display_name=alert_policy_name,  # Combine conditions with OR
                    conditions=conditions,
                    combiner=monitoring_v3.AlertPolicy.ConditionCombinerType.OR,
                    notification_channels=[notification_channel_id],
                    enabled=True,
                    alert_strategy=alert_strategy
                )
            request = monitoring_v3.CreateAlertPolicyRequest(
                    name="projects/dac-analytics-hsbc",
                    alert_policy=alert_policy
                )

            # Make the request
            # Create the alert policy
            created_policy = client.create_alert_policy(name=notification_channel_id, alert_policy=alert_policy)
            print(f"Created Alert Policy: {created_policy.name}")

# Main script
if __name__ == "__main__":
    # GitHub repository details
    repo_owner = "digitalapicraft"
    repo_name = "dac-analytics-api"
    branch = "main" 
    file_path = "src/main/resources/cloud-monitoring/logs.json"
    
    # Retrieve GitHub token securely
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise Exception("GitHub token not found. Set it in your environment using 'export GITHUB_TOKEN=your_token'.")

    try:
        # Step 1: Fetch the private file from GitHub
        log_pattern = fetch_private_file_from_github(repo_owner, repo_name, file_path, branch, token)
        print("Fetched log pattern:", log_pattern)
        json_logs = json.loads(log_pattern)
        
        # Step 2: Generate error log filters
        error_filters = generate_error_log_filters(log_pattern)
        if not error_filters:
            raise Exception("No error logs found in the provided JSON log pattern.")
        print("Generated Error Filters:", error_filters)

        # Step 3: Create a GCP alert policy
        project_id = os.getenv('project_id')
        print(project_id)
        alert_policy_name = "dac-analytics-api-alerts"
        notification_channel_id = f'projects/dac-analytics-hsbc/notificationChannels/{os.getenv("notification_channel_id")}'
        
        create_log_alert_policy(project_id, json_logs, alert_policy_name, notification_channel_id)
    except Exception as e:
        print(f"Error: {e}")