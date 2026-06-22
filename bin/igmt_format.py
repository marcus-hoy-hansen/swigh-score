#!/usr/bin/env python3
import argparse
from pathlib import Path


def parse_fasta(path):
    header = None
    seq_lines = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    yield header, "".join(seq_lines)
                header = line[1:]
                seq_lines = []
            else:
                seq_lines.append(line)
        if header is not None:
            yield header, "".join(seq_lines)


def extract_gene_info(header):
    fields = header.split("|")
    if len(fields) < 5:
        return None, None, None
    gene_name = fields[1].strip()
    species = fields[2].strip()
    region = fields[4].strip()
    return gene_name, species, region


def main():
    parser = argparse.ArgumentParser(
        description="Format IMGT FASTA into V/J name and sequence files."
    )
    parser.add_argument(
        "input_fasta",
        type=Path,
        help="Path to IMGTGENEDB-ReferenceSequences FASTA file.",
    )
    parser.add_argument(
        "--species",
        default="Homo sapiens",
        help="Species filter (default: Homo sapiens).",
    )
    parser.add_argument(
        "--out-prefix",
        default="igmt",
        help="Output prefix (default: igmt).",
    )
    parser.add_argument(
        "--include-or",
        action="store_true",
        help="Include gene names containing /OR (default: off).",
    )
    parser.add_argument(
        "--d-target",
        choices=["d", "v", "j", "skip"],
        default="d",
        help="Where to route D genes (default: d).",
    )
    args = parser.parse_args()

    v_prefixes = ("IGHV", "IGKV", "IGLV")
    j_prefixes = ("IGHJ", "IGKJ", "IGLJ")
    d_prefixes = ("IGHD",)

    data = {
        "igh": {"v": [], "v_seq": [], "j": [], "j_seq": [], "d": [], "d_seq": []},
        "igk": {"v": [], "v_seq": [], "j": [], "j_seq": []},
        "igl": {"v": [], "v_seq": [], "j": [], "j_seq": []},
    }

    for header, seq in parse_fasta(args.input_fasta):
        gene_name, species, region = extract_gene_info(header)
        if not gene_name or species != args.species:
            continue
        if region not in ("V-REGION", "D-REGION", "J-REGION"):
            continue
        if not args.include_or and "/OR" in gene_name:
            continue
        seq = seq.upper()
        if gene_name.startswith(v_prefixes):
            if gene_name.startswith("IGH"):
                locus = "igh"
            elif gene_name.startswith("IGK"):
                locus = "igk"
            else:
                locus = "igl"
            data[locus]["v"].append(gene_name)
            data[locus]["v_seq"].append(seq)
        elif gene_name.startswith(j_prefixes):
            if gene_name.startswith("IGH"):
                locus = "igh"
            elif gene_name.startswith("IGK"):
                locus = "igk"
            else:
                locus = "igl"
            data[locus]["j"].append(gene_name)
            data[locus]["j_seq"].append(seq)
        elif gene_name.startswith(d_prefixes):
            if args.d_target == "d":
                data["igh"]["d"].append(gene_name)
                data["igh"]["d_seq"].append(seq)
            elif args.d_target == "v":
                data["igh"]["v"].append(gene_name)
                data["igh"]["v_seq"].append(seq)
            elif args.d_target == "j":
                data["igh"]["j"].append(gene_name)
                data["igh"]["j_seq"].append(seq)
            else:
                continue

    out_prefix = args.out_prefix
    for locus, locus_data in data.items():
        if "v" in locus_data:
            Path(f"{out_prefix}-{locus}-vgene-name.txt").write_text(
                "\n".join(locus_data["v"]) + ("\n" if locus_data["v"] else ""),
                encoding="utf-8",
            )
            Path(f"{out_prefix}-{locus}-vgene-sequence.txt").write_text(
                "\n".join(locus_data["v_seq"]) + ("\n" if locus_data["v_seq"] else ""),
                encoding="utf-8",
            )
        if "j" in locus_data:
            Path(f"{out_prefix}-{locus}-jgene-name.txt").write_text(
                "\n".join(locus_data["j"]) + ("\n" if locus_data["j"] else ""),
                encoding="utf-8",
            )
            Path(f"{out_prefix}-{locus}-jgene-sequence.txt").write_text(
                "\n".join(locus_data["j_seq"]) + ("\n" if locus_data["j_seq"] else ""),
                encoding="utf-8",
            )
        if "d" in locus_data:
            Path(f"{out_prefix}-{locus}-dgene-name.txt").write_text(
                "\n".join(locus_data["d"]) + ("\n" if locus_data["d"] else ""),
                encoding="utf-8",
            )
            Path(f"{out_prefix}-{locus}-dgene-sequence.txt").write_text(
                "\n".join(locus_data["d_seq"]) + ("\n" if locus_data["d_seq"] else ""),
                encoding="utf-8",
            )


if __name__ == "__main__":
    main()
