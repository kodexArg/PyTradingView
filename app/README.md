routing 8080->80

sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
sudo iptables -t nat -I OUTPUT -p tcp -d 127.0.0.1 --dport 80 -j REDIRECT --to-ports 8080


webhook in TradingView:

{
  "strategy": "[k] 5/8/13",
  "token": "{{ticker}}",
  "close": {{close}},
  "action": "{{strategy.order.action}}",
  "direction": "{{strategy.market_position}}",
  "interval": "{{interval}}",
  "sent_at": "{{timenow}}",
  "strprice": {{strategy.order.price}},
  "volume": {{volume}},
  "ohlc": [
    {{open}},
    {{close}},
    {{high}},
    {{low}}
  ]
}

{
  "strategy": "{{strategy.title}}",
  "token": "{{ticker}}",
  "close": {{close}},
  "action": "{{strategy.order.action}}",
  "direction": "{{strategy.market_position}}",
  "interval": "{{interval}}",
  "sent_at": "{{timenow}}",
  "strprice": {{strategy.order.price}},
  "volume": {{volume}},
  "ohlc": [
    {{open}},
    {{close}},
    {{high}},
    {{low}}
  ]
}