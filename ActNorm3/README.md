# Size response experiment

![plot](https://github.com/tknapen/linescanning/blob/master/linescanning/examples/figures/exp_centersurround.png)

In this experiment, we tune the stimulus based on the obtained parameters earlier. It expects a pRF-parameter file in the [prf_params]-folder, with the same subject ID as the one you'll be using to call the experiment. In the settings file, you can specify the sizes of the stimulus in degree-of-visual angle in the variable `stim_sizes` that you would like to present. The other parameter (`stim_repetitions`) that you need to set controls how often each stimulus is presented. Together this controls the number of stimuli presented and thus the length of the experiment. The default settings are based on the simulations in this [notebook](https://github.com/tknapen/linescanning/blob/master/linescanning/notebooks/prf_simulate2.ipynb).

This experiment is based on exptools2.

To be run as:

```python main.py <sub ID> <run number> <hemisphere> <eyelink>```

Run:

```python main.py ```

to get a help-window. Settings for the experiment are in [settings.yml](settings.yml)

Button instructions:

- Press 'b' when the contrast was HIGH then LOW

- Press 'e' when the contrast was LOW then HIGH
