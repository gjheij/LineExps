#!/usr/bin/env python
#$ -j Y
#$ -cwd
#$ -V

from linescanning import utils, plotting
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os 
import numpy as np
import sys
opj = os.path.join

def main(argv):

    """
---------------------------------------------------------------------------------------------------
plot_stimuli.py

Make a figure of the screenshot made during the `--demo` run.

Parameters
----------
    <log_dir>   directory containing the png-files. Run experiment with:
                `python main.py --png --demo --fix`

Returns
----------
    a png/svg figure

Example
----------
    plot_stimuli.py -i sub-01_ses-1_task-2R_model-norm_stage-iter_desc-prf_params.pkl
    call_sizeresponse -i prf_estimates.pkl -o srfs.csv --unique

---------------------------------------------------------------------------------------------------
    """

    scr_path = argv[0]
    if not os.path.exists(scr_path):
        raise ValueError(f"Could not find directory: '{scr_path}'")
    ff = utils.FindFiles(scr_path, extension="png").files

    print(*ff, sep="\n")

    defs = plotting.Defaults()
    if len(ff)>0:
        imgs = []
        imgs_bin = []
        for file in ff:
            img = (255*mpimg.imread(file)).astype('int')
            img_bin = np.zeros_like(img[...,0])
            img_bin[np.where(((img[..., 0] < 40) & (img[..., 1] < 40)) | ((img[..., 0] > 200) & (img[..., 1] > 200)))] = 1
            imgs.append(img)
            imgs_bin.append(img_bin)

        fig,axs = plt.subplots(ncols=4,figsize=(20,5), sharex=True, sharey=True)
        cols = ["r","g","b"]
        for ix,img in enumerate(imgs_bin):
            cm = utils.make_binary_cm(cols[ix])
            axs[0].imshow(img, cmap=cm)
            plotting.conform_ax_to_obj(
                ax=axs[0], 
                title="overlap", 
                add_hline=img.shape[0]//2,
                add_vline=img.shape[1]//2,
                fontname=defs.fontname
            )

        for ix,img in enumerate(imgs):
            axs[ix+1].imshow(img)
            plotting.conform_ax_to_obj(
                ax=axs[ix+1], 
                title=f"ev-{ix+1}", 
                add_hline=img.shape[0]//2,
                add_vline=img.shape[1]//2,
                fontname=defs.fontname
            )
        
        for ax in fig.axes:
            ax.axis('off')

        comps = utils.split_bids_components(scr_path)
        base = ""
        for el in ["sub","ses","task","run","acq"]:
            if el in list(comps.keys()):
                if el == "sub":
                    base += f"sub-{comps['sub']}"
                else:
                    base += f"_{el}-{comps[el]}"

        fname = opj(os.path.dirname(scr_path), f"{base}_desc-stimuli")
        print(f"Writing '{fname}'")
        for ext in ["svg","png"]:
            fig.savefig(
                f"{fname}.{ext}",
                bbox_inches="tight",
                facecolor="white",
                dpi=300
            )    

if __name__ == "__main__":
    main(sys.argv[1:])
