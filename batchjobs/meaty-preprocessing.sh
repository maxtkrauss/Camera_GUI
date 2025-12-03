#!/bin/bash

#SBATCH --account=menon

#SBATCH --partition=notchpeak

#SBATCH --nodes=1

##SBATCH --ntasks-per-node=1

##SBATCH --cpus-per-task=1

#SBATCH --mem=16G

#SBATCH --time=12:00:00

#SBATCH --job-name=morales-meat-preprocessing-12022025

#SBATCH -o meat-slurmjob-%j.out-%N

#SBATCH -e meat-slurmjob-%j.error-%N

#SBATCH --mail-type=FAIL,BEGIN,END

#SBATCH --mail-user=u1344001@umail.utah.edu

## Load Miniforge
# module load miniforge3/24.9.0

# ## Activate the conda environment

# source activate /uufs/chpc.utah.edu/common/home/u1344001/BICEPS_HSI_2025/hsp_env

# ## Navigate to the project directory

# cd /uufs/chpc.utah.edu/common/home/u1344001/BICEPS_HSI_2025/Camera_GUI

preprocess () {
    # 1: Raw dir
    # 2: Prefix for renaming
    # 3: Final directory to place things in

    local raw_dir=$1/captures
    local dark_dir=$1/darkframes
    local sub_dir=$1/darksub
    local processed_dir=$1/processed

    echo $1 $2

    ## Run the dark frame subtraction script
    python dark_frame_sub.py -i "$raw_dir" -o "$sub_dir" -d "$dark_dir"

    ## Run the cropping script
    python image_preprocessing.py -i "$sub_dir" -xt 0 -yt 0 -st 2032 -xc 57 -yc 24 -sc 352 -o "$processed_dir"

    ## Add a prefix to the files to make it easier to consolidate
    python add_prefix.py $2 $processed_dir/cubert $processed_dir/thorlabs

    cp $processed_dir/cubert/\*.tif $3/cubert
    cp $processed_dir/thorlabs/\*.tif $3/thorlabs
}

data_dir=/scratch/general/nfs1/u1344001/data

chicken_dir=$data_dir/Exp6
turkey_dir=$data_dir/Exp8
beef_pork_dir=$data_dir/Exp9
consolidate_dir=$data_dir/MeatyDB


preprocess $chicken_dir ck_ $consolidate_dir
preprocess $turkey_dir tk_ $consolidate_dir
preprocess $beef_pork_dir bp_ $consolidate_dir

python data_stretch.py $consolidate_dir $consolidate_dir 9 31415 .tif

python reindex.py $consolidate_dir