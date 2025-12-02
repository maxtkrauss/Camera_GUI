#!/bin/bash

#SBATCH --account=menon

#SBATCH --partition=notchpeak

#SBATCH --nodes=1

##SBATCH --ntasks-per-node=1

##SBATCH --cpus-per-task=1

#SBATCH --mem=32G

#SBATCH --time=12:00:00

#SBATCH --job-name=morales-colorchart-preprocessing-11202025

#SBATCH --output=morales-colorchart-preprocessing-11202025.log

#SBATCH --mail-type=FAIL,BEGIN,END

#SBATCH --mail-user=u1344001@umail.utah.edu

## Load Miniforge
module load miniforge3/24.9.0

## Activate the conda environment

source activate /uufs/chpc.utah.edu/common/home/u1344001/BICEPS_HSI_2025/hsp_env

## Navigate to the project directory

cd /uufs/chpc.utah.edu/common/home/u1344001/BICEPS_HSI_2025/Camera_GUI

raw_dir=/scratch/general/nfs1/u1344001/data/Exp7/captures
dark_sub_dir=/scratch/general/nfs1/u1344001/data/Exp7/dark_sub
processed_dir=/scratch/general/nfs1/u1344001/data/Exp7/processed

darkframe_dir=/scratch/general/nfs1/u1344001/data/Exp7/darkframes

## Run the dark frame subtraction script

python dark_frame_sub.py -i "$raw_dir" -o "$dark_sub_dir" -d "$darkframe_dir"

## Run the cropping script
python image_preprocessing.py -i "$dark_sub_dir" -xt 0 -yt 0 -st 2032 -xc 57 -yc 24 -sc 352 -o "$processed_dir"