#!/usr/bin/env python

import os
import requests
import logging
from collections import defaultdict

GITLAB_API_TOKEN = os.getenv("GITLAB_GUEST_TOKEN")
GITLAB_PROJECT_ID = os.getenv("CI_PROJECT_ID")
GITLAB_MR_ID = os.getenv("CI_MERGE_REQUEST_IID")
DEPLOYMENT_JOBS_PIPELINE_ID = os.getenv("DEPLOYMENT_JOBS_PIPELINE_ID")
TOP_LEVEL_PIPELINE_ID = os.getenv("TOP_LEVEL_PIPELINE_ID")
GITLAB_API_URL = os.getenv("CI_API_V4_URL", "https://gitlab.com/api/v4")
UPDATE_SUMMARY = os.getenv("UPDATE_SUMMARY")


HEADERS = {
    "Private-Token": GITLAB_API_TOKEN
}

STATUS_ICON = {
    "failed": "❌",
    "success": "✅",
    "allowed_to_fail": "⚠️",
    "canceled": "🚫",
    "skipped": "⏩",
    "running": "🔄",
    "created": "🆕",
    "waiting_for_resource": "🔒",
    "preparing": "👀",
    "pending": "⏸️",
    "manual": "⚙️",
    "scheduled": "🕒",
}

logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)


def is_last_pipeline(project_id, mr_id):
    """Check if current pipeline is the last one from current MR."""
    url = f"{GITLAB_API_URL}/projects/{project_id}/merge_requests/{mr_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return str(response.json()["head_pipeline"]["id"]) == TOP_LEVEL_PIPELINE_ID


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


def get_pipeline_details(project_id, pipeline_id):
    """Fetch pipeline details"""

    url = f"{GITLAB_API_URL}/projects/{project_id}/pipelines/{pipeline_id}"
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
    all_jobs = []
    page = 1

    while True:
        response = requests.get(url, headers=HEADERS, params={"page": page})
        response.raise_for_status()

        jobs = response.json()
        all_jobs.extend(jobs)

        if 'X-Next-Page' in response.headers and response.headers['X-Next-Page']:
            page += 1
        else:
            break
    return all_jobs


def calculate_pipeline_status(jobs):
    """Calculate the status of the pipeline based on job statuses."""

    logging.info("Check status of all jobs")

    for job in jobs:
        # Consider the pipeline as failed if any job is failed
        if job["status"] == "failed":
            return "failed"
        # exclude summary jobs
        if job["name"] in {"initialize-summary", "update-summary"}:
            continue
        # else if any jobs is running, scheduled etc.. we consider the pipeline as still running
        if job["status"] in {"running", "pending", "scheduled", "created"}:
            return "running"
    # else it's a success
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
    """Delete an existing MR comment."""

    logging.info(f"Delete comment {comment_id} on MR {mr_id}")

    url = f"{GITLAB_API_URL}/projects/{project_id}/merge_requests/{mr_id}/notes/{comment_id}"
    response = requests.delete(url, headers=HEADERS)
    response.raise_for_status()
    return response


def format_jobs(jobs):
    """Format jobs grouped by stage with relevant titles."""

    logging.info("Formating jobs grouped by stage with relevant titles")

    grouped_jobs = defaultdict(list)

    ignored_jobs = {"create-runner", "create-runner-wait"}
    ignored_stages = {".pre", ".post", "cleanup"}

    for job in sorted(jobs, key=lambda d: d['stage']):
        if job["name"] in ignored_jobs and job["status"] != "failed":
            continue
        if job["stage"] in ignored_stages:
            continue
        if job["stage"] == "delete" and job["status"] != "failed":
            continue
        grouped_jobs[job["stage"]].append(job)

    formatted_output = ""
    for stage, jobs in grouped_jobs.items():
        formatted_output += f"**{stage.capitalize()} Stage**<br>"
        for job in sorted(jobs, key=lambda j: j["name"]):
            status_icon = STATUS_ICON.get(job["status"], "❔")
            formatted_output += f"[{job['name']} {status_icon}]({job['web_url']})<br>"
        formatted_output += "<br>"

    return formatted_output


def format_table(bridges):
    """Generate the Markdown table."""

    logging.info("Generate updated table")
    parent_pipeline_detail = get_pipeline_details(GITLAB_PROJECT_ID, DEPLOYMENT_JOBS_PIPELINE_ID)
    parent_pipeline_url = parent_pipeline_detail["web_url"]
    table = f"## Deployment pipelines from [{DEPLOYMENT_JOBS_PIPELINE_ID}]({parent_pipeline_url})\n"
    table += "| Pipeline Name | Status | Link |\n"
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
            downstream_pipeline_id = downstream_pipeline.get("id")
            logging.info(f"Updating pipeline {downstream_pipeline_id} status based on jobs status")
            jobs = get_pipeline_jobs(GITLAB_PROJECT_ID, int(downstream_pipeline_id))
            job_detail = "<details><summary>Details</summary>" + format_jobs(jobs) + "</details>"
            status = calculate_pipeline_status(jobs)
            status_icon = STATUS_ICON.get(status, "❔")
        else:
            link = "N/A"
            job_detail = ""
        table += f"| {name} | {status_icon} | {link}  {job_detail} |\n"
    return table


def main():
    current_user = get_current_user()
    current_user_id = current_user["id"]

    if not is_last_pipeline(GITLAB_PROJECT_ID, GITLAB_MR_ID):
        logging.info("Skipping because current pipeline is not the lastest one in the MR.")
        return

    comments = get_mr_comments(GITLAB_PROJECT_ID, GITLAB_MR_ID)
    user_comments = [comment for comment in comments if comment["author"]["id"] == current_user_id]

    if not DEPLOYMENT_JOBS_PIPELINE_ID:
        # We are in main pipeline, create a placeholder for deployment summary comment if it does not exist
        if len(user_comments) == 0:
            logging.info(f"No comment found for MR {GITLAB_MR_ID}, creating a placeholder")
            post_mr_comment(GITLAB_PROJECT_ID, GITLAB_MR_ID, "Placeholder for deployments pipelines summary")

        return

    bridges = get_pipeline_bridges(GITLAB_PROJECT_ID, DEPLOYMENT_JOBS_PIPELINE_ID)

    new_comment_body = format_table(bridges)

    if len(user_comments) == 0:
        logging.info(f"No comment found for MR {GITLAB_MR_ID}, posting a new one")
        post_mr_comment(GITLAB_PROJECT_ID, GITLAB_MR_ID, new_comment_body)
    else:
        logging.info(f"Existing comment(s) found for MR {GITLAB_MR_ID}, updating one (and removing others, if any)")
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
