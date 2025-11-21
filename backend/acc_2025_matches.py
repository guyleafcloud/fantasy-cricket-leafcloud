#!/usr/bin/env python3
"""
ACC 2025 Season Match Data
==========================
All 136 ACC matches from the 2025 season for historical validation.

Source: /Users/guypa/scorecards.md
"""

ALL_2025_MATCHES = [
    # ACC 1 (18 matches)
    {'match_id': 7254567, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7254567/scorecard/?period=2821921'},
    {'match_id': 7254572, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7254572/scorecard/?period=2841578'},
    {'match_id': 7254577, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7254577/scorecard/?period=2854160'},
    {'match_id': 7254582, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7254582/scorecard/?period=2871713'},
    {'match_id': 7254587, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7254587/scorecard/?period=2904089'},
    {'match_id': 7254592, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7254592/scorecard/?period=2933951'},
    {'match_id': 7254597, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7254597/scorecard/?period=2957934'},
    {'match_id': 7254602, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7254602/scorecard/?period=2964940'},
    {'match_id': 7254607, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7254607/scorecard/?period=2998705'},
    {'match_id': 7258314, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7258314/scorecard/?period=3010063'},
    {'match_id': 7258315, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7258315/scorecard/?period=3029908'},
    {'match_id': 7258320, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7258320/scorecard/?period=3064968'},
    {'match_id': 7258325, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7258325/scorecard/?period=3100289'},
    {'match_id': 7258330, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7258330/scorecard/?period=3134531'},
    {'match_id': 7258335, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7258335/scorecard/?period=3165885'},
    {'match_id': 7258340, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7258340/scorecard/?period=3176417'},
    {'match_id': 7258345, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7258345/scorecard/?period=3202331'},
    {'match_id': 7258350, 'team': 'ACC 1', 'url': 'https://matchcentre.kncb.nl/match/134453-7258350/scorecard/?period=3252749'},

    # ACC 2 (14 matches)
    {'match_id': 7323305, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323305/scorecard/?period=2904132'},
    {'match_id': 7323309, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323309/scorecard/?period=2939290'},
    {'match_id': 7323327, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323327/scorecard/?period=2996739'},
    {'match_id': 7323330, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323330/scorecard/?period=3029942'},
    {'match_id': 7323334, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323334/scorecard/?period=3065153'},
    {'match_id': 7323338, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323338/scorecard/?period=3100381'},
    {'match_id': 7323347, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323347/scorecard/?period=3165863'},
    {'match_id': 7323351, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323351/scorecard/?period=3202465'},
    {'match_id': 7323354, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323354/scorecard/?period=3227228'},
    {'match_id': 7323359, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323359/scorecard/?period=3278179'},
    {'match_id': 7323344, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323344/scorecard/?period=3299247'},
    {'match_id': 7323322, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323322/scorecard/?period=3310168'},
    {'match_id': 7323303, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323303/scorecard/?period=3329154'},
    {'match_id': 7323293, 'team': 'ACC 2', 'url': 'https://matchcentre.kncb.nl/match/134453-7323293/scorecard/?period=3348459'},

    # ACC 3 (14 matches)
    {'match_id': 7324739, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324739/scorecard/?period=2852194'},
    {'match_id': 7324742, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324742/scorecard/?period=2883336'},
    {'match_id': 7324747, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324747/scorecard/?period=2916332'},
    {'match_id': 7324749, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324749/scorecard/?period=2946803'},
    {'match_id': 7324755, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324755/scorecard/?period=2976460'},
    {'match_id': 7324760, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324760/scorecard/?period=3012923'},
    {'match_id': 7324763, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324763/scorecard/?period=3041462'},
    {'match_id': 7324766, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324766/scorecard/?period=3075853'},
    {'match_id': 7324770, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324770/scorecard/?period=3112798'},
    {'match_id': 7324777, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324777/scorecard/?period=3176994'},
    {'match_id': 7324784, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324784/scorecard/?period=3203046'},
    {'match_id': 7324787, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324787/scorecard/?period=3254305'},
    {'match_id': 7324791, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324791/scorecard/?period=3278195'},
    {'match_id': 7324776, 'team': 'ACC 3', 'url': 'https://matchcentre.kncb.nl/match/134453-7324776/scorecard/?period=3337237'},

    # ACC 4 (14 matches)
    {'match_id': 7324800, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324800/scorecard/?period=2883551'},
    {'match_id': 7324801, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324801/scorecard/?period=2916490'},
    {'match_id': 7324808, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324808/scorecard/?period=2946765'},
    {'match_id': 7324815, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324815/scorecard/?period=3007435'},
    {'match_id': 7324817, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324817/scorecard/?period=3033129'},
    {'match_id': 7324823, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324823/scorecard/?period=3076197'},
    {'match_id': 7324828, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324828/scorecard/?period=3112385'},
    {'match_id': 7324836, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324836/scorecard/?period=3177632'},
    {'match_id': 7324837, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324837/scorecard/?period=3196391'},
    {'match_id': 7324829, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324829/scorecard/?period=3220141'},
    {'match_id': 7324795, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324795/scorecard/?period=3229749'},
    {'match_id': 7324844, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324844/scorecard/?period=3254928'},
    {'match_id': 7324848, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324848/scorecard/?period=3278019'},
    {'match_id': 7324809, 'team': 'ACC 4', 'url': 'https://matchcentre.kncb.nl/match/134453-7324809/scorecard/?period=3291663'},

    # ACC 5 (13 matches)
    {'match_id': 7326156, 'team': 'ACC 5', 'url': 'https://matchcentre.kncb.nl/match/134453-7326156/scorecard/?period=2841845'},
    {'match_id': 7326162, 'team': 'ACC 5', 'url': 'https://matchcentre.kncb.nl/match/134453-7326162/scorecard/?period=2882990'},
    {'match_id': 7326166, 'team': 'ACC 5', 'url': 'https://matchcentre.kncb.nl/match/134453-7326166/scorecard/?period=2916125'},
    {'match_id': 7326170, 'team': 'ACC 5', 'url': 'https://matchcentre.kncb.nl/match/134453-7326170/scorecard/?period=2947165'},
    {'match_id': 7326173, 'team': 'ACC 5', 'url': 'https://matchcentre.kncb.nl/match/134453-7326173/scorecard/?period=2976000'},
    {'match_id': 7326177, 'team': 'ACC 5', 'url': 'https://matchcentre.kncb.nl/match/134453-7326177/scorecard/?period=3009818'},
    {'match_id': 7326183, 'team': 'ACC 5', 'url': 'https://matchcentre.kncb.nl/match/134453-7326183/scorecard/?period=3041738'},
    {'match_id': 7326186, 'team': 'ACC 5', 'url': 'https://matchcentre.kncb.nl/match/134453-7326186/scorecard/?period=3076097'},
    {'match_id': 7326195, 'team': 'ACC 5', 'url': 'https://matchcentre.kncb.nl/match/134453-7326195/scorecard/?period=3143609'},
    {'match_id': 7326199, 'team': 'ACC 5', 'url': 'https://matchcentre.kncb.nl/match/134453-7326199/scorecard/?period=3176682'},
    {'match_id': 7326203, 'team': 'ACC 5', 'url': 'https://matchcentre.kncb.nl/match/134453-7326203/scorecard/?period=3202881'},
    {'match_id': 7326207, 'team': 'ACC 5', 'url': 'https://matchcentre.kncb.nl/match/134453-7326207/scorecard/?period=3253329'},
    {'match_id': 7326192, 'team': 'ACC 5', 'url': 'https://matchcentre.kncb.nl/match/134453-7326192/scorecard/?period=3349431'},

    # ACC 6 (15 matches)
    {'match_id': 7326066, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326066/scorecard/?period=2850306'},
    {'match_id': 7326073, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326073/scorecard/?period=2883235'},
    {'match_id': 7326075, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326075/scorecard/?period=2916144'},
    {'match_id': 7326082, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326082/scorecard/?period=2946880'},
    {'match_id': 7326086, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326086/scorecard/?period=2977142'},
    {'match_id': 7326093, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326093/scorecard/?period=3006656'},
    {'match_id': 7326097, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326097/scorecard/?period=3040872'},
    {'match_id': 7326102, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326102/scorecard/?period=3076497'},
    {'match_id': 7326120, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326120/scorecard/?period=3177552'},
    {'match_id': 7326121, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326121/scorecard/?period=3202629'},
    {'match_id': 7326130, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326130/scorecard/?period=3254377'},
    {'match_id': 7326132, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326132/scorecard/?period=3278510'},
    {'match_id': 7326139, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326139/scorecard/?period=3299667'},
    {'match_id': 7326143, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326143/scorecard/?period=3318997'},
    {'match_id': 7326148, 'team': 'ACC 6', 'url': 'https://matchcentre.kncb.nl/match/134453-7326148/scorecard/?period=3336151'},

    # ACC ZAMI (18 matches)
    {'match_id': 7332092, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332092/scorecard/?period=2843768'},
    {'match_id': 7332265, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332265/scorecard/?period=2874105'},
    {'match_id': 7332269, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332269/scorecard/?period=2905571'},
    {'match_id': 7332277, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332277/scorecard/?period=3011077'},
    {'match_id': 7332287, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332287/scorecard/?period=3030800'},
    {'match_id': 7332115, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332115/scorecard/?period=3030130'},
    {'match_id': 7332119, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332119/scorecard/?period=3066708'},
    {'match_id': 7332299, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332299/scorecard/?period=3126107'},
    {'match_id': 7332129, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332129/scorecard/?period=3134372'},
    {'match_id': 7332305, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332305/scorecard/?period=3167281'},
    {'match_id': 7332101, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332101/scorecard/?period=3220873'},
    {'match_id': 7332315, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332315/scorecard/?period=3245799'},
    {'match_id': 7332316, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332316/scorecard/?period=3270149'},
    {'match_id': 7332095, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332095/scorecard/?period=3290232'},
    {'match_id': 7332122, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332122/scorecard/?period=3293739'},
    {'match_id': 7332309, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332309/scorecard/?period=3312111'},
    {'match_id': 7332302, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332302/scorecard/?period=3325946'},
    {'match_id': 7332274, 'team': 'ACC ZAMI', 'url': 'https://matchcentre.kncb.nl/match/134453-7332274/scorecard/?period=3344089'},

    # ACC U17 (10 matches)
    {'match_id': 7329152, 'team': 'ACC U17', 'url': 'https://matchcentre.kncb.nl/match/134453-7329152/scorecard/?period=2912677'},
    {'match_id': 7329153, 'team': 'ACC U17', 'url': 'https://matchcentre.kncb.nl/match/134453-7329153/scorecard/?period=2943897'},
    {'match_id': 7329157, 'team': 'ACC U17', 'url': 'https://matchcentre.kncb.nl/match/134453-7329157/scorecard/?period=2972028'},
    {'match_id': 7329168, 'team': 'ACC U17', 'url': 'https://matchcentre.kncb.nl/match/134453-7329168/scorecard/?period=3037165'},
    {'match_id': 7329170, 'team': 'ACC U17', 'url': 'https://matchcentre.kncb.nl/match/134453-7329170/scorecard/?period=3074823'},
    {'match_id': 7329172, 'team': 'ACC U17', 'url': 'https://matchcentre.kncb.nl/match/134453-7329172/scorecard/?period=3111697'},
    {'match_id': 7329159, 'team': 'ACC U17', 'url': 'https://matchcentre.kncb.nl/match/134453-7329159/scorecard/?period=3129887'},
    {'match_id': 7329176, 'team': 'ACC U17', 'url': 'https://matchcentre.kncb.nl/match/134453-7329176/scorecard/?period=3140558'},
    {'match_id': 7329179, 'team': 'ACC U17', 'url': 'https://matchcentre.kncb.nl/match/134453-7329179/scorecard/?period=3161466'},
    {'match_id': 7393900, 'team': 'ACC U17', 'url': 'https://matchcentre.kncb.nl/match/134453-7393900/scorecard/?period=3334719'},

    # ACC U15 (10 matches)
    {'match_id': 7331235, 'team': 'ACC U15', 'url': 'https://matchcentre.kncb.nl/match/134453-7331235/scorecard/?period=2879394'},
    {'match_id': 7331237, 'team': 'ACC U15', 'url': 'https://matchcentre.kncb.nl/match/134453-7331237/scorecard/?period=2912048'},
    {'match_id': 7331240, 'team': 'ACC U15', 'url': 'https://matchcentre.kncb.nl/match/134453-7331240/scorecard/?period=2944264'},
    {'match_id': 7331246, 'team': 'ACC U15', 'url': 'https://matchcentre.kncb.nl/match/134453-7331246/scorecard/?period=3002096'},
    {'match_id': 7331249, 'team': 'ACC U15', 'url': 'https://matchcentre.kncb.nl/match/134453-7331249/scorecard/?period=3037245'},
    {'match_id': 7331253, 'team': 'ACC U15', 'url': 'https://matchcentre.kncb.nl/match/134453-7331253/scorecard/?period=3072449'},
    {'match_id': 7331256, 'team': 'ACC U15', 'url': 'https://matchcentre.kncb.nl/match/134453-7331256/scorecard/?period=3108869'},
    {'match_id': 7331262, 'team': 'ACC U15', 'url': 'https://matchcentre.kncb.nl/match/134453-7331262/scorecard/?period=3173537'},
    {'match_id': 7393853, 'team': 'ACC U15', 'url': 'https://matchcentre.kncb.nl/match/134453-7393853/scorecard/?period=3334732'},
    {'match_id': 7397066, 'team': 'ACC U15', 'url': 'https://matchcentre.kncb.nl/match/134453-7397066/scorecard/?period=3356986'},

    # ACC U13 (10 matches)
    {'match_id': 7336247, 'team': 'ACC U13', 'url': 'https://matchcentre.kncb.nl/match/134453-7336247/scorecard/?period=2880895'},
    {'match_id': 7336254, 'team': 'ACC U13', 'url': 'https://matchcentre.kncb.nl/match/134453-7336254/scorecard/?period=2911963'},
    {'match_id': 7336258, 'team': 'ACC U13', 'url': 'https://matchcentre.kncb.nl/match/134453-7336258/scorecard/?period=2957282'},
    {'match_id': 7336263, 'team': 'ACC U13', 'url': 'https://matchcentre.kncb.nl/match/134453-7336263/scorecard/?period=2971797'},
    {'match_id': 7336272, 'team': 'ACC U13', 'url': 'https://matchcentre.kncb.nl/match/134453-7336272/scorecard/?period=3037077'},
    {'match_id': 7336280, 'team': 'ACC U13', 'url': 'https://matchcentre.kncb.nl/match/134453-7336280/scorecard/?period=3072362'},
    {'match_id': 7336281, 'team': 'ACC U13', 'url': 'https://matchcentre.kncb.nl/match/134453-7336281/scorecard/?period=3108918'},
    {'match_id': 7336290, 'team': 'ACC U13', 'url': 'https://matchcentre.kncb.nl/match/134453-7336290/scorecard/?period=3140511'},
    {'match_id': 7393858, 'team': 'ACC U13', 'url': 'https://matchcentre.kncb.nl/match/134453-7393858/scorecard/?period=3334564'},
    {'match_id': 7395421, 'team': 'ACC U13', 'url': 'https://matchcentre.kncb.nl/match/134453-7395421/scorecard/?period=3346989'},
]

# Summary
MATCH_COUNTS = {
    'ACC 1': 18,
    'ACC 2': 14,
    'ACC 3': 14,
    'ACC 4': 14,
    'ACC 5': 13,
    'ACC 6': 15,
    'ACC ZAMI': 18,
    'ACC U17': 10,
    'ACC U15': 10,
    'ACC U13': 10,
}

TOTAL_MATCHES = 136
