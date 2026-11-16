# Trace: night

Loop: Observe, Question, Verify, Revise.

**(a) Clip.** `Event20261107043924003.Avi`, camera `back_cam`, Day 1, minute 279 (04:39), track Cam 03-t2 (clip-local, not a cow ID).

**(b) Observe.** Label `lying`, confidence 0.395. Source: coarse pass: one 640x480 frame every 10 s, YOLO11-small + ByteTrack, geometric label.

**(c) Question.** This minute's confidence (0.395) is under the 0.45 trigger. Is 'lying' the right label for this minute, or was the box too weak to say?

**(d) Verify.** Tool: higher-FPS re-examination window (3 fps, 4 s, tracker re-run on those frames), starting at 0 s, the start of the clip (12 frames), triggered by a box under 0.45 in the coarse pass. Not used: zoom/crop, cross-camera retrieval, a look-back or look-forward outside the 4 s window.

**(e) Revise.** Label `standing`, confidence 0.828 (label changed).

**(f) Learned.** The label changed (lying to standing) and confidence rose to 0.828. The second read is better supported, but it is a new tracker pass matched by track number only, and at night the view is infrared with low contrast.

**VLM.** The VLM (Qwen2.5-VL-3B) was NOT invoked: its weights were not available on this machine. Verification used the tracker's box confidence plus the 3 fps temporal re-examination instead.

**Caveat.** The tracker is reset before each pass (`track_frames` in src/detect.py), so the window's track numbers are issued again; the second read is matched to the first by track number and minute, not by a verified identity. Only the second-look row stays in activity.csv (the coarse row was dropped by dedup). Nothing here is a diagnosis.
