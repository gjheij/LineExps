# Checkerboard experiment

This experiment is based on exptools2.

To be run as:

```python main.py <sub ID> <run number> <hemisphere> <eyelink>```

Run:

```python main.py```

to get a help-window. Settings for the experiment are in [settings.yml](settings.yml)

Button instructions:

- Press 'b' when the fixation dot changes from green to red and red to green

You can either run this experiment as block design or event-related design. Change the following items in the [settings.yml](settings.yml)-file:

- Block design:
    - `stim_repetitions`: number of blocks
    - `static_isi`: length of block
    - `start_duration`: 0
    - `end_duration`: set same as `static_isi`
    - `stim_duration`: set same as `static_isi`

- Event-related design:
    - `stim_repetitions`: number of presentations
    - `static_isi`: set to "None"
    - `start_duration`: baseline period (e.g., 20 seconds)
    - `end_duration`: baseline at the end (e.g., 20 seconds)
    - `stim_duration`: length of presentation (e.g., 2 seconds)
