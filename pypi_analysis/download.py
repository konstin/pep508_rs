"""
To run this:
 * `pip install google-cloud-bigquery`
 * Download https://cloud.google.com/sdk/docs/install
 * Unpack, skip installation
 * Create a free google cloud acount
 * `google-cloud-sdk/bin/gcloud auth application-default login`
 * Check `$HOME/.config/gcloud/application_default_credentials.json` is there
 * Run. Takes a while (15min - 1h)
"""

import json
from pathlib import Path

from google.cloud import bigquery
from tqdm import tqdm


def main():
    # noinspection PyTypeChecker
    client = bigquery.Client(project="jupyter-local-project")
    table_id = "the-psf.pypi.distribution_metadata"
    table = client.get_table(table_id)

    selected_fields = [
        field
        for field in table.schema
        if field.name in ["name", "version", "filename", "requires_dist"]
    ]
    with Path("pipy_requires_dist.ndjson").open("w") as fp:
        rows_iter = client.list_rows(table_id, selected_fields=selected_fields)
        for row in tqdm(rows_iter, total=table.num_rows):
            fp.write(json.dumps(dict(row)))
            fp.write("\n")


if __name__ == "__main__":
    main()
