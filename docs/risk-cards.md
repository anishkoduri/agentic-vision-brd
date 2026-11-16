# Anomaly tracklet evidence

These are the most anomalous tracklets observed: for each camera, the three tracklets whose behavior deviates most from the herd mean for that camera and day (method in `docs/anomaly-report.md`). They are clip-level evidence only. A tracklet is one tracker number inside one clip; the same number in another clip is a different tracking event, not the same animal. They do not identify individual cows, they are not linked across clips or days, and no ordering of individual cows is claimed. A deviation is not a diagnosis, and some, all, or none of the cattle may have BRD.

Tracklets in the batch: 9,750. Compared with the herd: 1,805 (at least 4 tracked minutes and mean confidence 0.5 or higher). Individual cows singled out: 0.

## Card 1 — back_cam

What this card shows: walking at night and midday on the back camera. A cow that keeps moving through the pen when the herd is resting is restless, and restlessness is a recognized sign of discomfort or fever. Walking here is a moving box, so a tracker shift can also cause it; open the clip before reading anything into it. Nothing on this card is a diagnosis.

### Event20261108033052003.Avi

- Clip: `Event20261108033052003.Avi`
- Camera, day, minute: back_cam, Day 2, 03:31 (first minute of the behavior)
- Track number: 1 (clip-local, not a cow ID)
- Observed behavior: walking in 2 of 4 tracked minutes (50%)
- Versus herd: the back_cam Day 2 herd mean is 0.6% of minutes (0.02 min for a 4-minute tracklet); deviation z = +11.0
- Why a veterinarian cares: walking at 03:31, when about 63% of Day 2 track-minutes at that hour were lying, would be restlessness while the herd rests. A restless animal can be uncomfortable or febrile, but one clip does not show that.

### Event20261108142134003.Avi

- Clip: `Event20261108142134003.Avi`
- Camera, day, minute: back_cam, Day 2, 14:23 (first minute of the behavior)
- Track number: 10 (clip-local, not a cow ID)
- Observed behavior: walking in 2 of 4 tracked minutes (50%)
- Versus herd: the back_cam Day 2 herd mean is 0.6% of minutes (0.02 min for a 4-minute tracklet); deviation z = +11.0
- Why a veterinarian cares: walking in 2 of 4 minutes at midday is movement instead of rest or feeding. Restlessness is a recognized sign of discomfort, but it is not specific to BRD.

### Event20261108043056003.Avi

- Clip: `Event20261108043056003.Avi`
- Camera, day, minute: back_cam, Day 2, 04:33 (first minute of the behavior)
- Track number: 1 (clip-local, not a cow ID)
- Observed behavior: walking in 2 of 4 tracked minutes (50%)
- Versus herd: the back_cam Day 2 herd mean is 0.6% of minutes (0.02 min for a 4-minute tracklet); deviation z = +11.0
- Why a veterinarian cares: walking at 04:33 is again movement in the pre-dawn hours when most of the herd lies down (about 61% of Day 2 track-minutes at 04 h). It is worth watching the clip for an animal that will not settle.

## Card 2 — front_cam_1

What this card shows: walking on the bunk-side camera. Reduced feed intake is an early BRD sign, so a veterinarian looks for animals that move along the bunk without settling to eat or rest. Walking here means the animal was neither labeled feeding nor lying in those minutes; it can also be normal herd movement. Nothing on this card is a diagnosis.

### Event20261107090952006.Avi

- Clip: `Event20261107090952006.Avi`
- Camera, day, minute: front_cam_1, Day 1, 09:11 (first minute of the behavior)
- Track number: 20 (clip-local, not a cow ID)
- Observed behavior: walking in 3 of 4 tracked minutes (75%)
- Versus herd: the front_cam_1 Day 1 herd mean is 2.5% of minutes (0.10 min for a 4-minute tracklet); deviation z = +8.0
- Why a veterinarian cares: walking in 3 of 4 minutes at 09:11 means the animal kept moving instead of settling at the bunk or lying down. Less time settled at the feed is the intake change to look for, and restlessness is a recognized discomfort sign; herd movement or a tracker shift can look the same.

### Event20261108162543006.Avi

- Clip: `Event20261108162543006.Avi`
- Camera, day, minute: front_cam_1, Day 2, 16:26 (first minute of the behavior)
- Track number: 5 (clip-local, not a cow ID)
- Observed behavior: walking in 2 of 4 tracked minutes (50%)
- Versus herd: the front_cam_1 Day 2 herd mean is 1.7% of minutes (0.07 min for a 4-minute tracklet); deviation z = +6.2
- Why a veterinarian cares: moving in 2 of 4 minutes at 16:26 instead of feeding or resting; a possible restlessness sign, and only worth a look if the clip shows the animal avoiding the bunk.

### Event20261108101130006.Avi

- Clip: `Event20261108101130006.Avi`
- Camera, day, minute: front_cam_1, Day 2, 10:13 (first minute of the behavior)
- Track number: 10 (clip-local, not a cow ID)
- Observed behavior: walking in 2 of 4 tracked minutes (50%)
- Versus herd: the front_cam_1 Day 2 herd mean is 1.7% of minutes (0.07 min for a 4-minute tracklet); deviation z = +6.2
- Why a veterinarian cares: moving in 2 of 4 minutes at 10:13 instead of feeding or resting; a possible restlessness sign, and only worth a look if the clip shows the animal avoiding the bunk.

## Card 3 — front_cam_2

What this card shows: one feeding clip and two lying clips, which read differently. Eating well is the opposite of the early BRD sign (reduced feed intake), so the feeding clip is a healthy-looking comparison, not a risk. Lying all four minutes in daylight, when the herd would be eating, is the increased lying a veterinarian pairs with eating less; lying through the night is normal rest. Nothing on this card is a diagnosis.

### Event20261107135022017.Avi

- Clip: `Event20261107135022017.Avi`
- Camera, day, minute: front_cam_2, Day 1, 13:50 (first minute of the behavior)
- Track number: 2 (clip-local, not a cow ID)
- Observed behavior: feeding in 3 of 4 tracked minutes (75%)
- Versus herd: the front_cam_2 Day 1 herd mean is 1.5% of minutes (0.06 min for a 4-minute tracklet); deviation z = +8.2
- Why a veterinarian cares: feeding in 3 of 4 minutes is normal appetite for that moment, the opposite of reduced intake. It is listed because it deviates from the camera’s herd mean (1.5%), not because it signals risk. It is a useful comparison for the Day 2 midday feeding drop (13 h: 26.6% on Day 1 to 0.7% on Day 2).

### Event20261107021436017.Avi

- Clip: `Event20261107021436017.Avi`
- Camera, day, minute: front_cam_2, Day 1, 02:14 (first minute of the behavior)
- Track number: 1 (clip-local, not a cow ID)
- Observed behavior: lying in 4 of 4 tracked minutes (100%)
- Versus herd: the front_cam_2 Day 1 herd mean is 11.4% of minutes (0.45 min for a 4-minute tracklet); deviation z = +3.5
- Why a veterinarian cares: lying all four minutes at 02:14 is normal overnight rest. It is listed only because this camera’s Day 1 herd mean for lying is low (11.4%); on its own it does not suggest illness.

### Event20261107140522017.Avi

- Clip: `Event20261107140522017.Avi`
- Camera, day, minute: front_cam_2, Day 1, 14:05 (first minute of the behavior)
- Track number: 9 (clip-local, not a cow ID)
- Observed behavior: lying in 4 of 4 tracked minutes (100%)
- Versus herd: the front_cam_2 Day 1 herd mean is 11.4% of minutes (0.45 min for a 4-minute tracklet); deviation z = +3.5
- Why a veterinarian cares: lying for every tracked minute at 14:05, in daylight when Day 1 feeding was 10.9% of track-minutes, is increased lying with no feeding in this clip. Increased lying together with reduced feed intake is what a veterinarian looks at first, but one clip does not show the animal was ill; it may simply have been resting.

