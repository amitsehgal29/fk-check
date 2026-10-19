# fk-check

A referential-integrity check between two CSV files. It finds child rows whose foreign key has no match in the parent file (orphans). It uses only the Python standard library and exits with code 1 when there are too many orphans, so it can block a load.

```bash
python3 fk_check.py samples/customers.csv samples/orders.csv --parent-key customer_id
python3 fk_check.py samples/customers.csv samples/orders.csv --parent-key customer_id --ignore-case --max-orphans 5
python3 fk_check.py dim.csv fact.csv --parent-key id,country --child-key cust_id,cust_country --show-unused
```

```json
{"parent_keys": 4, "child_rows": 6, "null_fk_rows": 1, "orphan_rows": 2,
 "orphan_keys": [{"key": ["c009"], "rows": 2}], "status": "fail"}
```

## Behaviour

- Composite keys are comma-separated column lists. The parent and child lists are matched by position.
- Whitespace is trimmed. `--ignore-case` matches keys case-insensitively.
- An empty foreign key is counted as `null_fk_rows`, not as an orphan.
- `--show-unused` also lists parent keys that no child row uses.
- It exits 0 on a pass, 1 when orphan rows are above `--max-orphans`, and 2 for a bad column or bad arguments.

## Tests

```bash
python3 -m unittest
```
