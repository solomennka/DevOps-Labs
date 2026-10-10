#!/usr/bin/env bash
set -u
BASE="https://app.local.test"

printf '\n1) HTTP must redirect to HTTPS (expect 301):\n'
curl -sSI http://app.local.test/ | head -n 1

printf '\n2) API should show both backend IDs (run slowly to avoid rate limit):\n'
for i in 1 2 3 4 5 6; do
  curl -ksS "$BASE/api/health"
  printf '\n'
  sleep 0.7
done

printf '\n3) Admin without password must return 401:\n'
curl -ksS -o /dev/null -w 'HTTP %{http_code}\n' "$BASE/admin"

printf '\n4) Docs alias must return 200:\n'
curl -ksS -o /dev/null -w 'HTTP %{http_code}\n' "$BASE/docs/"

printf '\n5) Nonexistent page must return 404 and custom page text:\n'
curl -ksS -w '\nHTTP %{http_code}\n' "$BASE/does-not-exist"

printf '\n6) Other vhost should show its own page:\n'
curl -ksS https://other.local.test/ | grep -o 'Это второй сайт' || true

printf '\n7) Unknown HTTPS host must not show the app (expect 404):\n'
curl -ksS --resolve unknown.local.test:443:127.0.0.1 -o /dev/null -w 'HTTP %{http_code}\n' https://unknown.local.test/

printf '\n8) Burst should include HTTP 429 responses:\n'
for i in 1 2 3 4 5 6 7 8; do
  curl -ksS -o /dev/null -w '%{http_code}\n' "$BASE/api/health" &
done
wait

printf '\n9) To test failover separately, run: docker compose stop backend1\n'
printf '   Then: curl -k https://app.local.test/api/health\n'
printf '   Restore: docker compose start backend1\n'
