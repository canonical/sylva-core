#!/usr/bin/env python3
#
# This script outputs a human readable RKE2 CIS benchmark from a JSON file report dumped by the command
# kubectl get $(kubectl get clusterscanreports -o name) -o jsonpath="{.spec.reportJSON}"
# Usage: kubectl get < clusterscanreports name > -o jsonpath="{.spec.reportJSON} | ./tools/display-scan-report.py
# ref: https://pypi.org/project/tabulate/
import sys
import json
from tabulate import tabulate

data = json.load(sys.stdin)

head = ["ID", "Area", "Description", "State", "Type"]

dataresult = []

for RES in data["results"]:
    for CHECKS in RES["checks"]:
        dataresult.append([CHECKS["id"], RES["description"], CHECKS["description"],
                           CHECKS["state"], CHECKS["test_type"]])

print(tabulate(dataresult, headers=head, tablefmt="mixed_grid"))

print("\nSummary\n")

headsummary = ["Total", "Pass", "Fail", "Skip", "n/a"]

summary = [
    [str(data["total"]), str(data["pass"]), str(data["fail"]), str(data["skip"]), str(data["notApplicable"])]
]

print(tabulate(summary, headers=headsummary, tablefmt="fancy_grid"))
