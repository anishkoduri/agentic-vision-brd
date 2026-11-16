# Trace: failure

Loop: Observe, Question, Verify, Revise.

**(a) Clip.** `Event20261107013412003.Avi`, camera `back_cam`, Day 1, minute 94 (01:34), track Cam 03-t1 (clip-local, not a cow ID).

**(b) Observe.** Label `standing`, confidence 0.311. Source: coarse pass: one 640x480 frame every 10 s, YOLO11-small + ByteTrack, geometric label.

**(c) Question.** This minute's confidence (0.311) is under the 0.45 trigger. Is 'standing' the right label for this minute, or was the box too weak to say?

**(d) Verify.** Tool: higher-FPS re-examination window (3 fps, 4 s, tracker re-run on those frames), starting at 0 s, the start of the clip (12 frames), triggered by a box under 0.45 in the coarse pass. Not used: zoom/crop, cross-camera retrieval, a look-back or look-forward outside the 4 s window.

**(e) Revise.** Label `walking`, confidence 0.100 (label changed).

**(f) Learned.** The label changed (standing to walking) but confidence fell to 0.100, still under 0.45. The re-examination did not resolve the ambiguity, so the revised label is unreliable.

Reviewer note (made after the run, not part of the pipeline): a frame at the clip start (`frames/Event20261107013412003/f0001.jpg`) and the last frame of the window (`frames/Event20261107013412003-dense-0/d0012.jpg`) show the same dark shapes in the same places in a night view, so the 'walking' label looks like a tracker artifact.

**VLM.** The VLM (Qwen2.5-VL-3B) was NOT invoked: its weights were not available on this machine. Verification used the tracker's box confidence plus the 3 fps temporal re-examination instead.

**Caveat.** The tracker is reset before each pass (`track_frames` in src/detect.py), so the window's track numbers are issued again; the second read is matched to the first by track number and minute, not by a verified identity. Both rows stay in activity.csv. Nothing here is a diagnosis.
