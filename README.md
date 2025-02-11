# Log-based-alert-policy-script-dsh
Purpose of this script to automate the process of monitoring error logs in Google Cloud Platform (GCP) 

Main Funtions:
1.	Fetching a private JSON log file from a GitHub repository.
2.	Extracting error logs from the JSON data.
3.	Deleting existing GCP alert policies with the same name.
4.	Creating a new GCP alert policy based on error logs.

**•	Imports necessary libraries for interacting with GitHub, Google Cloud Logging & Monitoring, and handling JSON data.**
import os
import requests
import json
from google.cloud import logging, monitoring_v3
from google.protobuf.duration_pb2 import Duration
from dotenv import load_dotenv
from pathlib import Path

**•	Environment variables using dotenv / os.environ**
dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

# Sets up Google Cloud authentication using a service account key stored in Authentication.json
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./Authentication.json"

# Initialize the logging client
client = logging.Client()

# Fetching the log details from GitHub with the below condition :

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


# Generates GCP log filters for error logs (severity = DEFAULT) by GCP standard filter condition

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
    

# Delete the existing alert policies with the same name and creates a new one

"""
    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{project_id}"

    # Step 1: Delete existing policies with the same name
    delete_existing_alert_policies(client, project_id, alert_policy_name)
        
# Condition to create Log based Alert policy

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

            
# On Main function the project_id , notification_channel_id  been parameterized which to be refered from .env file

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


# Create a Env file pattern as below
  project_id=dac-analytics-hsbc
  notification_channel_id=5401153197620063180
