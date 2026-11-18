"""Check the merge revision for the isolated GitHub pull request control."""

import json
import os
from pathlib import Path
import subprocess
import sys


REPOSITORY = "Zi-Yi-Ming/semantic-router"
BRANCH_PAIRS = {
    ("lab-target/pr-event-green", "lab/pr-event-green"),
}


def qualify():
    if os.environ["GITHUB_EVENT_NAME"] != "pull_request":
        raise ValueError("The control requires a pull_request event")

    pull = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))[
        "pull_request"
    ]
    base, head = pull["base"], pull["head"]
    if any(
        repository != REPOSITORY
        for repository in (
            os.environ["GITHUB_REPOSITORY"],
            base["repo"]["full_name"],
            head["repo"]["full_name"],
        )
    ):
        raise ValueError("Both branches must belong to the lab repository")
    if (base["ref"], head["ref"]) not in BRANCH_PAIRS:
        raise ValueError("The pull request does not match a control branch pair")

    revision, *parents = subprocess.check_output(
        ["git", "log", "-1", "--format=%H %P"], text=True
    ).split()
    if revision != os.environ["GITHUB_SHA"] or parents != [base["sha"], head["sha"]]:
        raise ValueError("Checkout and merge parents must match the pull_request event")

    fixture = Path("qualification.txt")
    if not fixture.is_file() or fixture.read_bytes() != b"ready\n":
        raise ValueError("The qualification fixture is missing or does not contain ready")
    print(f"Qualified merge revision {revision} for base {base['sha']} and head {head['sha']}")


if __name__ == "__main__":
    try:
        qualify()
    except (KeyError, TypeError, ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
