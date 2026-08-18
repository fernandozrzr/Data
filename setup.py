# setup.py  —  interview data loader
# Keep this file private-ish: candidates should not read it.
# The notebook fetches and runs this; it builds the tables and defines run().
import duckdb
import pandas as pd

BASE = "https://raw.githubusercontent.com/fernandozrzr/Data/main"

con = duckdb.connect()

# students / dogs / cats: plain CSVs (pandas reads the URL directly)
for _name in ["students", "dogs", "cats"]:
    _df = pd.read_csv(f"{BASE}/{_name}.csv")
    con.register(f"_{_name}_src", _df)
    con.execute(f"CREATE TABLE {_name} AS SELECT * FROM _{_name}_src")

# cdr: keep timestamp as text on load, then coerce to a real TIMESTAMP
# (handles both clean ISO and Excel's day/month/year formatting)
_cdr = pd.read_csv(f"{BASE}/cdr.csv", dtype={"call_start_time": str})
con.register("_cdr_src", _cdr)
con.execute("""
CREATE TABLE cdr AS
SELECT id, customer_id,
       COALESCE(
         try_cast(call_start_time AS TIMESTAMP),
         try_strptime(call_start_time, '%-d/%-m/%Y %-H:%M')
       ) AS call_start_time,
       call_duration_in_secs, call_charge_in_sgd
FROM _cdr_src
""")


def run(sql):
    """Run a SQL query and return the result as a DataFrame."""
    return con.execute(sql).df()


print("Tables ready:", [r[0] for r in con.execute("SHOW TABLES").fetchall() if not r[0].startswith("_")])
print("Row counts:", {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                      for t in ["students", "dogs", "cats", "cdr"]})
