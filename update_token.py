import json
import os

# 配置文件路径
config_path = 'config/config.json'

# 新的 token（从日志中获取）
new_token = '622121be-663d-44d7-b65a-8763f4502e2c'

print('🔧 更新配置文件中的 Token...\n')

# 读取现有配置
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 显示当前 token
old_token = config['SYSTEM_OPTIONS']['NETWORK']['WEBSOCKET_ACCESS_TOKEN']
print(f'当前 Token: {old_token}')
print(f'新的 Token: {new_token}\n')

# 更新 token
config['SYSTEM_OPTIONS']['NETWORK']['WEBSOCKET_ACCESS_TOKEN'] = new_token

# 写回配置文件
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print('✅ Token 已更新！')
print(f'\n配置文件: {os.path.abspath(config_path)}')
print(f'新的 Token: {new_token}')
