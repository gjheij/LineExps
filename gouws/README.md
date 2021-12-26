# Gouws-like experiment

![plot](https://github.com/tknapen/linescanning/blob/master/linescanning/examples/figures/exp_gouws.png)

This experiment is similar to the one described in Gouws, et al. (2014). Here, hemifield stimuli consists of wedged that are cleanly separated at the horizontal merdian. These two wedges always move in opposite directions. The task for the participant is to count how often the direction changes. Such an attentional task is thought to increase the negative BOLD compared to our other `twosided` experiment.

This experiment is based on exptools2.

To be run as:

```python main.py 01 01```

where the first `01` is the subject number, and the second `01` is the run number. Settings for the experiment are in [settings.yml](settings.yml)
