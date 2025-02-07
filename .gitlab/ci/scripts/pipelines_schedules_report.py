#!/bin/env python

import sys
import datetime
import os
import re

try:
    import gitlab
except ModuleNotFoundError:
    print("[ERROR] python-gitlab package not found", file=sys.stderr)
    print("[ERROR] it can be installed with: 'pip install --upgrade python-gitlab'", file=sys.stderr)
    sys.exit(1)

try:
    from tabulate import tabulate
except ModuleNotFoundError:
    print("[ERROR] tabulate package not found", file=sys.stderr)
    print("[ERROR] it can be installed with: 'pip install --upgrade tabulate'", file=sys.stderr)
    sys.exit(1)

REPORT_FILE = "report_output.md"

status_icon = {
    "failed": "❌",
    "success": "✔",
    "allowed_to_fail": "⚠️",
    "canceled": "🛇",
    "skipped": "⏩",
    "running": "🔄",
    "created": "𑀣",
    "waiting_for_resource": "🔒",
    "preparing": "👀",
    "pending": "⏸️",
    "manual": "⚙️",
    "scheduled": "🕒",
}


def get_status_icon(job):
    allow_failure = getattr(job, 'allow_failure', False)
    if job.status == "failed" and allow_failure is True:
        status = "allowed_to_fail"
    else:
        status = job.status
    return status_icon.get(status)


def normalize_older_pipeline_name(name):
    options = []
    option_match = re.compile(r"🛠️\s*([\w\d,-]+)").findall(name)
    if option_match:
        options = option_match[0].split(",")

    # if 'oci' in options, remove it to align with new jobs where 'oci' is implicit
    # and does not appear in the name anymore
    if 'oci' in options:
        options.remove('oci')
        name = re.sub(
            r'🛠️\s*([\w\d,-]+)',
            '🛠️' + ','.join(options),
            name
        )

    return name


def pipeline_summary(pipeline):
    if not pipeline:
        return "(no pipeline info)"

    pipeline = project.pipelines.get(pipeline["id"])

    summary = ""

    def _sort_jobs_by_starting_date(jobs):
        pending_jobs = [j for j in jobs if j.status == "pending"]
        executed_jobs = [j for j in jobs if hasattr(j, "started_at") and j.started_at]
        sorted_executed_jobs = sorted(
            executed_jobs,
            key=lambda x: datetime.datetime.strptime(
                x.started_at, "%Y-%m-%dT%H:%M:%S.%f%z"
            )
        )
        return sorted_executed_jobs + pending_jobs

    jobs = _sort_jobs_by_starting_date(pipeline.jobs.list(get_all=True))
    test_jobs = [j for j in jobs if j.stage == "deployment-test"]
    test_combined_md = ""

    # List of jobs to ignore if they suceed
    ignored_jobs = [
        "create-runner",
        "create-runner-wait",
        "🚨 dont-interrupt-me",
    ]
    for job in jobs:
        # Don't display jobs in if they are in ignored_jobs list and succeed
        if job.name in ignored_jobs and job.status == "success":
            continue
        # we don't care about displaying the cleanup stage if it worked
        if job.stage == "cleanup" and job.status == "success":
            continue
        if job not in test_jobs:
            job_text = f"{job.name.replace('-', '‑')}: {get_status_icon(job)}"
            job_md = f"[{job_text}]({job.web_url})<br>"
            summary += job_md
        else:
            if test_combined_md == "":
                test_combined_statuses = " ".join(
                    [get_status_icon(j) for j in test_jobs]
                )
                test_text = f"tests: {test_combined_statuses}"
                test_combined_md = f"[{test_text}]({pipeline.web_url})<br>"
                summary += test_combined_md

    # dumy line for padding to avoid ugly line breaks
    summary += "&#160;" * 60

    return summary


def create_report():
    with open(REPORT_FILE, "w") as report_fd:

        def print_report(text):
            print(text, file=report_fd)

        print_report(
            "**scheduled pipelines report produced at "
            + datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            + ".**"
        )
        print_report("")
        for pipeline_schedule in pipeline_schedules:

            if not pipeline_schedule.active:
                print(pipeline_schedule.description + "is not active, skipping")
                continue

            if pipeline_schedule_name not in pipeline_schedule.description:
                continue

            pipeline_description = pipeline_schedule.description

            print(f"processing pipeline schedule {pipeline_description}")

            schedules = project.pipelineschedules.get(pipeline_schedule.id)
            pipelines = schedules.pipelines.list(get_all=True)
            pipelines.reverse()
            newest_pipelines = pipelines[:PIPELINE_HISTORY_COUNT]

            print_report(f"## {pipeline_description}")
            print_report("")

            child_pipelines_reports = dict()
            success_counts = dict()
            total_counts = dict()
            last_success_dates = dict()

            def _get_child_md(child):
                duration_text = "unknown runtime"
                if child.duration:
                    duration_text = f"{child.duration / 60.0:.0f}min"
                ds_pipeline_summary = pipeline_summary(child.downstream_pipeline)
                return (
                    f"[{duration_text} {get_status_icon(child)}]({child.web_url})<br/>{ds_pipeline_summary}"
                    f"<br/>\\[[🕵️notes](https://gitlab.com/sylva-projects/sylva-core/-/wikis/sched-pipelines-notes/{child.id})\\]"
                )

            child_pipelines_reports = dict()
            for pipeline in newest_pipelines:
                print(f"  processing pipeline {pipeline.id}")
                for level1_child in project.pipelines.get(pipeline.id).bridges.list():
                    print(f"    processing child {level1_child.name}")
                    if level1_child.name == "deployment-jobs":
                        for level2_child in project.pipelines.get(level1_child.downstream_pipeline['id']).bridges.list():
                            print(f"      processing child {level2_child.name}")
                            child_pipeline_name = normalize_older_pipeline_name(level2_child.name)
                            child_pipelines_reports.setdefault(child_pipeline_name, dict())
                            child_pipelines_reports[child_pipeline_name][pipeline.id] = _get_child_md(level2_child)

                            # Count successes and total for each child pipeline
                            total_counts[child_pipeline_name] = total_counts.get(child_pipeline_name, 0) + 1
                            if level2_child.status == "success":
                                success_counts[child_pipeline_name] = success_counts.get(child_pipeline_name, 0) + 1
                                if child_pipeline_name in last_success_dates:
                                    if last_success_dates[child_pipeline_name] < level2_child.started_at:
                                        last_success_dates[child_pipeline_name] = level2_child.started_at
                                else:
                                    last_success_dates[child_pipeline_name] = level2_child.started_at

                    # keep compatibility with old CI behavior
                    else:
                        child_pipeline_name = normalize_older_pipeline_name(level1_child.name)
                        child_pipelines_reports.setdefault(child_pipeline_name, dict())
                        child_pipelines_reports[child_pipeline_name][pipeline.id] = _get_child_md(level1_child)

                        # Count successes and total for each child pipeline
                        total_counts[child_pipeline_name] = total_counts.get(child_pipeline_name, 0) + 1
                        if level1_child.status == "success":
                            success_counts[child_pipeline_name] = success_counts.get(child_pipeline_name, 0) + 1
                            if child_pipeline_name in last_success_dates:
                                if last_success_dates[child_pipeline_name] < level1_child.started_at:
                                    last_success_dates[child_pipeline_name] = level1_child.started_at
                            else:
                                last_success_dates[child_pipeline_name] = level1_child.started_at

            headers = ["name"]
            rows_as_dict = dict()
            for pipeline in newest_pipelines:
                time_status = f"[{pipeline.created_at[:16]} {get_status_icon(pipeline)}]({pipeline.web_url})"
                headers.append(time_status)
                # add empty cell in table if any child pipeline type doesn't exist at a given date
                for child_pipeline_name in child_pipelines_reports.keys():
                    if pipeline.id not in child_pipelines_reports[child_pipeline_name]:
                        child_pipelines_reports[child_pipeline_name][pipeline.id] = ""

                    rows_as_dict.setdefault(child_pipeline_name,
                                            [child_pipeline_name.replace("-deploy", "").replace("-", "‑")])
                    rows_as_dict[child_pipeline_name].append(
                        child_pipelines_reports[child_pipeline_name][pipeline.id])

            # Calculate success rates
            # and insert it in 2nd position
            headers.insert(1, "success rate")
            today = datetime.datetime.now()
            fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
            for child_name in rows_as_dict.keys():
                total = total_counts.get(child_name, 0)
                success = success_counts.get(child_name, 0)
                if success > 0:
                    last_success_date = last_success_dates.get(child_name, 0)
                    days_since_event = (today - datetime.datetime.strptime(last_success_date, fmt)).days
                    if days_since_event == 0:
                        last_success_message = "Last pipeline Ok :heavy_check_mark:"
                    else:
                        last_success_message = f"Last success {days_since_event} day{'s'[:days_since_event > 1]} ago"
                else:
                    last_success_message = f"No success in past {total} days"
                success_rate = f"success: {success}/{total} pipelines"
                rows_as_dict[child_name].insert(1, f"{success_rate},<br>{last_success_message}")

            report_rows = list(rows_as_dict.values())
            print_report(tabulate(report_rows, headers=headers, tablefmt="pipe"))
            print_report(" ")


def publish_report():

    with open(REPORT_FILE, "r") as f:
        report_content = f.read()

    if PIPELINE_HISTORY_COUNT > 1:
        # if script is run for aggregate several days, publish on "WIKI_REPORT_PAGE"
        wiki_page = WIKI_REPORT_PAGE
    else:
        # if script is run for an single day, publish on "WIKI_REPORT_PAGE/date"
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        wiki_page = f"{WIKI_REPORT_PAGE}/{date}"

    try:
        main_report = project.wikis.get(wiki_page)
    except gitlab.exceptions.GitlabGetError:
        main_report = project.wikis.create(
            {
                "title": f"{wiki_page}",
                "content": report_content,
            }
        )
    else:
        main_report.content = report_content
        main_report.save()

    print("The report can be found on following URL: " +
          os.getenv("CI_PROJECT_URL", default="https://gitlab.com/sylva-projects/sylva-core") + f"/-/wikis/{wiki_page}")
    print("Report uploaded for " + datetime.datetime.now().strftime("%Y-%m-%d"))


def delete_old_reports():
    print("Delete reports older than 7 days")
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    time_now = datetime.datetime.strptime(date, "%Y-%m-%d")
    for page in project.wikis.list():
        if f"{WIKI_REPORT_PAGE}/" not in page.slug:
            continue
        report_date = datetime.datetime.strptime(page.slug.split("/")[1], "%Y-%m-%d")
        delta = time_now - report_date
        if delta.days > 7:
            print(f"Deleting page {page.slug}")
            project.wikis.delete(page.slug)


if __name__ == '__main__':
    PIPELINE_HISTORY_COUNT = int(sys.argv[1])
    print(f"PIPELINE_HISTORY_COUNT={PIPELINE_HISTORY_COUNT}")

    gitlab_url = "https://" + os.getenv("CI_SERVER_HOST", default="gitlab.com")
    gl = gitlab.Gitlab(gitlab_url, private_token=os.getenv("PRIVATE_TOKEN"))
    project_id = os.getenv("CI_PROJECT_ID", default="42451983")
    pipeline_schedule_name = os.getenv("PIPELINE_SCHEDULE_NAME_SELECTOR", default="Nightly")
    project = gl.projects.get(project_id)
    print("retrieving pipeline schedules")
    try:
        pipeline_schedules = project.pipelineschedules.list()
    except (gitlab.exceptions.GitlabHttpError, gitlab.exceptions.GitlabListError) as e:
        print(f"error on pipelineschedules.list {e}\n  {e.response_body}")
        raise

    print("  done")

    WIKI_REPORT_PAGE = os.getenv("WIKI_REPORT_PAGE", "Scheduled-pipelines-report")

    create_report()
    publish_report()

    if PIPELINE_HISTORY_COUNT == 1:
        delete_old_reports()
