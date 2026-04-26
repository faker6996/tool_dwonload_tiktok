use video_core::{CoreClip, CoreMagneticTrack, CoreTrack};

fn clip(asset_id: &str, name: &str, duration: f64) -> CoreClip {
    let mut clip = CoreClip::new(asset_id.to_string(), name.to_string(), duration);
    clip.id = asset_id.to_string();
    clip
}

#[test]
fn clip_defaults_out_point_to_duration() {
    let clip = CoreClip::new("asset.mp4".to_string(), "asset".to_string(), 12.5);

    assert_eq!(clip.in_point, 0.0);
    assert_eq!(clip.out_point, 12.5);
    assert_eq!(clip.length(), 12.5);
}

#[test]
fn clip_length_never_negative() {
    let mut clip = CoreClip::new("asset.mp4".to_string(), "asset".to_string(), 10.0);
    clip.in_point = 8.0;
    clip.out_point = 3.0;

    assert_eq!(clip.length(), 0.0);
}

#[test]
fn base_track_appends_and_sorts_clips() {
    let mut track = CoreTrack::new("Track".to_string(), false);
    assert!(track.add_clip(clip("c2", "Clip 2", 3.0), Some(5.0)));
    assert!(track.add_clip(clip("c1", "Clip 1", 5.0), Some(0.0)));

    assert_eq!(track.clips[0].id, "c1");
    assert_eq!(track.clips[1].id, "c2");
}

#[test]
fn magnetic_append_matches_python_behavior() {
    let mut track = CoreMagneticTrack::new("Test Track".to_string());
    assert!(track.add_clip(clip("c1", "Clip 1", 5.0), None));
    assert!(track.add_clip(clip("c2", "Clip 2", 3.0), None));

    assert_eq!(track.track.clips.len(), 2);
    assert_eq!(track.track.clips[0].start_time, 0.0);
    assert_eq!(track.track.clips[1].start_time, 5.0);
    assert!(track.validate_no_overlaps());
}

#[test]
fn magnetic_remove_ripples_subsequent_clips() {
    let mut track = CoreMagneticTrack::new("Test Track".to_string());
    track.add_clip(clip("c1", "Clip 1", 5.0), None);
    track.add_clip(clip("c2", "Clip 2", 3.0), None);

    let removed = track.remove_clip("c1");

    assert_eq!(removed.as_ref().map(|clip| clip.id.as_str()), Some("c1"));
    assert_eq!(track.track.clips.len(), 1);
    assert_eq!(track.track.clips[0].id, "c2");
    assert_eq!(track.track.clips[0].start_time, 0.0);
}

#[test]
fn magnetic_insert_snaps_to_previous_clip_end_and_ripples() {
    let mut track = CoreMagneticTrack::new("Test Track".to_string());
    track.add_clip(clip("c1", "Clip 1", 5.0), None);
    track.add_clip(clip("c3", "Clip 3", 4.0), None);

    assert!(track.add_clip(clip("c2", "Clip 2", 3.0), Some(2.0)));

    assert_eq!(track.track.clips[0].id, "c1");
    assert_eq!(track.track.clips[1].id, "c2");
    assert_eq!(track.track.clips[2].id, "c3");
    assert_eq!(track.track.clips[1].start_time, 5.0);
    assert_eq!(track.track.clips[2].start_time, 8.0);
    assert!(track.validate_no_overlaps());
}

#[test]
fn magnetic_split_clip_matches_python_behavior() {
    let mut track = CoreMagneticTrack::new("Test Track".to_string());
    track.add_clip(clip("c1", "Clip 1", 10.0), None);

    let right = track.split_clip("c1", 4.0);

    assert!(right.is_some());
    assert_eq!(track.track.clips.len(), 2);
    assert_eq!(track.track.clips[0].start_time, 0.0);
    assert_eq!(track.track.clips[0].in_point, 0.0);
    assert_eq!(track.track.clips[0].out_point, 4.0);
    assert_eq!(track.track.clips[1].start_time, 4.0);
    assert_eq!(track.track.clips[1].in_point, 4.0);
    assert_eq!(track.track.clips[1].out_point, 10.0);
    assert_ne!(track.track.clips[0].id, track.track.clips[1].id);
}

#[test]
fn magnetic_trim_shrink_ripples_subsequent_clips() {
    let mut track = CoreMagneticTrack::new("Test Track".to_string());
    track.add_clip(clip("c1", "Clip 1", 5.0), None);
    track.add_clip(clip("c2", "Clip 2", 3.0), None);

    assert!(track.trim_clip("c1", None, Some(3.0)));

    assert_eq!(track.track.clips[0].length(), 3.0);
    assert_eq!(track.track.clips[1].start_time, 3.0);
    assert!(track.validate_no_overlaps());
}

#[test]
fn magnetic_trim_expand_ripples_subsequent_clips() {
    let mut track = CoreMagneticTrack::new("Test Track".to_string());
    let mut first = clip("c1", "Clip 1", 5.0);
    first.in_point = 1.0;
    track.add_clip(first, None);
    track.add_clip(clip("c2", "Clip 2", 3.0), None);
    assert_eq!(track.track.clips[1].start_time, 4.0);

    assert!(track.trim_clip("c1", Some(0.0), None));

    assert_eq!(track.track.clips[0].length(), 5.0);
    assert_eq!(track.track.clips[1].start_time, 5.0);
    assert!(track.validate_no_overlaps());
}

#[test]
fn magnetic_split_or_trim_rejects_invalid_ranges() {
    let mut track = CoreMagneticTrack::new("Test Track".to_string());
    track.add_clip(clip("c1", "Clip 1", 5.0), None);

    assert!(track.split_clip("c1", 0.0).is_none());
    assert!(track.split_clip("c1", 5.0).is_none());
    assert!(!track.trim_clip("c1", Some(4.0), Some(2.0)));
}

#[test]
fn locked_magnetic_track_rejects_mutations() {
    let mut track = CoreMagneticTrack::new("Test Track".to_string());
    track.track.is_locked = true;

    assert!(!track.add_clip(clip("c1", "Clip 1", 5.0), None));
    assert!(track.remove_clip("c1").is_none());
    assert!(track.split_clip("c1", 1.0).is_none());
    assert!(!track.trim_clip("c1", None, Some(3.0)));
}
