# -*- coding: utf-8 -*-
"""Asset manifest: every image the app needs, with its generation prompt.
Shared style strings guarantee visual consistency across all images."""

STYLE_CHAR = ("Art style (must follow exactly): cute chibi cartoon character, flat colors with soft cel shading, "
              "thick clean dark-brown outlines, big sparkling eyes, friendly smile, sticker style, children's "
              "picture-book aesthetic, full body, standing, facing viewer, centered with about 5% margin, "
              "fully TRANSPARENT background, PNG 1024x1024, no text, no watermark, single character only.")

STYLE_ITEM = ("Art style (must follow exactly): cute cartoon sticker of a single object, flat colors with soft cel "
              "shading, thick clean dark-brown outline, glossy highlight, children's picture-book aesthetic, "
              "big and centered, fully TRANSPARENT background, PNG 1024x1024, no text, no watermark, single object only.")

STYLE_ISLAND = ("Art style (must follow exactly): cute cartoon floating island seen from the front with a slight top angle, "
                "flat colors with soft cel shading, thick clean outlines, fluffy round grass top, small rounded rocks "
                "hanging under the island bottom, children's picture-book aesthetic, centered, fully TRANSPARENT "
                "background, PNG 1024x1024, no text, no watermark.")

STYLE_BG = ("Art style (must follow exactly): soft dreamy children's picture-book background scene, flat pastel colors, "
            "gentle gradients, soft cel shading, rounded friendly shapes, decorative elements only near the left and "
            "right edges and far distance, large calm uncluttered empty area in the center and lower-middle for gameplay, "
            "NO characters, NO animals, NO text, NO watermark, landscape 1536x1024.")

CHARS = [
    # 西游记
    ("wukong",    "Sun Wukong the Monkey King as an adorable child-friendly cartoon monkey hero — golden-yellow fur, warm red and gold traditional Chinese outfit, thin golden circlet band on head, holding a small golden staff, waving one hand cheerfully"),
    ("bajie",     "Zhu Bajie the pig from Journey to the West as an adorable chubby cartoon pig-man — soft pink skin, big floppy pig ears and round snout, blue-black sleeveless monk vest with an orange sash over a round belly, holding a tiny nine-tooth golden rake, jolly laughing expression"),
    ("wujing",    "Sha Wujing (Sandy) from Journey to the West as a friendly gentle cartoon monk — light blue-teal skin, short dark hair and short tidy beard, brown-and-teal monk robe, big brown prayer-bead necklace, holding a small monk's spade staff, warm gentle smile"),
    ("tangseng",  "Tang Sanzang the young monk from Journey to the West as a kind cartoon monk — fair skin, gentle smile, red-and-gold kasaya robe over an orange robe, ornate golden monk's crown hat, hands together in a friendly greeting"),
    ("bailongma", "the White Dragon Horse from Journey to the West as an adorable cartoon white pony — snow-white body, flowing pale-silver mane and tail, two tiny pale-blue dragon horns, red saddle with golden tassels, standing proudly with a happy smile"),
    # 葫芦娃
    ("hulu1", "one of the Calabash Brothers (Huluwa) as an adorable cartoon toddler hero — crimson RED calabash-gourd hat on head, matching red leaf-collar top and leaf skirt, chubby cheerful toddler body, fists raised in a cute hero pose"),
    ("hulu2", "one of the Calabash Brothers (Huluwa) as an adorable cartoon toddler hero — bright ORANGE calabash-gourd hat on head, matching orange leaf-collar top and leaf skirt, chubby cheerful toddler body, one arm flexing in a cute strong pose"),
    ("hulu3", "one of the Calabash Brothers (Huluwa) as an adorable cartoon toddler hero — sunny YELLOW calabash-gourd hat on head, matching yellow leaf-collar top and leaf skirt, chubby cheerful toddler body, waving happily"),
    ("hulu4", "one of the Calabash Brothers (Huluwa) as an adorable cartoon toddler hero — leaf GREEN calabash-gourd hat on head, matching green leaf-collar top and leaf skirt, chubby cheerful toddler body, jumping with joy"),
    ("hulu5", "one of the Calabash Brothers (Huluwa) as an adorable cartoon toddler hero — CYAN teal calabash-gourd hat on head, matching cyan leaf-collar top and leaf skirt, chubby cheerful toddler body, giggling with hands on cheeks"),
    ("hulu6", "one of the Calabash Brothers (Huluwa) as an adorable cartoon toddler hero — deep BLUE calabash-gourd hat on head, matching blue leaf-collar top and leaf skirt, chubby cheerful toddler body, arms wide open for a hug"),
    ("hulu7", "one of the Calabash Brothers (Huluwa) as an adorable cartoon toddler hero — PURPLE calabash-gourd hat on head, matching purple leaf-collar top and leaf skirt, chubby cheerful toddler body, clapping hands happily"),
    ("yeye",  "the kind old Grandpa from Calabash Brothers as a cartoon elder — long white beard and bushy white eyebrows, bald shiny head, simple brown peasant vest and grey trousers, holding a wooden walking stick, warm loving smile"),
    ("shejing",   "the Snake Spirit from Calabash Brothers as a playful NON-scary cartoon fairy lady — pale mint-green skin, elegant black updo hair with a tiny golden crown, flowing light-green dress that ends in a cute coiled snake tail instead of feet, friendly mischievous wink"),
    ("xiezijing", "the Scorpion Spirit from Calabash Brothers as a silly NON-scary cartoon fellow — purple-and-black outfit, two tiny rounded scorpion pincers, a small curled tail with a harmless rounded ball tip, goofy friendly grin"),
    # 复仇者联盟
    ("ironman",   "Iron Man as an adorable chibi cartoon hero — shiny red and gold armor suit, glowing round white light on chest, full helmet with friendly glowing white eyes, one fist raised in a cheerful hero pose"),
    ("cap",       "Captain America as an adorable chibi cartoon hero — blue suit with a white star on the chest, red-and-white striped belly band, blue mask, holding a small round red-white-blue shield, big friendly smile"),
    ("thor",      "Thor as an adorable chibi cartoon hero — long golden-blonde hair, silver-and-black armor with round silver discs on the chest, flowing red cape, holding a small grey stone hammer, hearty friendly laugh"),
    ("hulk",      "Hulk as an adorable chibi cartoon hero — big friendly green muscly body, messy dark-green hair, purple shorts, huge happy grin, flexing both arms in a playful pose"),
    ("blackwidow","Black Widow as an adorable chibi cartoon heroine — shoulder-length wavy red hair, black tactical suit with a small golden hourglass belt buckle, hands on hips, confident friendly smile"),
    ("hawkeye",   "Hawkeye as an adorable chibi cartoon hero — short brown hair, purple-and-black archer outfit, holding a small bow, quiver of round-tipped arrows on his back, friendly wink"),
    ("spiderman", "Spider-Man as an adorable chibi cartoon hero — bright red and blue suit with thin black web pattern, big friendly white teardrop eyes on the red mask, one hand waving hello"),
    ("miles",     "Miles Morales Spider-hero as an adorable chibi cartoon hero — sleek black suit with bold red spider emblem and red web accents, big friendly white eyes, energetic jumping pose"),
    ("gwen",      "Ghost-Spider (Spider-Gwen) as an adorable chibi cartoon heroine — white hooded suit with black torso, pink and cyan accents inside the hood, hood up, big white teardrop eyes, ballet-like pose"),
    # 汪汪队
    ("ryder",    "Ryder the boy leader from PAW Patrol as an adorable cartoon boy — spiky brown hair, red-white-and-blue rescue vest, dark blue trousers, giving a cheerful thumbs up"),
    ("chase",    "Chase from PAW Patrol as an adorable cartoon German-shepherd puppy — brown and tan fur, blue police uniform and blue police cap, blue pup-pack on his back, sitting proudly with a big smile"),
    ("marshall", "Marshall from PAW Patrol as an adorable cartoon dalmatian puppy — white fur with black spots, red firefighter outfit and red fire helmet, red pup-pack, cheerful goofy smile with tongue out"),
    ("skye",     "Skye from PAW Patrol as an adorable cartoon cockapoo puppy girl — light pink-brown fur, pink pilot outfit with pink flight goggles resting on her head, small pink wing pack, joyful smile"),
    ("rocky",    "Rocky from PAW Patrol as an adorable cartoon grey mixed-breed puppy — grey and white fur, green recycling outfit and green cap, green pup-pack, clever happy smile"),
    ("zuma",     "Zuma from PAW Patrol as an adorable cartoon chocolate-brown labrador puppy — brown fur, orange water-rescue outfit and orange helmet, orange pup-pack, relaxed happy smile"),
    ("rubble",   "Rubble from PAW Patrol as an adorable cartoon english-bulldog puppy — tan and white fur, yellow construction outfit and yellow hard hat, yellow pup-pack, hearty giggling smile"),
    # Bluey
    ("bluey",  "Bluey the blue heeler puppy kid from the cartoon Bluey — light blue body with dark blue patches, tan face and belly, perky ears, standing upright like a playful kid with arms open wide, joyful grin"),
    ("bingo",  "Bingo the red heeler puppy kid from the cartoon Bluey — cream body with warm orange-tan patches, floppy-tipped ears, standing upright like a sweet little kid with hands together, gentle happy smile"),
    ("bandit", "Bandit the dad blue heeler dog from the cartoon Bluey — tall dark-blue and light-blue patched fur, tan paws and muzzle, standing upright like a playful dad, arms crossed with a warm grin"),
    ("chilli", "Chilli the mum red heeler dog from the cartoon Bluey — cream and warm orange-tan patched fur, standing upright like a kind mum, one hand on hip, loving smile"),
    # 小猪佩奇
    ("peppa",  "Peppa Pig as an adorable cartoon piggy girl — pink head with round cheeks and a cute snout, wearing a red dress, little black shoes, tiny curly tail, sweet giggling expression"),
    ("george", "George Pig, Peppa's little brother, as an adorable cartoon piggy boy — pink head with cute snout, wearing a dark blue romper, holding a tiny green toy dinosaur, happy toddler smile"),
    ("papa",   "Daddy Pig as an adorable cartoon big piggy dad — pink head with cute snout, round glasses, wearing a teal-green shirt and dark trousers, jolly laughing expression"),
    ("mama",   "Mummy Pig as an adorable cartoon piggy mum — pink head with cute snout, long pretty eyelashes, wearing an orange dress, warm gentle smile"),
]

ITEMS = [
    ("peach",  "a cute cartoon peach — soft pink-to-red gradient, one small green leaf on top, glossy highlight"),
    ("baozi",  "a cute cartoon Chinese steamed bun (baozi) — soft fluffy white bun with neat spiral pleats on top, faint warm glow, tiny happy steam puffs"),
    ("hulu",   "a cute cartoon golden calabash gourd — glossy golden-orange double-bulb gourd shape with a small green vine curl on top"),
    ("star",   "a cute cartoon glowing golden five-pointed star — chunky rounded points, warm yellow-gold gradient, soft outer glow"),
    ("bone",   "a cute cartoon dog-bone biscuit treat — warm beige biscuit color, classic rounded bone shape, tiny sparkle highlight"),
    ("ball",   "a cute cartoon tennis ball — bright yellow-green, white curved seam lines, glossy highlight"),
    ("cookie", "a cute cartoon round chocolate-chip cookie — golden-brown, scattered dark chocolate chips, soft glossy highlight"),
    ("apple",  "a cute cartoon red apple — bright glossy red, small brown stem, one green leaf"),
    ("basket", "a cute cartoon woven bamboo basket — warm golden-tan, wide open oval top, empty inside, sturdy arched handle"),
    ("web",    "a cute cartoon circular orb spider web — soft silver-grey silk lines with gentle glow, symmetrical spokes and rings"),
    ("puddle", "a cute cartoon muddy brown puddle — top-down slight angle, oval splashy shape, small mud droplets around the edge"),
    ("tree",   "a big cute cartoon peach tree — lush round fluffy green canopy with tiny pink blossoms, sturdy brown trunk, no fruit"),
    ("bowl",   "a cute cartoon glossy red dog food bowl — front slight angle, empty, plain"),
]

ISLANDS = [
    ("isl_xiyou",    "the floating island carries a pink-blossom mountain with tiny peach trees full of pink fruit and a tiny white waterfall"),
    ("isl_hulu",     "the floating island carries a green vine-covered hill with giant colorful calabash gourds (red orange yellow green blue purple) growing on curly vines"),
    ("isl_avengers", "the floating island carries a tiny bright futuristic toy city — small rounded friendly towers with glowing blue window dots and one glowing blue circle beacon on the tallest tower"),
    ("isl_paw",      "the floating island carries a small seaside hill with a tall cartoon lookout tower topped by a colorful dome and a tiny slide, a tiny sandy beach edge"),
    ("isl_bluey",    "the floating island carries a cosy cream-and-brown family house with a terracotta roof and a big leafy purple-flowering tree beside it"),
    ("isl_peppa",    "the floating island carries a little yellow house with a red roof on top of a smooth green hill, tiny flowers and one small blue puddle at the hill base"),
]

BGS = [
    ("bg_sky",      "a dreamy bright open sky — soft fluffy white clouds of different sizes floating around, gentle pastel blue fading to warm cream near the bottom, one faint distant small rainbow arc near a lower corner"),
    ("bg_xiyou",    "a soft pastel mountain valley — pink blossom trees and pale peach-colored rocky peaks only at the far left and right edges, gentle light-green meadow floor, warm blue sky"),
    ("bg_hulu",     "a soft pastel magical green valley — giant curly gourd vines with leaves climbing only the far left and right edges, misty pale-green mountains far away, gentle grass floor"),
    ("bg_avengers", "a soft pastel friendly futuristic city plaza — rounded pastel skyscrapers with tiny glowing windows far in the background and at the edges, smooth light blue-grey plaza floor"),
    ("bg_paw",      "a soft pastel sunny seaside bay — calm light-blue sea meeting a warm sandy beach floor, a distant tiny lookout tower silhouette at the far right edge, a few seagull-free fluffy clouds"),
    ("bg_bluey",    "a soft pastel sunny backyard — warm green grass floor, a light wooden fence and one big leafy tree only at the edges, golden afternoon light"),
    ("bg_peppa",    "soft pastel rolling green hills — one tiny yellow house with red roof on a far-left hill, one or two puffy clouds, smooth bright green grass floor in front"),
]

def build():
    out = []
    for cid, desc in CHARS:
        out.append({"file": f"assets/char/{cid}.png", "prompt": f"{desc}. {STYLE_CHAR}", "transparent": True})
    for iid, desc in ITEMS:
        out.append({"file": f"assets/item/{iid}.png", "prompt": f"{desc}. {STYLE_ITEM}", "transparent": True})
    for iid, desc in ISLANDS:
        out.append({"file": f"assets/bg/{iid}.png", "prompt": f"{desc}. {STYLE_ISLAND}", "transparent": True})
    for bid, desc in BGS:
        out.append({"file": f"assets/bg/{bid}.png", "prompt": f"{desc}. {STYLE_BG}", "transparent": False, "size": "1536x1024"})
    return out

if __name__ == "__main__":
    import json
    m = build()
    print(json.dumps([a["file"] for a in m], indent=1))
    print(len(m), "assets")
