import sys
import pandas as pd
import pysam

vcf = pysam.VariantFile(sys.argv[1])
outfile = sys.argv[2]

records = []
for rec in vcf:
    if rec.id is None or rec.samples is None:
        continue
    gt = rec.samples[0].get('GT')
    if gt and len(gt) == 2:
        alleles = ''.join([rec.alleles[i] if i is not None else '0' for i in gt])
        records.append([rec.id, rec.chrom, rec.pos, alleles])

pd.DataFrame(records, columns=["rsid", "chromosome", "position", "genotype"]).to_csv(outfile, sep="\t", index=False)
