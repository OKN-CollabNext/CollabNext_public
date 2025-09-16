#!/usr/bin/env python3
import sys, argparse, re

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--table", required=True)
    p.add_argument("--include-col", action="append", default=[])
    p.add_argument("--ids-file", action="append", default=[])
    p.add_argument("--emit-id", action="append", default=[])
    return p.parse_args()

def main():
    args = parse_args()
    keep_ids = set()
    for f in args.ids_file:
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                keep_ids.add(line.strip())

    emit_map = {}
    for spec in args.emit_id:
        col, out = spec.split("=", 1)
        emit_map[col] = out
    emit_sets = {col: set() for col in emit_map}

    copy_re = re.compile(r"^COPY\s+([^\s(]+)\s*\(([^)]+)\)\s+FROM\s+stdin;?$", re.IGNORECASE)
    in_copy = False
    target = args.table
    colnames = []
    idx_map = {}
    copy_for_target = False

    # read/write raw lines to preserve COPY format
    for raw in sys.stdin:
        line = raw.rstrip("\n")
        if not in_copy:
            m = copy_re.match(line)
            if m:
                tbl = m.group(1)
                cols = [c.strip() for c in m.group(2).split(",")]
                in_copy = True
                copy_for_target = (tbl == target)
                colnames = cols
                idx_map = {c:i for i,c in enumerate(colnames)}
                sys.stdout.write(raw)
            else:
                sys.stdout.write(raw)
            continue

        if line == r"\.":
            in_copy = False
            copy_for_target = False
            colnames = []
            idx_map = {}
            sys.stdout.write(raw)
            continue

        if not copy_for_target:
            sys.stdout.write(raw)
            continue

        fields = line.split("\t")
        keep = True
        if args.include_col:
            keep = False
            for col in args.include_col:
                ix = idx_map.get(col)
                if ix is not None and fields[ix] in keep_ids:
                    keep = True
                    break
        global progress_counter
        try:
            progress_counter += 1
        except NameError:
            progress_counter = 1
        if progress_counter % 1000000 == 0:
            print(f"[filter] passed {progress_counter:,} rows for {args.table}", file=sys.stderr, flush=True)
        if keep:
            for col, out in emit_map.items():
                ix = idx_map.get(col)
                if ix is not None:
                    v = fields[ix]
                    if v != r"\N":
                        emit_sets[col].add(v)
            
            sys.stdout.write(raw)

    for col, out in emit_map.items():
        with open(out, "w", encoding="utf-8") as fh:
            for v in sorted(emit_sets[col]):
                fh.write(f"{v}\n")

if __name__ == "__main__":
    main()
