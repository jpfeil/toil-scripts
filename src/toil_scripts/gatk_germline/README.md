## University of California, Santa Cruz Genomics Institute
### Guide: Running GATK Best Practices Variant Pipeline using Toil

## Overview

The Toil germline pipeline accepts FASTQ or BAM files as input and runs
the [GATK best practices pipeline](https://software.broadinstitute.org/gatk/best-practices/).
for SNP and INDEL discovery. This pipeline can be configured to run 
BWA alignment, GATK preprocessing, variant calling, and filtering. 
The pipeline also supports functional variant annotation using Oncotator. 
Samples can be analyzed individually or merged for joint genotyping and 
filtering. False positives are removed using GATK recommended "hard 
filters" or through variant quality score recalibration and filtering.

#### General Dependencies

    1. Python 2.7
    2. Curl         apt-get install curl
    3. Docker       http://docs.docker.com/engine/installation/

#### Python Dependencies

    1. pip          apt-get install python-pip
    2. virtualenv   pip install virtualenv
    3. Toil         pip install toil

#### Installation

Toil-scripts is now pip installable! `pip install toil-scripts` for a toil-stable version 
or `pip install --pre toil-scripts` for cutting edge development version.

Type: `toil-germline` to get basic help menu and instructions

To decrease the chance of versioning conflicts, install toil-scripts into a virtualenv: 

- `virtualenv ~/toil-scripts` 
- `source ~/toil-scripts/bin/activate`
- `pip install toil`
- `pip install toil-scripts`

If Toil is already installed globally (true for CGCloud users), or there are global dependencies (like Mesos),
use virtualenv's `--system-site-packages` flag.

## General Usage

    1. Type `toil-germline generate` to create an editable manifest and config in the current working directory.
    2. Parameterize the pipeline by editing the config.
    3. Fill in the manifest with information pertaining to your samples.
    4. Type `toil-germline run [jobStore] --config [config] --manifest [manifest]` to execute the pipeline.
    
## Example Commands
Run sample(s) locally using the manifest
    1. `toil-germline generate`
    2. Fill in config and manifest
    3. `toil-germline run --config config-toil-germline.yaml \
        --manifest manifest-toil-germline.tsv ./example-jobstore`

Toil options can be appended to `toil-germline run`, for example:
`toil-germline run ./example-jobstore --retryCount=1 --workDir=/data`

For a complete list of Toil options, just type `toil-germline run -h`

Run a single sample locally
    1. `toil-germline generate-config`
    2. Fill in config
    3. `toil-germline run ./example-jobstore --workDir /data --samples \
        UUID https://sample-depot.com/sample.bam`
        
## Acceptable Inputs
The Toil germline pipeline accepts FASTQ and BAM file formats. Sample
information should be placed in the Toil germline manifest file. 

    FASTQ Manifest Information:
    - unique identifier
    - URL or local path with .fq file extension
    - Paired FASTQ URL/PATH
    - Read group line
    
    BAM Manifest Information:
    - unique identifier
    - sample URL or local path with .bam file extension
    
GATK tools require several [read group](http://gatkforums.broadinstitute.org/wdl/discussion/6472/read-groups)
fields. For this reason, FASTQ manifest entries must include a valid 
GATK read group line. Input BAM files must already contain read group 
information.

Example manifest entry:
UUID    file:///path/to/sample.1.fq   file:///path/to/sample.2.fq   @RG\tID:foo\tSM:bar

## Pipeline outputs
Results are uploaded to the output directory defined in the config file. 
The output-dir can be an S3 URL or local path. Sample specific results 
are placed in a subdirectory named after the sample's unique identifier.

## Tools
| Tool         | Version | Description                      |
|--------------|---------|----------------------------------|
| Bwakit       | 0.7.12  | Maps sequencing reads            |
| SAMtools     | 0.1.19  | Manipulates SAM/BAM files        |
| Picard tools | 1.95    | Processes HTS data formats       |
| GATK         | 3.5     | Identifies genomic variants      |
| Oncotator    | 1.9     | Adds cancer relevant annotations |

## GATK Variant Annotations
Variant annotations are added during the variant discovery and 
genotyping steps. They help describe the context of the variant call 
and are used during filtering to identify which variants are likely 
false positives.

Recommended annotations:
- QualByDepth
- FischerStrand
- StrandOddsRatio
- ReadPosRankSumTest
- MappingQualityRankSumTest
- RMSMappingQuality
- InbreedingCoeff

## Joint Genotyping
[Joint genotyping](https://software.broadinstitute.org/gatk/guide/article?id=3893)
provides the benefits of joint calling without the exponential increase 
in run times. If the joint-genotype config parameter is set to True, 
then the pipeline will merge the genomic VCFs across the entire cohort. 
All downstream steps will use the merged GVCF file. The GATK 
documentation recommends between 30 and 200 samples per batch. Larger 
batches increase the disk and memory requirements for the run.

## VQSR
Variant Quality Score Recalibration is applied whenever the config
parameter run-vqsr is set to True. [VQSR](https://software.broadinstitute.org/gatk/guide/tooldocs/org_broadinstitute_gatk_tools_walkers_variantrecalibration_VariantRecalibrator.php)
is a filtering method that uses machine learning algorithms to remove 
false positive calls. For this reason, VQSR requires many samples to 
train on in order to create an accurate statistical model. We have 
followed [GATK recommendations](https://software.broadinstitute.org/gatk/guide/article?id=2805).
for training resources and variant annotations. 

### SNP Recalibration Parameters
```
java -jar GenomeAnalysisTK.jar \
-T VariantRecalibrator \
-R genome.fa \
-input input.vcf \
-tranche 100.0 \
-tranche 99.9 \
-tranche 99.0 \
-tranche 90.0 \
-an {snp-filter-annotations}
-resource:hapmap,known=false,training=true,truth=true,prior=15.0 hapmap.vcf \
-resource:omni,known=false,training=true,truth=true,prior=12.0 omni.vcf \
-resource:1000G,known=false,training=true,truth=false,prior=10.0 1000G.vcf \
-resource:dbsnp,known=true,training=false,truth=false,prior=2.0 dbsnp.vcf \
-mode SNP \
--maxGaussians 4 \
-recalFile output.recal \
-tranchesFile output.tranches \
-rscriptFile output.plots.R
```

### INDEL Recalibration Parameters
```
java -jar GenomeAnalysisTK.jar \
-T VariantRecalibrator \
-R genome.fa \
-an {indel-filter-annotations}
-tranche 100.0 \
-tranche 99.9 \
-tranche 99.0 \
-tranche 90.0 \
-resource:mills,known=false,training=true,truth=true,prior=12.0 mills.vcf \
-resource:dbsnp,known=true,training=false,truth=false,prior=2.0 dbsnp.vcf \
-mode INDEL \
--maxGaussians 4 \
-recalFile output.recal \
-tranchesFile output.tranches \
-rscriptFile output.plots.R
```

## Hard Filters
When not using VQSR, GATK recommended ["hard filters"](http://gatkforums.broadinstitute.org/wdl/discussion/2806/howto-apply-hard-filters-to-a-call-set)
are used instead. This method uses simple thresholds based on GATK 
variant annotation values to remove false variant calls. You can find an 
explanation of filter threshold values [here](https://software.broadinstitute.org/gatk/guide/article?id=6925).

Recommended SNP Filter:
    "QD < 2.0 || FS > 60.0 || MQ < 40.0 || MQRankSum < -12.5 || ReadPosRankSum < -8.0"
    
Recommended INDEL Filter:
    "QD < 2.0 || FS > 200.0 || ReadPosRankSum < -20.0"
    
## Config
```
##############################################################################################################
# GATK Germline Pipeline configuration file
# Variant databases can be obtained through the GATK resource bundle:
# https://software.broadinstitute.org/gatk/guide/article?id=1213
# http://gatkforums.broadinstitute.org/gatk/discussion/1259/what-vqsr-training-sets-arguments-should-i-use-for-my-specific-project
##############################################################################################################
# This configuration file is formatted in YAML. Simply write the value (at least one space) after the colon.
# Edit the values in this configuration file and then rerun the pipeline
# Comments (beginning with #) do not need to be removed. Optional parameters may be left blank.
##############################################################################################################
# Required: Number of cores per job
cores:

# Required: Java heap size (human readable bytes format i.e. 10G)
xmx:

# Required: Approximate input file size (human readable bytes format)
file-size:

# Required: S3 URL or local path to output directory
output-dir:

# Required: Input BAM file is sorted (Default: False)
sorted:

# Required: URL or local path to reference genome FASTA file
genome-fasta:

# Optional: URL or local path to reference genome index (Default: None)
genome-fai:

# Optional: URL or local path to reference genome sequence dictionary (Default: None)
genome-dict:

# Required for VQSR: URL or local path to 1000G SNP resource file (Default: None)
g1k_snp:

# Required for preprocessing: URL or local path to 1000G INDEL resource file (Default: None)
g1k_indel:

# Required for VQSR: URL or local path HapMap resource file (Default: None)
hapmap:

# Required for VQSR: URL or local path Omni resource file (Default: None)
omni:

# Required for VQSR: URL or local path to Mills resource file (Default: None)
mills:

# Required for VQSR: URL or local path to dbSNP resource file (Default: None)
dbsnp:

# Required for FASTQ samples: Align FASTQs or Realign BAM file (Default: False)
run-bwa:

# Optional. Trim adapters (Default: False)
trim:

# Required for BWA alignment: URL or local path to BWA index file prefix.amb (Default: None)
amb:

# Required for BWA alignment: URL or local path to BWA index file prefix.ann (Default: None)
ann:

# Required for BWA alignment: URL or local path to BWA index file prefix.bwt (Default: None)
bwt:

# Required for BWA alignment: URL or local path to BWA index file prefix.pac (Default: None)
pac:

# Required for BWA alignment: URL or local path to BWA index file prefix.sa (Default: None)
sa:

# Required for ALT-aware alignment: URL or local path to alternate contigs (Default: None)
alt:

# Optional: Run GATK Preprocessing (Default: False)
preprocess:

# Optional: Stops after GATK Preprocessing (Default: False)
preprocess-only:

# Required for hard filtering: Name of SNP filter for VCF header
snp_filter_name:

# Required for hard filtering: SNP JEXL filter expression
snp_filter_expression:

# Required for hard filtering: Name of INDEL filter for VCF header
indel_filter_name:

# Required for hard filtering: INDEL JEXL filter expression
indel_filter_expression:

# Optional: Run GATK VQSR (Default: False)
run-vqsr:

# Optional: Merges all samples into a single GVCF for genotyping and filtering (Default: False)
joint-genotype:

# Optional: Run Oncotator (Default: False)
run-oncotator:

# Required for Oncotator: URL or local path to Oncotator database (Default: None)
oncotator-db:

# Optional: Suffix added to output filename (i.e. .toil)
suffix:

# Optional: Path to key file for SSE-C Encryption (Default: None)
ssec:

# Optional: Allow seq dict incompatibility (Default: False)
unsafe-mode:
```
    

## Example Config
```
genome-fasta: s3://cgl-pipeline-inputs/hg19/ucsc.hg19.fasta
genome-fai: s3://cgl-pipeline-inputs/hg19/ucsc.hg19.fasta.fai
genome-dict: s3://cgl-pipeline-inputs/hg19/ucsc.hg19.dict
g1k_indel: s3://cgl-pipeline-inputs/hg19/1000G_phase1.indels.hg19.sites.vcf
g1k_snp: s3://cgl-pipeline-inputs/hg19/1000G_phase1.snps.high_confidence.hg19.sites.vcf
mills: s3://cgl-pipeline-inputs/hg19/Mills_and_1000G_gold_standard.indels.hg19.sites.vcf
dbsnp: s3://cgl-pipeline-inputs/hg19/dbsnp_138.hg19.excluding_sites_after_129.vcf
hapmap: s3://cgl-pipeline-inputs/hg19/hapmap_3.3.hg19.sites.vcf
omni: s3://cgl-pipeline-inputs/hg19/1000G_omni2.5.hg19.sites.vcf
run-bwa: True
trim: True
amb: s3://cgl-pipeline-inputs/alignment/hg19.fa.amb
ann: s3://cgl-pipeline-inputs/alignment/hg19.fa.ann
bwt: s3://cgl-pipeline-inputs/alignment/hg19.fa.bwt
pac: s3://cgl-pipeline-inputs/alignment/hg19.fa.pac
sa: s3://cgl-pipeline-inputs/alignment/hg19.fa.sa
joint-genotype: True
snp-filter-annotations:
 - QualByDepth
 - FisherStrand
 - StrandOddsRatio
 - ReadPosRankSum
 - MappingQualityRankSumTest
 - RMSMappingQuality
indel-filter-annotations:
 - QualByDepth
 - FisherStrand
 - StrandOddsRatio
 - ReadPosRankSum
 - MappingQualityRankSumTest
run-vqsr: False
snp_filter_name: GERMLINE_SNP_FILTER
snp_filter_expression: "QD < 2.0 || FS > 60.0 || MQ < 40.0 || MQRankSum < -12.5 || ReadPosRankSum < -8.0"
indel_filter_name: GERMLINE_INDEL_FILTER
indel_filter_expression: "QD < 2.0 || FS > 200.0 || ReadPosRankSum < -20.0"
file-size: 200G
xmx: 30G
suffix: .toil
output_dir: /data/my-toil-run
ssec:
unsafe_mode: False
```
