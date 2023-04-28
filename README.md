<p align="center">
    <img src="https://img.shields.io/github/license/DioniS1902/FRT" />
    <img src="https://img.shields.io/github/stars/DioniS1902/FRT" />
    <img src="https://img.shields.io/docker/pulls/dionis1902/frt" />
    <img src="https://img.shields.io/github/downloads/Dionis1902/FRT/total">
    <img src="https://img.shields.io/badge/python-3.10%2B-brightgreen">
</p>

![Logo](/images/big_logo.png)
<h1 align="center">Disclaimer</h1>

<p align="center">THIS SOFTWARE IS PROVIDED FOR EDUCATIONAL USE ONLY!</p>
<p align="center">IF YOU ENGAGE IN ANY ILLEGAL ACTIVITY, THE AUTHOR IS NOT RESPONSIBLE FOR THIS AND FOR POSSIBLE ACCOUNT BLOCKING.</p>
<p align="center">THE AUTHOR DOES NOT PUBLISH ANY IP ADDRESSES AND DOES NOT INVITE ANY ILLEGAL ACTIONS. ALL AT YOUR OWN RISK.</p>
<p align="center">BY USING THIS SOFTWARE, YOU AGREE TO BE BOUND BY THESE TERMS. I WARNED YOU.</p>

## Contents
* [Main information](#main-information)
    * [Features](#features)
    * [Api ID and Api hash](#api-id-and-api-hash)
    * [Default credentials](#default-credentials)
    * [Supported methods for adding an account](#supported-methods-for-adding-an-account)
    * [Functions](#functions)
* [How run](#how-run)
    * [Docker compose](#docker-compose)
    * [Docker compose local](#docker-compose-local)
    * [Python](#python)
* [Screenshots](#screenshots)
* [Coming soon](#coming-soon)
* [Say thank you me](#say-thank-you-me)

## Main information

### Features
- Web interface (Dark and light theme, WOOOW)
- Ability to import an account using all popular methods
- Ability to select random or specific accounts to perform the function
- Ability to export account as TData
- Convenient account setting (Basic data and profile photo)
- Possibility to get a code from a telegram on the site
- Ability to configure global proxies and personal proxies for each account
- Ability to add your own list of account names
- Live logs with the ability to save them
- And many other small features

### Api ID and Api hash
You can find instructions on how to get an Api ID and Api hash [here](https://core.telegram.org/api/obtaining_api_id)

### Default credentials
By default, the website is launched on port 8080 but you can change this 
```
Login: root
Password: roottoor
```

### Supported methods for adding an account
- Phone number (Will automatically create an account if it does not exist)
- Session file (Pyrogram and Telethon)
- Session string (Pyrogram)
- QR Code
- TData

### Functions
- Join groups
- Leave groups
- Reaction raid
- Spam chat
- Spam chat by channel
- Spam comments
- Spam comments by channel
- Spam PM
- Vote poll
- [Suggest a function](https://github.com/Dionis1902/FRT/issues/new?assignees=&labels=function&template=new-function.md&title=%5BFUNCTION%5D)

## How run
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/YGdHQR?referralCode=cTSsKD)
### Docker compose
- Install docker and docker-compose
- Create file docker-compose.yml
```yml
# docker-compose.yml
version: "3.9"
services:
  botnet:
    container_name: frt
    image: dionis1902/frt:latest
    restart: always
    volumes:
      - ./data:/data
    ports:
      - '8080:80' # any_port_you_like:8080
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://root:secret_password@postgres/data

  postgres:
    container_name: postgres_container
    image: postgres:latest
    restart: always
    volumes:
      - ./data/postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: data
      POSTGRES_PASSWORD: secret_password
      POSTGRES_USER: root
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 5s
      retries: 5
```
- Run commands
```
$ docker-compose pull
$ docker-compose run -d
```

### Docker compose local
- Install docker and docker-compose
```
$ git clone git@github.com:Dionis1902/FRT.git
$ cd FRT
$ docker-compose build
$ docker-compose run -d
```

### Python
- Install Python 3.10+
```
$ git clone git@github.com:Dionis1902/FRT.git
$ cd FRT
$ python -m venv env

### Linux 
$ source env/bin/activate
$ export DATABASE_URL=postgresql://root:secret_password@127.0.0.1/data

### Windows
$ .\env\Scripts\activate
$ set DATABASE_URL=postgresql://root:secret_password@127.0.0.1/data 

$ pip install -r requirements.txt

$ python main.py
OR
$ uvicorn main:app --host 0.0.0.0 --port 8080
```

## Screenshots
<details><summary>Screenshots of pages</summary>
  <img src="/images/accounts.png" />
  <img src="/images/functions.png" />
  <img src="/images/tasks.png" />
  <img src="/images/task.png" />
  <img src="/images/settings.png" />
</details>

## Coming soon
- Live functions (For example, to automatically write comments under new posts)
- Phishing link
- Integration with ChatGPT or/and Dialogflow
- Ability to write custom functions by visual programing like scratch

## Say thank you me
<p align="center">
    <a href="https://www.buymeacoffee.com/Dionis1902"><img src="https://i.imgur.com/zE8Y8Dp.png"></a>
</p>

<p align="center">USDT (ERC20) : 0xB8314551f0633aee73f93Ff4389629B367e59189</p>
<p align="center">USDT (TRC20) : TYJmX4R22NmSMBu7HWbwuwRr7TW9jN5az9</p>
<p align="center">BTC : bc1q3jgp25rc8qtzx0fwd9ltpy45yv05hphu7pvwla</p>
<p align="center">ETH : 0xB8314551f0633aee73f93Ff4389629B367e59189</p>
<p align="center">BNB (Smart Chain) : 0xB8314551f0633aee73f93Ff4389629B367e59189</p>
