# Public Examples Repository

Welcome to the Code Examples Repository! This public repository contains a variety of code examples primarily intended for documentation purposes.

These examples are not intended to be executed but rather to be used as a reference.

## Running VNA Example

**NOTE:**
Driver `public_code_example/drivers/znb.py` was written for the **R&S ZNB** VNA instrument, it will also work with their ZNA model.

You can run the `main.py` file which will open a connection to a VNA instrument and get data from trace "Trc1".

1. Install dependencies

```python
poetry install
poetry shell
```

1. Connect instrument
2. Change VNA address in `main.py`

```python
ZNB_ADDR = "TCPIP::192.168.29.103::5025::SOCKET" # EDIT ME
```

3. Run main

```
python3 main.py
```
