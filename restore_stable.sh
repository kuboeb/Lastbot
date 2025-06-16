#!/bin/bash
echo "Восстановление стабильной версии v0.9..."
git checkout stable-version
sudo systemctl restart crypto-bot
sudo systemctl restart crypto-admin
echo "✅ Восстановлено!"
