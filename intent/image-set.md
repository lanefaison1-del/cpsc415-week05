# Intent: image set (Week 6)

## Goal
Five pictures of one original pocket creature, a fox kit, each adapted to a different habitat
(forest, desert, ocean, city, snow), each with its own name in a banner at the top. Every picture
is checked by a vision model against a yes/no list made from its prompt, and the answers are
checked in code, so a wrong critique shows up instead of being trusted.

## Who it is for
Me, for Team Project 1 (Pocket Creatures): this set becomes `images/lane/` in the team
repository, and the web page I am building there shows the same checklist result. Without it I
would look at each picture and take a model's opinion of it at its word.

## Constraints
- Python, in `.venv` (Python 3.11); the `openrouter` SDK for the Image API and the vision call.
- Image model `black-forest-labs/flux.2-klein-4b` (about $0.014 per image), compared on one
  prompt with `google/gemini-3.1-flash-lite-image`.
- Critic `minimax/minimax-m3`, checked by `xiaomi/mimo-v2.6-flash`.
- One generation per prompt, one critique per image, fixed seeds 6301–6305, no retries. The
  whole lab stays under $0.25.
- The team's style text, word for word, so my set matches Ethan's: plain white background, the
  name in a banner, no other text. The habitat shows in the creature (fur, gear), not in a scene.
- Original creatures only: no franchise, character, or real person. The key comes from the
  environment and never reaches a commit.
- Due Monday, November 2, 2026, 1:30 PM.

## Not in scope
The web page and server (team repository), the team's critic module (Joud's), regenerating a
picture that came out wrong, and picking the best of several pictures.

## Success looks like
- Five images in `week06/images/` with a `manifest.json` that records prompt, seed, model, media
  type, and the cost from the reply for each.
- For each image the checker says ok, or names each requirement that is unmet, unanswered, or
  invented, and says whether the banner name it read matches the one asked for.
- `week06/CHECKS.md` says where MiniMax and MiMo disagreed and who was right by my own eye.

## Open questions
None. Creature family, models, and seeds were settled in the interview.

## The five creatures
| Name | Habitat | Its own two requirements |
|---|---|---|
| FERNKIT | forest | leaves on its tail; holds an acorn |
| DUNEKIT | desert | sand-colored fur; wears a scarf |
| REEFKIT | ocean | has fins; wears a snorkel mask |
| CITYKIT | city | wears headphones; holds a skateboard |
| SNOWKIT | snow | wears a knitted hat; wears mittens |

Every image also gets the team's four shared requirements: exactly one creature, a plain white
background, the name in a banner at the top, no text other than the name.

**Approved by:** <your name>, <date>
