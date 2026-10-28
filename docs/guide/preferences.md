# Preferences

`preferences.json` lives in your **project root** and is the only place for channel-specific choices. Aurora reads it at the start of every command and passes its path to every subagent. If it is missing, she asks you to run `/aurora interview`.

The file is flat and human-editable; unknown keys are kept. Typical shape:

```json
{
  "channel": "Dev Notes with Lia",
  "language": "en",
  "niche": "web development",
  "audience": "junior and mid developers",
  "tone": "warm, curious, dry humor",
  "persona": {
    "character": "Lia, a retired lighthouse keeper turned developer",
    "story": "Kept a lighthouse for 20 years; now debugs the same way: patience and a good lamp.",
    "personality": "calm, precise, quietly funny",
    "catchphrases": ["keep the lamp lit"],
    "never": ["insult viewers", "promise get-rich-quick results"]
  },
  "voice": { "name": "Lia", "voice_id": "<your ElevenLabs voice id>" },
  "palette": ["#0b1d3a", "#1e6091", "#ffd166"],
  "topics_like": ["debugging", "tooling"],
  "topics_avoid": ["crypto"],
  "research_sources": ["https://news.ycombinator.com", "https://github.com/trending"],
  "free_tier": true,
  "blender": true
}
```

## Keys

| Key | Meaning |
|---|---|
| `channel`, `audience`, `niche`, `language` | Who it is for and in what language scripts and subtitles are written. |
| `tone`, `humor`, `avoid` | Voice of the writing; what is funny; what is off limits. |
| `persona` | Object: `character`, `story`, `personality`, `catchphrases`, `never`. The narrator Aurora never breaks. |
| `voice` | Name or `voice_id`. If unset, Aurora A/B-tests candidate voices and saves your pick. |
| `visual_style`, `palette`, `mascot`, `fonts` | Look of the videos. `palette` themes the web engine. |
| `topics_like`, `topics_avoid`, `research_sources` | Steer theme discovery. |
| `code_depth` | Technical depth, if the niche has code. |
| `checkpoints`, `pace`, `subtitles`, `music` | How involved you are; speaking pace; burned-in subtitles or `.srt` only; music. |
| `thumbnail_style`, `title_style`, `cta` | Packaging defaults; the like/subscribe ask. |
| `joke_bank` | Gags Aurora rotates (never the same one twice in a row). |
| `labels` | Words used in descriptions: `sources`, `attributed`. |
| `blender` | `false` disables 3D hero scenes. |
| `free_tier` | `false` never sends work to free models (free endpoints may log prompts). |
| `min_tier` | `0`-`2`, the lowest [cost-ladder](cost-ladder.md) tier allowed. |
| `budget_tokens_per_video` | Warn at 75%, stop at 100%. |
| `notes` | Free text for anything else. |

!!! tip
    Do not edit the skill to fit your channel. Put it here. One install then serves any number of channels, languages and niches.
