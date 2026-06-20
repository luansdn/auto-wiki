#!/usr/bin/env python3
"""Fetch metadata for repos from EbookFoundation/free-programming-books."""
import json, requests, time, sys
from pathlib import Path

TOKEN = open('/root/.config/gh/hosts.yml').read().split('oauth_token: ')[1].split('\n')[0].strip()
HEADERS = {'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
OUTPUT = []

batch_file = sys.argv[1]
batch_idx = sys.argv[2]

with open(batch_file) as f:
    repos = json.load(f)

total = len(repos)
for i, repo_name in enumerate(repos):
    try:
        url = f'https://api.github.com/repos/{repo_name}'
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            d = r.json()
            OUTPUT.append({
                'full_name': d['full_name'],
                'description': d.get('description') or '',
                'html_url': d['html_url'],
                'stargazers_count': d.get('stargazers_count', 0),
                'language': d.get('language') or '',
                'topics': d.get('topics', []),
                'license': d['license']['spdx_id'] if d.get('license') else '',
                'source': ['free-programming-books-list']
            })
        elif r.status_code == 404:
            pass  # Dead link
        elif r.status_code == 403:
            print(f'Rate limited! Sleeping 60s...')
            time.sleep(60)
            continue  # Retry
        if (i+1) % 10 == 0:
            print(f'[{batch_idx}] {i+1}/{total} - {len(OUTPUT)} valid')
        time.sleep(0.3)
    except Exception as e:
        print(f'[{batch_idx}] Error {repo_name}: {e}')
        time.sleep(1)

output_path = f'/tmp/fpb_results_{batch_idx}.json'
with open(output_path, 'w') as f:
    json.dump(OUTPUT, f, ensure_ascii=False)
print(f'[{batch_idx}] Done. Valid repos: {len(OUTPUT)} -> {output_path}')
