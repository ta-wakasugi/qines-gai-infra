#!/bin/sh
npm ci  --include=dev
npm run generate-openapi-zod-client
npm run build
npm run start