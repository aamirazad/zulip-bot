# Zulip Bots

This repo hosts my moderation bot for the HASD zulip community as well as any other
utility bot I create.

The code that I wrote (not the [zulip app](https://github.com/zulip/python-zulip-api) template files) can be found [here](https://github.com/aamirazad/zulip-bot/blob/main/zulip_bots/zulip_bots/bots/moderation/moderation.py)

## Demo (SoM)

This [video](https://hc-cdn.hel1.your-objectstorage.com/s/v3/5f45a6faa4747cb5e21ea14421df005b8da2caa6_03.07.2025_13.56.44_rec.mp4) is a super easy way to see the bot in action; I **highly recommend** you just watch this.

https://github.com/user-attachments/assets/b319140f-ce7d-47bc-ae8b-ddec0bc0b000

If you insist and want to try it out yourself, please visit https://hasd.zulipchat.com/join/a6amkfo3hlv4cqqr3kvpl55w/ and create an account. _Please_ don't mess anything up and stay in the bot chat topic under mod chat. Mention the bot with `@**HASD**` to get started.

And if, for whatever reason, you want to run the bot yourself on your own hardware, you will need your own [zulip](http://zulip.com/) organization, and just follow the development steps below and throw the run-bot command as a background task.

## Run the bot

1. Clone the Git repo:

    ```
    git clone https://github.com/aamirazad/zulip-bot.git
    ```

2. Make sure you edit the moderation.py's global variables to work with your org.

3. Run:

    ```
    python3 ./tools/provision
    ```

    Make sure you have [pip](https://pip.pypa.io/en/stable/installing/).

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

6. Run the bot
    ```
    zulip-run-bot moderation --config-file ./zuliprc
    ```

Throw this in screen or make a systemd file to run the bot in the background.

### AI Use

All the features of the bot was written by hand.
Although my code worked, it was a bit hard to read, so I had AI clean it up. No functionality was added, and the commit can be found [here](https://github.com/aamirazad/zulip-bot/commit/52955e3347c0b8ecd203fbe809ff07276999b1b0). 
