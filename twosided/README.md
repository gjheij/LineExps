# Hemifield experiment

![plot](https://github.com/tknapen/linescanning/blob/master/linescanning/examples/figures/exp_hemifield.png)

This is our initial experiment, where we present flickering checkerboards to either the left or right side of the visual field. Meanwhile, the subject is to fixate on the cross and detect when this fixation cross changes. Because this did not (yet) evoke the negative BOLD response we desired, we created a separate experiment `Gouws`. That experiment contains slightly different stimuli and has an attentional task embedded.

This experiment is based on exptools2.

To be run as:

```python main.py 01 01```

where the first `01` is the subject number, and the second `01` is the run number. Settings for the experiment are in [settings.yml](settings.yml)
