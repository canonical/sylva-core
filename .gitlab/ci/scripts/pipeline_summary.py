#!/usr/bin/env python

import os
import requests
import logging

GITLAB_API_TOKEN = os.getenv("GITLAB_GUEST_TOKEN")
GITLAB_PROJECT_ID = os.getenv("CI_PROJECT_ID")
GITLAB_MR_ID = os.getenv("CI_MERGE_REQUEST_IID")
PARENT_PIPELINE_ID = os.getenv("DEPLOYMENT_JOBS_PIPELINE_ID")
GITLAB_API_URL = os.getenv("CI_API_V4_URL", "https://gitlab.com/api/v4")
UPDATE_SUMMARY = os.getenv("UPDATE_SUMMARY")

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

logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)


def get_mr_comments(project_id, mr_id):
    """Retrieve all comments for a given MR, handling pagination."""
    url = f"{GITLAB_API_URL}/projects/{project_id}/merge_requests/{mr_id}/notes"
    all_comments = []
    page = 1

    logging.info(f"Retrieve all comments for MR {mr_id}")

    while True:
        response = requests.get(url, headers=HEADERS, params={"page": page})
        response.raise_for_status()

        comments = response.json()
        all_comments.extend(comments)

        if 'X-Next-Page' in response.headers and response.headers['X-Next-Page']:
            page += 1
        else:
            break

    return all_comments


def get_current_user():
    """Retrieve the current GitLab user."""

    logging.info("Retrieve current gitlab user")

    url = f"{GITLAB_API_URL}/user"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_pipeline_bridges(project_id, pipeline_id):
    """Retrieve all trigger jobs (bridges) for a given pipeline."""

    logging.info(f"Retrieve all trigger jobs for pipeline {pipeline_id}")

    url = f"{GITLAB_API_URL}/projects/{project_id}/pipelines/{pipeline_id}/bridges"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_pipeline_jobs(project_id, pipeline_id):
    """Retrieve all jobs for a given pipeline."""

    logging.info(f"Retrieve all jobs for pipeline {pipeline_id}")

    url = f"{GITLAB_API_URL}/projects/{project_id}/pipelines/{pipeline_id}/jobs"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def calculate_pipeline_status(jobs, current_job_id):
    """Calculate the status of the pipeline based on job statuses."""

    logging.info("Check status of all jobs")

    for job in jobs:
        if job["id"] != current_job_id and job["status"] != "success":
            return "failed"
    return "success"


def post_mr_comment(project_id, mr_id, comment):
    """Post a new comment on the MR."""

    logging.info(f"Post a new comment on MR {mr_id}")

    url = f"{GITLAB_API_URL}/projects/{project_id}/merge_requests/{mr_id}/notes"
    payload = {"body": comment}
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()


def edit_mr_comment(project_id, mr_id, comment_id, comment):
    """Edit an existing MR comment."""

    logging.info(f"Edit comment {comment_id} on MR {mr_id}")

    url = f"{GITLAB_API_URL}/projects/{project_id}/merge_requests/{mr_id}/notes/{comment_id}"
    payload = {"body": comment}
    response = requests.put(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()


def delete_mr_comment(project_id, mr_id, comment_id):
    """Edit an existing MR comment."""

    logging.info(f"Delete comment {comment_id} on MR {mr_id}")

    url = f"{GITLAB_API_URL}/projects/{project_id}/merge_requests/{mr_id}/notes/{comment_id}"
    response = requests.delete(url, headers=HEADERS)
    response.raise_for_status()
    return response


def format_table(bridges):
    """Generate the Markdown table."""

    logging.info("Generate updated table")

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
            if UPDATE_SUMMARY:
                downstream_pipeline_id = downstream_pipeline.get("id")
                if downstream_pipeline_id == int(os.getenv("CI_PIPELINE_ID")):
                    logging.info(f"Updating pipeline {downstream_pipeline_id} status based on jobs status")
                    jobs = get_pipeline_jobs(GITLAB_PROJECT_ID, os.getenv("CI_PIPELINE_ID"))
                    status = calculate_pipeline_status(jobs, int(os.getenv("CI_JOB_ID", "0")))
                    status_icon = STATUS_ICON.get(status, "❔")
        else:
            link = "N/A"

        table += f"| {name} | {status_icon} | {link} |\n"
    return table


def main():
    current_user = get_current_user()
    current_user_id = current_user["id"]

    bridges = get_pipeline_bridges(GITLAB_PROJECT_ID, PARENT_PIPELINE_ID)

    new_comment_body = format_table(bridges)

    comments = get_mr_comments(GITLAB_PROJECT_ID, GITLAB_MR_ID)
    user_comments = [comment for comment in comments if comment["author"]["id"] == current_user_id]

    if len(user_comments) == 0:
        logging.info(f"No comment found for MR {GITLAB_MR_ID}, posting a new one")
        post_mr_comment(GITLAB_PROJECT_ID, GITLAB_MR_ID, new_comment_body)
    elif len(user_comments) == 1:
        logging.info(f"One comment found for MR {GITLAB_MR_ID}, updating it")
        existing_comment = user_comments[0]
        edit_mr_comment(
            GITLAB_PROJECT_ID,
            GITLAB_MR_ID,
            existing_comment["id"],
            new_comment_body
        )
    else:
        # This case happens sometimes when we have a race condition
        #  between multiple autostarted pipelines
        logging.info(f"Multiple comments found for MR {GITLAB_MR_ID}, cleaning them and updating the latest")
        edit_mr_comment(
            GITLAB_PROJECT_ID,
            GITLAB_MR_ID,
            user_comments[0]["id"],
            new_comment_body
        )
        for comment in user_comments[1:]:
            delete_mr_comment(
                GITLAB_PROJECT_ID,
                GITLAB_MR_ID,
                comment["id"]
            )


if __name__ == "__main__":
    main()
