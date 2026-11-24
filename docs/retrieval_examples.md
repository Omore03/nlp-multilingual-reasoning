# Approved-pool retrieval examples

Recomputed on 25 November from Rayyan's genuine pinned encoder cache, after excluding demos 4 and 5. Scores are cosine similarity rounded to six decimals. Observations below are integration analysis; Rayyan has not separately approved them. These are retrieval examples, not downstream accuracy results.

## gsm8k-train-19b0d3572fbe

James spends 40 years teaching. His partner has been teaching for 10 years less. How long is their combined experience?

جیمز نے 40 سال تدریس کی۔ اس کے ساتھی نے اس سے 10 سال کم تدریس کی۔ دونوں کا مجموعی تدریسی تجربہ کتنے سال ہے؟

| Rank | Demo ID | Cosine | English question |
| --- | --- | --- | --- |
| 1 | `gsm8k-train-cdcae5775716` | 0.535786 | Mr. Sanchez found out that 40% of his Grade 5 students got a final grade below B. How many of his students got a final grade of B and above if he has 60 students in Grade 5? |
| 2 | `gsm8k-train-9d7481516507` | 0.382831 | James is a first-year student at a University in Chicago. He has a budget of $1000 per semester. He spends 30% of his money on food, 15% on accommodation, 25% on entertainment, and the rest on coursework materials. How much money does he spend on coursework materials? |
| 3 | `gsm8k-train-7f5709a21d11` | 0.334385 | Lisa, Jack, and Tommy earned $60 from washing cars all week. However, half of the $60 was earned by Lisa. Tommy earned half of what Lisa earned. How much more money did Lisa earn than Tommy? |
| 4 | `gsm8k-train-3f23a7d4df7c` | 0.279447 | Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes of babysitting. How much did she earn? |
| 5 | `gsm8k-train-f9fe6096f4fc` | 0.270375 | Mr. Sam shared a certain amount of money between his two sons, Ken and Tony. If Ken got $1750, and Tony got twice as much as Ken, how much was the money shared? |

The target needs subtraction followed by addition. Grades and student-budget examples share school or name vocabulary, but their percentage calculations differ. Similarity is not a direct mathematical-structure score.

## gsm8k-train-4e78856e0b87

Peter goes to the store to buy a soda. The soda costs $.25 an ounce. He brought $2 with him and leaves with $.50. How many ounces of soda did he buy?

پیٹر سوڈا خریدنے دکان گیا۔ سوڈے کی قیمت $.25 فی اونس ہے۔ وہ اپنے ساتھ $2 لایا اور اس کے پاس جاتے وقت $.50 بچے۔ اس نے کتنے اونس سوڈا خریدا؟

| Rank | Demo ID | Cosine | English question |
| --- | --- | --- | --- |
| 1 | `gsm8k-train-73bcb06b471e` | 0.663724 | It's Ava's birthday party. Her parents bought a unicorn piñata for $13 and filled it with all of her favorite treats. They bought 4 bags of Reese's for $9 per bag, 3 bags of Snickers for $5 per bag, and 5 bags of Skittles for $7 per bag. How much did the unicorn piñata and the treats cost altogether? |
| 2 | `gsm8k-train-cf2595dad6a3` | 0.632450 | Albert is wondering how much pizza he can eat in one day. He buys 2 large pizzas and 2 small pizzas. A large pizza has 16 slices and a small pizza has 8 slices. If he eats it all, how many pieces does he eat that day? |
| 3 | `gsm8k-train-f9fe6096f4fc` | 0.615502 | Mr. Sam shared a certain amount of money between his two sons, Ken and Tony. If Ken got $1750, and Tony got twice as much as Ken, how much was the money shared? |
| 4 | `gsm8k-train-b384164045eb` | 0.599724 | Dale and Andrew had breakfast at a cafe. A slice of toast costs £1, and eggs cost £3 each. Dale had 2 slices of toast and 2 eggs. Andrew had 1 slice of toast and 2 eggs. How much did their breakfast cost? |
| 5 | `gsm8k-train-ea66ef8b11aa` | 0.555845 | Artemis is making tea for a party. She knows her mom drinks an 8-ounce cup of tea and uses one ounce of tea. She will use this same ratio for the party. The party has 12 people there and each of them wants a 6-ounce cup of tea. How many ounces of tea does she need? |

The target subtracts change from cash and divides by unit price. The leading shopping/food examples multiply quantities and sum totals instead; topic overlap does not imply the same operations.

## gsm8k-train-1d58b8a27f49

Krystian works in the library. He borrows an average of 40 books every day. Every Friday, his number of borrowed books is about 40% higher than the daily average. How many books does he borrow in a week if the library is open from Monday to Friday?

کرسٹیان لائبریری میں کام کرتا ہے۔ وہ روزانہ اوسطاً 40 کتابیں ادھار لیتا ہے۔ ہر جمعے کو ادھار لی گئی کتابوں کی تعداد روزانہ اوسط سے تقریباً 40% زیادہ ہوتی ہے۔ اگر لائبریری پیر سے جمعہ تک کھلی رہتی ہے تو وہ ایک ہفتے میں کتنی کتابیں ادھار لیتا ہے؟

| Rank | Demo ID | Cosine | English question |
| --- | --- | --- | --- |
| 1 | `gsm8k-train-9d7481516507` | 0.465633 | James is a first-year student at a University in Chicago. He has a budget of $1000 per semester. He spends 30% of his money on food, 15% on accommodation, 25% on entertainment, and the rest on coursework materials. How much money does he spend on coursework materials? |
| 2 | `gsm8k-train-3f23a7d4df7c` | 0.376252 | Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes of babysitting. How much did she earn? |
| 3 | `gsm8k-train-73429d562982` | 0.368371 | Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May. How many clips did Natalia sell altogether in April and May? |
| 4 | `gsm8k-train-86ba5b70f686` | 0.335380 | It is Roger’s turn to provide a snack for the baseball team after the game and he has decided to bring trail mix. The trail mix comes in packs of 6 individual pouches. Roger has 13 members on his baseball team, plus 3 coaches and 2 helpers. How many packs of trail mix does he need to buy? |
| 5 | `gsm8k-train-eb06c14679dc` | 0.333471 | A concert ticket costs $40. Mr. Benson bought 12 tickets and received a 5% discount for every ticket bought that exceeds 10. How much did Mr. Benson pay in all? |

The target combines a Friday percentage increase with four ordinary days. The remaining budget and hourly-pay neighbours share percentages or time, but do not demonstrate that complete structure.
