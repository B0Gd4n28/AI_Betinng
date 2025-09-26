# Replit configuration
entrypoint = "bot/bot.py"

[nix]
channel = "stable-22_11"

[deployment]
run = ["python", "-m", "bot.bot"]

[[ports]]
localPort = 8000
externalPort = 80