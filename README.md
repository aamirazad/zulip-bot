# Zulip Bots

This repo host my moderation bot for the HASD zulip community as well as any other
utility bot I create.

## Development

1. Clone the Git repo:

    ```
    git clone https://github.com/aamirazad/zulip-bot.git
    ```

2. Make sure you have [pip](https://pip.pypa.io/en/stable/installing/).

3. Run:

    ```
    python3 ./tools/provision
    ```

    This sets up a virtual Python environment in `zulip-api-py<your_python_version>-venv`,
    where `<your_python_version>` is your default version of Python. If you would like to specify
    a different Python version, run

    ```
    python3 ./tools/provision -p <path_to_your_python_version>
    ```

4. If that succeeds, it will end with printing the following command:

    ```
    source /.../python-zulip-api/.../activate
    ```

    You can run this command to enter the virtual environment.
    You'll want to run this in each new shell before running commands from `python-zulip-api`.

5. Once you've entered the virtualenv, you should see something like this on the terminal:

    ```
    (zulip-api-py3-venv) user@pc ~/python-zulip-api $
    ```

    You should now be able to run any commands/tests/etc. in this
    virtual environment.

6. Run the bot in development mode:
    ```
    zulip-run-bot <bot-name> --config-file ~/path/to/zuliprc
    ```

### Running tests

You can run all the tests with:

`pytest`

or test individual packages with `pytest zulip`, `pytest zulip_bots`,
or `pytest zulip_botserver` (see the [pytest
documentation](https://docs.pytest.org/en/latest/how-to/usage.html)
for more options).

To run the linter, type:

`./tools/lint`

To check the type annotations, run:

`./tools/run-mypy`

### AI Use

AI was used to generate the moderation.py file but almost all of it was
changed in some way (cause it didn't work at all) really only the structure
remains.
