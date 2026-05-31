# Survival Shooter

A simple pygame top-down shooter with scaling infinite enemy waves, recurring
bosses, shot cooldowns, XP level-ups, stat multiplier cards, unlockable weapons, and a compact repeatable points shop.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Controls

- `ENTER` starts the game from the menu.
- `WASD` moves the player.
- Left mouse click shoots toward the cursor; hold left click to keep firing.
- `TAB` opens or closes the compact shop.
- `I` opens or closes the stats/weapons menu.
- `SPACE` dashes/dodges with a short burst of invincibility.
- `E` drops a mine after you unlock mine cards.
- Hold and release left click for a charged shot.
- Click shop upgrades or press `1`-`9` / `0` to buy repeatable upgrades while the shop is open.
- `1`-`3` picks a level-up card when the card screen appears.
- `R` restarts after game over.
- `M` returns to the menu after game over.
- `Q` quits.

Bosses start at 50 seconds, and infinite waves begin after 60 seconds. Kills give XP; each level needs more XP than the last and offers cards for stats and weapons, including damage, fire rate, health, armor, speed, XP gain, regeneration, piercing bullets, rockets, lasers, scatter shots, point bonuses, and scaling fractional healing on kill, boomerangs, chain lightning, mines, charge shots, curses, and railgun synergy.
