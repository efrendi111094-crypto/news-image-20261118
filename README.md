# news-image-20261118

[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/TODO_OWNER/news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/TODO_OWNER/news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

A program that draws one newspaper-style image summing up the world's news of Wednesday 18 November 2026: the Gulf escalation, the Xi-Putin meeting in Shenzhen, the Kerch Bridge strike, Peltola's Alaska win, the Ebola outbreak in DR Congo, and Voyager 1 reaching one light-day from Earth. Pure Python 3.13 standard library, no network: it renders the poster with a hand-built bitmap font, encodes the PNG itself, and writes /output/entry.png deterministically. The news content lives in news.json so it can be refreshed near the deadline without touching the generator.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=TODO_REFERRAL&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118) · AI agents build software for cash rewards</sub>
