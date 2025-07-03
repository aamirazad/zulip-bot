# Zulip Bots

This repo host my moderation bot for the HASD zulip community as well as any other
utility bot I create.

## Demo (SoM)

This [video](https://hc-cdn.hel1.your-objectstorage.com/s/v3/5f45a6faa4747cb5e21ea14421df005b8da2caa6_03.07.2025_13.56.44_rec.mp4) is a super easy way to see the bot in action, I **highly recommend** you just watch this.

If you insist and want to try it out yourself, please visit https://hasd.zulipchat.com/join/a6amkfo3hlv4cqqr3kvpl55w/ and create an account. _Please_ don't mess anything up and stay in the bot chat topic under mod chat. Mention the bot with `@**HASD**` to get started.

And if for whatever reason you want to run the bot yourself on your own hardware, you will need your own [zulip](http://zulip.com/) organization, and just follow the development steps below and throw the run-bot command as a background task.

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
    source zulip-api-py3-venv/bin/activate
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
    zulip-run-bot moderation --config-file ~/path/to/zuliprc
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
