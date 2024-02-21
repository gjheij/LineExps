# Commands for SRF-experiment

```bash
# define subject/session ID
subID=001
sesID=3
```

## BEFORE EXPERIMENT
### create size-response functions
```bash
ff=${DIR_DATA_DERIV}/prf/sub-${subID}/ses-1/sub-${subID}_ses-1_task-2R_model-norm_stage-iter_desc-prf_params.pkl
qsub -N sub-${subID}_ses-1_task-2R_model-norm_stage-iter_desc-srfs_centered -wd $(dirname ${ff}) -q long.q ${DIR_SCRIPTS}/bin/call_sizeresponse --in ${ff} --verbose
```

### make V1 surface
```bash
ff=${DIR_DATA_DERIV}/prf/sub-${subID}/ses-1/sub-${subID}_ses-1_task-2R_model-norm_stage-iter_desc-prf_params.pkl
call_prf2fs -i ${ff} --freeview
```

### find vertex
```bash
master -m 18 -s ${subID} -l ${sesID} --srf_file --norm --manual
```

### Copy parameter file
```bash
src=${DIR_DATA_DERIV}/pycortex/sub-${subID}/ses-${sesID}/sub-${subID}_ses-${sesID}_model-norm_desc-best_vertices.csv 
demo=$(dirname ${PATH_HOME})/project_repos/LineExps/ActNorm3/data/sub-999_ses-0_model-norm_desc-best_vertices.csv
trg=$(dirname ${demo})

# copy file with orig filename to project_repo dir
cp ${src} $(dirname ${demo})

# cp as sub-999_ses-0 for demo
cp ${src} ${demo}
```

## DURING EXPERIMENT

### start environment
```bash
# activate environment and confirm python path
conda activate eyelink
which python
```

### demo for subject prior to entering scanner
```bash
# runs sub-999_ses-0_run-demo
python main.py --demo
```

### run demo mode, calibrate eyetracker, make pngs to create figure
```bash
python main.py -s ${subID} -n ${sesID} --task SRFa --eye --demo --png
```

### task version 1 | no `--png!!`
```bash
python main.py -s ${subID} -n ${sesID} --task SRFa --eye -r 1
```

### task version 2 | no `--png!!`
```bash
python main.py -s ${subID} -n ${sesID} --task SRFb --eye -r 1
```
