# Overview

## Setup Python environment

Follow the usual steps to setup a Python virtual env and install the required packages:

```
python3 -m venv <VIRTUAL_ENV_PATH>
source <VIRTUAL_ENV_PATH>/bin/activate
python3 -m pip install -r requirements.txt
```

## Development

Run `python app.py` to get the Dash app running on `http://127.0.0.1:8050`. Alternatively, `http://localhost:8050` should work as well on most standard machines.


## To Run Backend code on Local Machine for testing

- Enter layer containing app.py on cmd
- To test ggldecode.py run `python ./backend/ggldecode.py`
- To test i2ldecode.py run `python ./backend/i2ldecode.py`
