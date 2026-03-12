/*
 * 01_databases.sql
 * -------------------------------------------------------
 * Keycloak 用とアプリケーション用の DB／ユーザーを作成する
 *  - template0 を使用して POSTGRES_DB 相当の設定を継承
 *  - ENCODING / LC_COLLATE / LC_CTYPE は明示的に UTF8 / C
 * -------------------------------------------------------
 */

-- ------------------------------------------------------
-- Keycloak
-- ------------------------------------------------------
CREATE ROLE keycloak LOGIN PASSWORD 'kcpass';

CREATE DATABASE keycloak
  WITH OWNER    = keycloak
       TEMPLATE = template0
       ENCODING = 'UTF8'
       LC_COLLATE = 'C'
       LC_CTYPE   = 'C';

GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;

-- ------------------------------------------------------
-- Application
-- ------------------------------------------------------
CREATE ROLE qinesgai LOGIN PASSWORD 'qinesgai';

CREATE DATABASE qinesgai
  WITH OWNER    = qinesgai
       TEMPLATE = template0
       ENCODING = 'UTF8'
       LC_COLLATE = 'C'
       LC_CTYPE   = 'C';

GRANT ALL PRIVILEGES ON DATABASE qinesgai TO qinesgai;