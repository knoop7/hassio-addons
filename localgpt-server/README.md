## Home Assistant Add-on ：LocalGPT server

要访问 LocalGPT server 的 Web 界面，请直接在浏览器中打开 `http://<IP>:4567/web`。确保将 `<IP>` 替换为服务器的实际 IP 地址



对于API的调用方法

```
curl http://ip:4567/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini", 
    "messages": [{"role": "user", "content": "你好, GPT!"}],
    "max_tokens": 200
  }'
```
