#!/usr/bin/env bash
set -euo pipefail

travel_env_file="${1:-}"
if [[ -z "$travel_env_file" ]]; then
  echo "用法: $0 <env-file>" >&2
  exit 2
fi
if [[ ! -f "$travel_env_file" ]]; then
  echo "配置文件不存在: $travel_env_file" >&2
  exit 2
fi

IFS= read -r -s -p "请输入 DeepSeek 官方 API Key: " travel_deepseek_key
echo
if [[ ${#travel_deepseek_key} -lt 20 ]]; then
  unset travel_deepseek_key
  echo "API Key 长度异常，未修改配置。" >&2
  exit 1
fi

travel_backup_file="${travel_env_file}.before-deepseek-$(date +%Y%m%d-%H%M%S)"
cp -a "$travel_env_file" "$travel_backup_file"
travel_env_dir="$(dirname "$travel_env_file")"
travel_env_tmp="$(mktemp "${travel_env_dir}/.travel-api-env.XXXXXX")"
trap 'unset travel_deepseek_key; [[ -z "${travel_env_tmp:-}" ]] || rm -f "$travel_env_tmp"' EXIT

awk '
  !/^TRAVEL_AI_BASE_URL=/ &&
  !/^TRAVEL_AI_MODEL=/ &&
  !/^TRAVEL_AI_FAST_MODEL=/ &&
  !/^TRAVEL_AI_API_KEY=/
' "$travel_env_file" > "$travel_env_tmp"

printf '%s\n' 'TRAVEL_AI_BASE_URL=https://api.deepseek.com' >> "$travel_env_tmp"
printf '%s\n' 'TRAVEL_AI_MODEL=deepseek-v4-pro' >> "$travel_env_tmp"
printf '%s\n' 'TRAVEL_AI_FAST_MODEL=deepseek-v4-flash' >> "$travel_env_tmp"
printf 'TRAVEL_AI_API_KEY=%s\n' "$travel_deepseek_key" >> "$travel_env_tmp"
chmod 600 "$travel_env_tmp"
mv -f "$travel_env_tmp" "$travel_env_file"
travel_env_tmp=''
unset travel_deepseek_key

echo "已切换为 DeepSeek 官方 API。"
echo "备份文件: $travel_backup_file"
awk -F= '
  /^TRAVEL_AI_BASE_URL=/{print "AI 地址: " $2}
  /^TRAVEL_AI_MODEL=/{print "深度模型: " $2}
  /^TRAVEL_AI_FAST_MODEL=/{print "快速模型: " $2}
  /^TRAVEL_AI_API_KEY=/{print "API Key 已配置: yes（未显示原文）"}
' "$travel_env_file"
