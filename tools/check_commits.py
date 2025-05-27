"""
Script to check that a tagged commit in Sylva-core does include all commits in its dependencies in sylva-elements.
"""

import gitlab
import os

# Your GitLab URL and access token
GITLAB_URL = 'https://gitlab.com'
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

# Initialize GitLab connection
gl = gitlab.Gitlab(GITLAB_URL, private_token=ACCESS_TOKEN)

# List of groups or repositories to check
GROUPS = ['sylva-projects/sylva-elements']  # GitLab group names
REPOSITORIES = []  # Specific repositories
EXCLUDED_REPOSITORIES = ['sylva-projects/sylva-elements/renovate-config',
                         'sylva-projects/sylva-elements/renovate',
                         'sylva-projects/sylva-elements/gitlab-config',
                         'sylva-projects/sylva-elements/kiwi-imagebuilder',
                         'sylva-projects/sylva-elements/helm-charts/metal3'
                         ]  # Repositories to exclude
BRANCH_PATTERN = ['main']  # Branch patterns to check


def get_all_projects_in_group(group_id):
    """Recursively fetch all projects in a group and its subgroups."""
    projects = []
    group = gl.groups.get(group_id)
    group_projects = group.projects.list(all=True)

    for project in group_projects:
        projects.append(gl.projects.get(project.id))

    subgroups = group.subgroups.list(all=True)
    for subgroup in subgroups:
        projects.extend(get_all_projects_in_group(subgroup.id))

    return projects


def get_repos_from_groups(groups):
    """Fetch all repositories from the specified groups, including subgroups."""
    repos = []
    for group_name in groups:
        group = gl.groups.get(group_name)
        repos.extend(get_all_projects_in_group(group.id))
    return repos


def get_uncovered_commits(repo, branch_name):
    """
    Get commits on a branch that are more recent than the latest tag.
    Fetches commits page by page for efficiency.
    """
    try:
        tags = repo.tags.list(all=True)
        tag_commit_shas = {tag.commit['id']: tag.name for tag in tags}
        uncovered_commits = []
        latest_tag_name = None

        page = 1
        per_page = 50  # Adjust as needed (max 100)
        found_tag = False

        while True:
            batch = repo.commits.list(ref_name=branch_name, per_page=per_page, page=page)
            if not batch:
                break

            for commit in batch:
                if commit.id in tag_commit_shas:
                    latest_tag_name = tag_commit_shas[commit.id]
                    found_tag = True
                    break
                uncovered_commits.append(commit)

            if found_tag:
                break
            page += 1

        if uncovered_commits:
            if latest_tag_name:
                return uncovered_commits, latest_tag_name
            else:
                # No tag found on the branch, return all collected commits
                return uncovered_commits, None
        else:
            # All commits are covered by tags
            return [], None

    except gitlab.exceptions.GitlabListError:
        return [], None  # No commits on the branch


def check_repos_for_uncovered_commits(groups, repositories, excluded_repositories, branch_pattern):
    """
    Check each repository for branches with commits not covered by tags.
    Returns True if all commits are covered by tags in all repos, False otherwise.
    Prints the list of uncovered commits if any are found.
    """
    all_covered = True
    repos = get_repos_from_groups(groups)
    repos.extend([gl.projects.get(repo_name) for repo_name in repositories])

    for repo in repos:
        if repo.path_with_namespace in excluded_repositories:
            print(f"* Skipping excluded repository: {repo.path_with_namespace}")
            continue

        for branch_name in branch_pattern:
            try:
                uncovered_commits, latest_tag_name = get_uncovered_commits(repo, branch_name)
                if uncovered_commits:
                    all_covered = False
                    if latest_tag_name:
                        print(f"## Repository: {repo.path_with_namespace}")
                        print(f"### Branch: {branch_name}")
                        print(f"These commits on **{branch_name}** are not covered by the latest tag **{latest_tag_name}**:")
                    else:
                        print(f"## Repository: {repo.path_with_namespace}")
                        print(f"### Branch: {branch_name}")
                        print("These commits are **not** covered by any tag:")

                    for commit in uncovered_commits:
                        print(f"- {commit.id}: {commit.title}")
                else:
                    print(f"## Repository: {repo.path_with_namespace}")
                    print(f"### Branch: {branch_name}")
                    print("**All** commits are covered by tags.")
            except gitlab.exceptions.GitlabGetError:
                print(f"## Branch {branch_name} not found in repository {repo.path_with_namespace}")
            except gitlab.exceptions.GitlabListError:
                print(f"## No commits found for branch {branch_name} in repository {repo.path_with_namespace}")

    return all_covered


if __name__ == "__main__":
    check_repos_for_uncovered_commits(GROUPS, REPOSITORIES, EXCLUDED_REPOSITORIES, BRANCH_PATTERN)
