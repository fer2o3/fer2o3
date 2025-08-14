import os
import requests
from datetime import date
from dateutil.relativedelta import relativedelta
from lxml import etree


def uptime():
    birthday = date(2003, 9, 23)
    today = date.today()
    diff = relativedelta(today, birthday)
    return f"{diff.years} years, {diff.months} months, {diff.days} days"


def github_stats(username="fer2o3"):
    token = os.getenv("README_TOKEN")
    headers = {"Authorization": f"bearer {token}"}

    query = """
    query($username: String!) {
        user(login: $username) {
            repositories(first: 100, ownerAffiliations: OWNER) {
                totalCount
                nodes {
                    stargazerCount
                    languages(first: 10) {
                        edges {
                            size
                        }
                    }
                }
            }
            contributions2025: contributionsCollection(from: "2025-01-01T00:00:00Z", to: "2025-12-31T23:59:59Z") {
                totalCommitContributions
            }
            contributionsAll: contributionsCollection {
                totalCommitContributions
                totalIssueContributions
                totalPullRequestContributions
                totalPullRequestReviewContributions
            }
        }
    }
    """

    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"username": username}},
        headers=headers,
    )

    result = response.json()
    if "errors" in result:
        print(f"GraphQL errors: {result['errors']}")
        return None

    data = response.json()["data"]["user"]

    repos = data["repositories"]["totalCount"]
    stars = sum(repo["stargazerCount"] for repo in data["repositories"]["nodes"])
    commits = data["contributions2025"]["totalCommitContributions"]

    contributions = (
        data["contributionsAll"]["totalCommitContributions"]
        + data["contributionsAll"]["totalIssueContributions"]
        + data["contributionsAll"]["totalPullRequestContributions"]
        + data["contributionsAll"]["totalPullRequestReviewContributions"]
    )

    lines = sum(
        sum(edge["size"] for edge in repo["languages"]["edges"])
        for repo in data["repositories"]["nodes"]
    )

    return {
        "repos": repos,
        "stars": stars,
        "commits": commits,
        "contributions": contributions,
        "lines": lines,
    }


def update_dots(root, total_width=47):
    ns = {"svg": "http://www.w3.org/2000/svg"}
    for tspan in root.findall(".//svg:tspan", ns):
        if tspan.get("id") == "dots":
            prev_tspan = tspan.getprevious()
            next_tspan = tspan.getnext()
            prev_text = prev_tspan.text if prev_tspan is not None else ""
            next_text = next_tspan.text if next_tspan is not None else ""
            used_width = len(prev_text) + len(next_text) + 2
            dots_needed = max(1, total_width - used_width)
            tspan.text = " " + "." * dots_needed + " "


def update_lines(root, username="fer2o3", total_width=47):
    token = os.getenv("README_TOKEN")
    headers = {"Authorization": f"token {token}"}

    query = """
    query($username: String!) {
        user(login: $username) {
            repositories(first: 50, ownerAffiliations: OWNER) {
                nodes {
                    name
                    owner {
                        login
                    }
                }
            }
        }
    }
    """

    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"username": username}},
        headers=headers,
    )

    if response.status_code != 200:
        return

    repos = response.json()["data"]["user"]["repositories"]["nodes"]
    lines_added = 0
    lines_removed = 0

    for repo in repos:
        repo_query = """
        query($name: String!, $owner: String!) {
            repository(name: $name, owner: $owner) {
                defaultBranchRef {
                    target {
                        ... on Commit {
                            history(first: 100) {
                                edges {
                                    node {
                                        author {
                                            user {
                                                login
                                            }
                                        }
                                        additions
                                        deletions
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        repo_response = requests.post(
            "https://api.github.com/graphql",
            json={
                "query": repo_query,
                "variables": {"name": repo["name"], "owner": repo["owner"]["login"]},
            },
            headers=headers,
        )

        if repo_response.status_code == 200:
            data = repo_response.json()
            if data["data"]["repository"]["defaultBranchRef"]:
                commits = data["data"]["repository"]["defaultBranchRef"]["target"][
                    "history"
                ]["edges"]
                for commit in commits:
                    if (
                        commit["node"]["author"]["user"]
                        and commit["node"]["author"]["user"]["login"] == username
                    ):
                        lines_added += commit["node"]["additions"]
                        lines_removed += commit["node"]["deletions"]

    add_text = f"{lines_added} ++"
    rem_text = f" {lines_removed} --"

    update_svg_element(root, "add", add_text)
    update_svg_element(root, "rem", rem_text)

    add = root.find(".//*[@id='add']")
    rem = root.find(".//*[@id='rem']")
    dots = add.getprevious()

    add_length = len(add.text) if add is not None else 0
    rem_length = len(rem.text) if rem is not None else 0
    used_width = len(" lines of code") + add_length + rem_length + 2
    dots_needed = max(1, total_width - used_width)
    dots.text = " " + "." * dots_needed + " "


def update_svg_element(root, id, value):
    element = root.find(f".//*[@id='{id}']")
    if element is not None:
        element.text = str(value)


def update_svg_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()
    root = etree.fromstring(content)

    current_uptime = uptime()
    stats = github_stats()

    if not stats:
        print("Fuck.")
        return

    update_svg_element(root, "uptime", current_uptime)
    update_svg_element(root, "repos", stats["repos"])
    update_svg_element(root, "stars", stats["stars"])
    update_svg_element(root, "commits", stats["commits"])
    update_svg_element(root, "contributions", stats["contributions"])
    update_dots(root)
    update_lines(root)

    with open(filepath, "w") as f:
        f.write(etree.tostring(root, encoding="unicode", pretty_print=True))


if __name__ == "__main__":
    update_svg_file("dark.svg")
    update_svg_file("light.svg")
