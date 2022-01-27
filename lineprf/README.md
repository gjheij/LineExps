# pRF mapping around target pRF

![plot](https://github.com/tknapen/linescanning/blob/master/linescanning/examples/figures/exp_prf.png)

In this experiment, we tune the stimulus based on the obtained parameters earlier. It expects a pRF-parameter file in the [prf_params]-folder, with the same subject ID as the one you'll be using to call the experiment. The script reads in the parameter file and creates stimuli based on it; a stimulus that directly stimulates the center only, and an annulus around the center of the pRF to stimulate the surround.

This experiment is based on exptools2.

To be run as:

```python main.py <sub ID> <run number> <hemisphere> <eyelink>```

Run:

```python main.py ```

to get a help-window. Settings for the experiment are in [settings.yml](settings.yml)
