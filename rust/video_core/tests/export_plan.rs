use std::fs::File;

use serde_json::json;
use video_core::build_export_plan;
use video_core::build_export_plan_with_overlays;

#[test]
fn export_plan_orders_clips_and_normalizes_trim_points() {
    let temp_dir = tempfile::tempdir().expect("temp dir");
    let clip_a = temp_dir.path().join("a.mp4");
    let clip_b = temp_dir.path().join("b.mp4");
    File::create(&clip_a).expect("clip a");
    File::create(&clip_b).expect("clip b");

    let clips = vec![
        json!({
            "path": clip_b,
            "start": 10.0,
            "in_point": 1.0,
            "duration": 2.0
        }),
        json!({
            "path": clip_a,
            "start": 0.0,
            "in_point": 0.25,
            "out_point": 4.0,
            "duration": 3.5
        }),
    ];

    let plan = build_export_plan(
        &clips,
        &json!({"resolution": "original", "fps": "original", "speed": 2.0}),
    )
    .expect("plan");

    assert_eq!(plan.clips.len(), 2);
    assert!(plan.clips[0].path.ends_with("a.mp4"));
    assert!(plan.clips[1].path.ends_with("b.mp4"));
    assert_eq!(plan.clips[0].in_point, 0.25);
    assert_eq!(plan.clips[0].out_point, Some(4.0));
    assert_eq!(plan.clips[1].in_point, 1.0);
    assert_eq!(plan.clips[1].out_point, Some(3.0));
    assert_eq!(plan.settings.resolution, "original");
    assert_eq!(plan.settings.fps, json!("original"));
    assert_eq!(plan.settings.speed, 2.0);
    assert_eq!(plan.settings.gap_policy, "omit");
    assert_eq!(plan.total_duration, 2.875);
    assert_eq!(plan.gaps.len(), 1);
    assert_eq!(plan.gaps[0].policy, "omit");
    assert_eq!(plan.gaps[0].start, 3.75);
    assert_eq!(plan.gaps[0].duration, 6.25);
    assert!(plan
        .warnings
        .iter()
        .any(|warning| warning.contains("Timeline gap omitted")));
}

#[test]
fn export_plan_rejects_timeline_gap_when_requested() {
    let temp_dir = tempfile::tempdir().expect("temp dir");
    let clip_a = temp_dir.path().join("a.mp4");
    let clip_b = temp_dir.path().join("b.mp4");
    File::create(&clip_a).expect("clip a");
    File::create(&clip_b).expect("clip b");
    let clips = vec![
        json!({"path": clip_a, "start": 0.0, "duration": 1.0}),
        json!({"path": clip_b, "start": 3.0, "duration": 1.0}),
    ];

    let error = build_export_plan(&clips, &json!({"gap_policy": "reject"})).expect_err("gap");

    assert!(error.contains("Timeline gap rejected"));
}

#[test]
fn export_plan_reports_missing_and_invalid_clips() {
    let clips = vec![
        json!({"path": "", "start": 0.0, "duration": 1.0}),
        json!({"path": "/definitely/missing.mp4", "start": 1.0, "duration": 1.0}),
    ];

    let error = build_export_plan(&clips, &json!({})).expect_err("no valid clips");

    assert_eq!(error, "No valid clip files to render.");
}

#[test]
fn export_plan_normalizes_audio_subtitles_stickers_and_filters() {
    let temp_dir = tempfile::tempdir().expect("temp dir");
    let clip_path = temp_dir.path().join("clip.mp4");
    let audio_path = temp_dir.path().join("voice.mp3");
    File::create(&clip_path).expect("clip");
    File::create(&audio_path).expect("audio");

    let clips = vec![json!({"path": clip_path, "start": 0.0, "duration": 5.0})];
    let stickers = vec![json!({"content": "🔥", "x": 12.0, "y": -4.0, "scale": -1.0})];
    let subtitles = vec![
        json!({"start_time": 1.0, "duration": 2.0, "text_content": "Hello"}),
        json!({"start_time": 2.0, "duration": 2.0, "text_content": ""}),
    ];
    let audio_tracks = vec![
        json!({"path": audio_path, "start_time": 0.5, "duration": 3.0}),
        json!({"path": "/missing/voice.mp3", "start_time": 0.0, "duration": 1.0}),
    ];

    let plan = build_export_plan_with_overlays(
        &clips,
        &json!({"speed": 1.5}),
        &stickers,
        &subtitles,
        &audio_tracks,
    )
    .expect("plan");

    assert_eq!(plan.stickers.len(), 1);
    assert_eq!(plan.stickers[0].scale, 0.01);
    assert_eq!(plan.subtitles.len(), 1);
    assert_eq!(plan.audio_tracks.len(), 1);
    assert!(plan.filters.needs_filter_complex);
    assert!(plan.filters.has_video_speed_filter);
    assert!(plan.filters.has_audio_speed_filter);
    assert!(plan.filters.has_subtitles);
    assert_eq!(plan.filters.sticker_count, 1);
    assert_eq!(plan.filters.audio_track_count, 1);
    assert!(plan
        .filter_steps
        .iter()
        .any(|step| step.target == "video" && step.kind == "subtitles"));
    assert!(plan
        .filter_steps
        .iter()
        .any(|step| step.target == "video" && step.kind == "setpts"));
    assert!(plan
        .filter_steps
        .iter()
        .any(|step| step.target == "video" && step.kind == "overlay"));
    assert!(plan
        .filter_steps
        .iter()
        .any(|step| step.target == "audio" && step.kind == "mix"));
    assert!(plan
        .filter_steps
        .iter()
        .any(|step| step.target == "audio" && step.kind == "atempo"));
    assert!(plan
        .warnings
        .iter()
        .any(|warning| warning.contains("empty text")));
    assert!(plan
        .warnings
        .iter()
        .any(|warning| warning.contains("missing audio track path")));
}
