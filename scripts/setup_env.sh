#!/bin/bash

# UIDの下二桁をポート・IPアドレスに利用
uid=$(id -u $(whoami) | cut -c 3-4)
echo "USER_ID=$uid" > .env

user_name=$(id -u -n)
echo "USER_NAME=$user_name" >> .env
# この環境変数を設定すると、docker compose -p {COMPOSE_PROJECT_NAME} {command}になる
echo "COMPOSE_PROJECT_NAME=qines-gai-${user_name}" >> .env

# TODO: AWS CLIを使ってパラメータストアからAPIキーを落とす
