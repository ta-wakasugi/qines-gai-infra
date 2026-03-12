#!/bin/bash

CLIENT_ID="18sq895fb54nepjltt38uhkecj"

# メールアドレスとパスワードを入力してもらう
echo "Enter your email address:"
read email
echo "Enter your password:"
read -s password

# ログインしてトークンを取得
idp_response=$(aws cognito-idp initiate-auth \
        --client-id 125rhluldrc2p94p6f5upffkej \
        --auth-flow USER_PASSWORD_AUTH \
        --auth-parameters "USERNAME=$email,PASSWORD=$password" \
        --region ap-northeast-1)

id_token=$(echo $idp_response | jq -r '.AuthenticationResult.IdToken')
access_token=$(echo $idp_response | jq -r '.AuthenticationResult.AccessToken')
sub=$(jwt decode -j $id_token | jq -r '.payload.sub')

# Cookie-Editorでインポートできる形式に整形
base_header='"domain": "localhost","hostOnly": true,"httpOnly": false,"path": "/","sameSite": null,"secure": false,"session": true,"storeId": null, \n'
result=$(cat << EOS
[{\n
    $base_header
    "name": "CognitoIdentityServiceProvider.${CLIENT_ID}.LastAuthUser", \n
    "value": "$sub" \n
}, \n
{\n
    $base_header
    "name": "CognitoIdentityServiceProvider.${CLIENT_ID}.${sub}.idToken", \n
    "value": "$id_token" \n
}, \n
{\n
    $base_header
    "name": "CognitoIdentityServiceProvider.${CLIENT_ID}.${sub}.accessToken", \n
    "value": "$access_token" \n
}]
EOS
)

echo $result

# $resultをクリップボードにコピーする
echo $result | pbcopy
echo "クリップボードにコピーしました。Cookie-Editorでインポートしてください。"