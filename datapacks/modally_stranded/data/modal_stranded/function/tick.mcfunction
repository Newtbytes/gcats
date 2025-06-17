execute as @e[type=area_effect_cloud, tag=creative_zone] at @s \
run gamemode creative @a[distance=0..100,   gamemode=!creative]

execute as @e[type=area_effect_cloud, tag=creative_zone] at @s \
run gamemode survival @a[distance=100..110, gamemode=!survival]
