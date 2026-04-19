# girlbot300

> [!NOTE]
> Feel free to use this a base but it is *not* a template.
> You *will* need to modify the code heavily to get it useable for anything else

## How to Use

1. Clone repository - `git clone https://github.com/lumilovesyou/Nightlight-GirlBot300.git`
2. Open directory - `cd ./Nightlight-GirlBot300`
3. Set up environment variables - `nano .env`

    ```env
    USERNAME=username
    PASSWORD=password
    VERSION=1.0.0
    ABOUT_MESSAGE="Username: %u, version: %v, commands: %c"
    UPDATE_MESSAGE="New version out! Username: %u, version: %v, commands: %c"
    COOLDOWN=60
    ```

4. Set up the venv - `python3 -m venv venv && source venv/bin/activate`
5. Install dependencies - `pip3 install -r requirements.txt`
6. Run - `python3 ./index.py`

## About

The `.env` file has several fields to explain.

`USERNAME` - The username of the account you're connecting to
`PASSWORD` - The password of the account you're connecting to
`VERSION` - The version of the bot. Used for about and update messages
`ABOUT_MESSAGE` - A message meant to introduce the bot. A new one will be sent every time the `VERSION` value in incremented
`UPDATE_MESSAGE` - A message similar to the above field but meant to introduce new features
`COOLDOWN` - The time between running actions in seconds

For the `ABOUT_MESSAGE` and `UPDATE_MESSAGE` fields there's several placeholder keys you can use. `%u` is replaced with the `USERNAME` field, `%v` is replaced with the `VERSION` field, and `%c` is replaced with the values from the COMMANDS dictionary in `index.py` split by newlines.
