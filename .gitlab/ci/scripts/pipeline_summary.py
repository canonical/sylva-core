#!/usr/bin/env python

import os
import requests


GITLAB_API_TOKEN = os.getenv("GITLAB_GUEST_TOKEN")
GITLAB_PROJECT_ID = os.getenv("CI_PROJECT_ID")
GITLAB_MR_ID = os.getenv("CI_MERGE_REQUEST_IID")
PARENT_PIPELINE_ID = os.getenv("DEPLOYMENT_JOBS_PIPELINE_ID")
GITLAB_API_URL = os.getenv("CI_API_V4_URL", "https://gitlab.com/api/v4")

HEADERS = {
    "Private-Token": GITLAB_API_TOKEN
}

STATUS_ICON = {
    "failed": "❌",
    "success": "✔",
    "allowed_to_fail": "⚠️",
    "canceled": "🚫",
    "skipped": "⏩",
    "running": "🔄",
    "created": "⚙️",
    "waiting_for_resource": "🔒",
    "preparing": "👀",
    "pending": "⏸️",
    "manual": "⚙️",
    "scheduled": "🕒",
}


def get_mr_comments(project_id, mr_id):
    """Retrieve all comments for a given MR."""
    url = f"{GITLAB_API_URL}/projects/{project_id}/merge_requests/{mr_id}/notes"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_current_user():
    """Retrieve the current GitLab user."""
    url = f"{GITLAB_API_URL}/user"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_pipeline_bridges(project_id, pipeline_id):
    """Retrieve all trigger jobs (bridges) for a given pipeline."""
    url = f"{GITLAB_API_URL}/projects/{project_id}/pipelines/{pipeline_id}/bridges"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def post_mr_comment(project_id, mr_id, comment):
    """Post a new comment on the MR."""
    url = f"{GITLAB_API_URL}/projects/{project_id}/merge_requests/{mr_id}/notes"
    payload = {"body": comment}
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()


def edit_mr_comment(project_id, mr_id, comment_id, comment):
    """Edit an existing MR comment."""
    url = f"{GITLAB_API_URL}/projects/{project_id}/merge_requests/{mr_id}/notes/{comment_id}"
    payload = {"body": comment}
    response = requests.put(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()


def format_table(bridges):
    """Generate the Markdown table."""
    table = "| Pipeline Name | Status | Link |\n"
    table += "|---------------|--------|------|\n"
    for bridge in bridges:
        name = bridge.get("name", "Unknown")
        status = bridge.get("status", "unknown")
        status_icon = STATUS_ICON.get(status, "❔")
        # Handle cases where downstream_pipeline is null (Manual jobs, not started)
        downstream_pipeline = bridge.get("downstream_pipeline")
        if downstream_pipeline:
            url = downstream_pipeline.get("web_url", "N/A")
            link = f"[View Pipeline]({url})"
        else:
            link = "N/A"

        table += f"| {name} | {status_icon} | {link} |\n"
    return table


def main():
    current_user = get_current_user()
    current_user_id = current_user["id"]

    comments = get_mr_comments(GITLAB_PROJECT_ID, GITLAB_MR_ID)

    existing_comment = None
    for comment in comments:
        if comment["author"]["id"] == current_user_id:
            existing_comment = comment
            break

    bridges = get_pipeline_bridges(GITLAB_PROJECT_ID, PARENT_PIPELINE_ID)

    new_comment_body = format_table(bridges)

    if existing_comment:
        edit_mr_comment(
            GITLAB_PROJECT_ID,
            GITLAB_MR_ID,
            existing_comment["id"],
            new_comment_body
        )
    else:
        post_mr_comment(GITLAB_PROJECT_ID, GITLAB_MR_ID, new_comment_body)


if __name__ == "__main__":
    main()
