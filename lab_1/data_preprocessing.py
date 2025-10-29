from pathlib import Path
import re
import pandas as pd

in_path = Path(r"c:\sensores-y-actuadores\lab_1\data.txt")
out_path = Path(r"c:\sensores-y-actuadores\lab_1\data.csv")

# Robust pattern: tolerate typos (e.g., "stra 28/30") and varying whitespace
pattern = re.compile(
    r'(?<!\d)(\d+)\s*/\s*(\d+).*?Valor\s*ADC:\s*(\d+)\s*\|\s*Voltaje:\s*([0-9]+(?:[.,][0-9]+)?)\s*V',
    re.IGNORECASE
)

rows = []
stage_id = -1  # will become 0 on first "sample 1/.."

for line in in_path.read_text(encoding="utf-8", errors="ignore").splitlines():
    m = pattern.search(line)
    if not m:
        continue
    sample_no, total_in_stage, adc, volt_str = m.groups()
    sample_no = int(sample_no)
    total_in_stage = int(total_in_stage)
    adc = int(adc)
    volt = float(volt_str.replace(",", "."))

    # Start new stage when sample counter resets to 1
    if sample_no == 1:
        stage_id += 1

    rows.append(
        {
            "stage_id": stage_id,
            "sample_no": sample_no,
            "adc": adc,
            "voltaje_v": volt,
        }
    )

df = pd.DataFrame(rows)

# Assign level per stage: 0..8 ascending, then 7..0 descending (no repeated 8)
expected_levels = list(range(0, 9)) + list(range(7, -1, -1))  # length 17
num_stages = df["stage_id"].max() + 1 if not df.empty else 0

if num_stages == 0:
    raise SystemExit("No samples found. Check the input file format and path.")

if num_stages != len(expected_levels):
    print(f"Warning: detected {num_stages} stages, expected {len(expected_levels)} (0..8..0).")
    # Map as far as possible
    levels = expected_levels[:num_stages]
else:
    levels = expected_levels

level_map = {sid: levels[sid] for sid in range(num_stages)}
df["level_cm"] = df["stage_id"].map(level_map)

# Optional sanity check: each stage should have 30 samples
counts = df.groupby("stage_id")["sample_no"].nunique()
bad = counts[counts != 30]
if not bad.empty:
    print("Warning: some stages do not have 30 unique samples:")
    print(bad.to_string())

# Order and write
df = df.sort_values(["stage_id", "sample_no"])[
    ["stage_id", "level_cm", "sample_no", "adc", "voltaje_v"]
]
df.to_csv(out_path, index=False)
print(f"Wrote {len(df)} rows across {num_stages} stages to {out_path}")