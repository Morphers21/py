# Survival Shooter

A simple pygame top-down shooter with scaling infinite enemy waves, recurring
bosses, shot cooldowns, and a repeatable points shop.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Controls

- `ENTER` starts the game from the menu.
- `WASD` moves the player.
- Left mouse click shoots toward the cursor.
- `TAB` opens or closes the shop.
- `1`-`9` and `0` buy repeatable shop upgrades while the shop is open.
- `R` restarts after game over.
- `M` returns to the menu after game over.
- `Q` quits.

Bosses start at 50 seconds, and infinite waves begin after 60 seconds.
