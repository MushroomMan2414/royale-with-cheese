# Mornye: how the pieces fit together

This repository documents the relationship between the local **Mornye-Python**
host and the **Mornye-Extension** provider store, and includes a small example
that runs against those neighboring checkouts.

- [Architecture and extension lifecycle](docs/architecture.md)
- [Local setup and walkthrough](docs/local-setup.md)
- [Isolated Docker example](docs/docker-setup.md)
- [Example scripts](examples/)

To build and start the Docker example, run `make up`, then open
<http://127.0.0.1:18080>. Use `make down` to stop it.
Downloads appear in the local `downloads/` directory.
To download a CSV of track and album links, run `make csv CSV="/path/to/list.csv"`.
See the [CSV guide](docs/csv.md) for the format and results.

The guide describes the checked-out code at Mornye-Python `dcff676` and
Mornye-Extension `12530ce`. Provider services, package versions, and APIs may
change; re-check the relevant source when upgrading.
