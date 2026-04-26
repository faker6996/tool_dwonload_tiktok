use std::path::Path;

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportClipPlan {
    pub path: String,
    pub start: f64,
    pub in_point: f64,
    pub out_point: Option<f64>,
    pub duration: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportPlanSettings {
    pub resolution: String,
    pub fps: Value,
    pub speed: f64,
    pub gap_policy: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportStickerPlan {
    pub content: String,
    pub x: f64,
    pub y: f64,
    pub scale: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportSubtitlePlan {
    pub start_time: f64,
    pub duration: f64,
    pub text_content: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportAudioPlan {
    pub path: String,
    pub start_time: f64,
    pub duration: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportFilterPlan {
    pub has_video_speed_filter: bool,
    pub has_audio_speed_filter: bool,
    pub has_subtitles: bool,
    pub sticker_count: usize,
    pub audio_track_count: usize,
    pub needs_filter_complex: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportFilterStep {
    pub target: String,
    pub kind: String,
    pub value: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportGapPlan {
    pub start: f64,
    pub duration: f64,
    pub policy: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportPlan {
    pub clips: Vec<ExportClipPlan>,
    pub settings: ExportPlanSettings,
    pub stickers: Vec<ExportStickerPlan>,
    pub subtitles: Vec<ExportSubtitlePlan>,
    pub audio_tracks: Vec<ExportAudioPlan>,
    pub filters: ExportFilterPlan,
    pub filter_steps: Vec<ExportFilterStep>,
    pub gaps: Vec<ExportGapPlan>,
    pub total_duration: f64,
    pub warnings: Vec<String>,
}

pub fn build_export_plan(clips: &[Value], settings: &Value) -> Result<ExportPlan, String> {
    build_export_plan_with_overlays(clips, settings, &[], &[], &[])
}

pub fn build_export_plan_with_overlays(
    clips: &[Value],
    settings: &Value,
    stickers: &[Value],
    subtitles: &[Value],
    audio_tracks: &[Value],
) -> Result<ExportPlan, String> {
    let mut warnings = Vec::new();
    let mut planned_clips = clips
        .iter()
        .enumerate()
        .filter_map(|(index, clip)| plan_clip(index, clip, &mut warnings))
        .collect::<Vec<_>>();

    planned_clips.sort_by(|left, right| left.start.total_cmp(&right.start));

    if planned_clips.is_empty() {
        return Err("No valid clip files to render.".to_string());
    }

    let gap_policy = settings
        .get("gap_policy")
        .and_then(Value::as_str)
        .map(normalize_gap_policy)
        .unwrap_or_else(|| "omit".to_string());
    let gaps = plan_gaps(&planned_clips, &gap_policy, &mut warnings)?;
    let speed = read_float(
        settings
            .get("speed")
            .or_else(|| settings.get("export_speed")),
        1.0,
    )
    .filter(|value| *value > 0.0)
    .unwrap_or(1.0);

    let resolution = settings
        .get("resolution")
        .and_then(Value::as_str)
        .filter(|value| !value.trim().is_empty())
        .unwrap_or("1920x1080")
        .to_string();

    let fps = settings.get("fps").cloned().unwrap_or(Value::from(30));
    let total_duration = planned_clips.iter().map(|clip| clip.duration).sum::<f64>() / speed;
    let planned_stickers = stickers
        .iter()
        .enumerate()
        .filter_map(|(index, sticker)| plan_sticker(index, sticker, &mut warnings))
        .collect::<Vec<_>>();
    let planned_subtitles = subtitles
        .iter()
        .enumerate()
        .filter_map(|(index, subtitle)| plan_subtitle(index, subtitle, &mut warnings))
        .collect::<Vec<_>>();
    let planned_audio_tracks = audio_tracks
        .iter()
        .enumerate()
        .filter_map(|(index, audio)| plan_audio(index, audio, &mut warnings))
        .collect::<Vec<_>>();
    let wants_speed_filter = (speed - 1.0).abs() > 1e-6;
    let needs_filter_complex = wants_speed_filter
        || !planned_stickers.is_empty()
        || !planned_subtitles.is_empty()
        || !planned_audio_tracks.is_empty();
    let filter_steps = plan_filter_steps(
        wants_speed_filter,
        planned_stickers.len(),
        planned_subtitles.len(),
        planned_audio_tracks.len(),
        speed,
    );

    Ok(ExportPlan {
        clips: planned_clips,
        settings: ExportPlanSettings {
            resolution,
            fps,
            speed,
            gap_policy,
        },
        filters: ExportFilterPlan {
            has_video_speed_filter: wants_speed_filter,
            has_audio_speed_filter: wants_speed_filter,
            has_subtitles: !planned_subtitles.is_empty(),
            sticker_count: planned_stickers.len(),
            audio_track_count: planned_audio_tracks.len(),
            needs_filter_complex,
        },
        filter_steps,
        gaps,
        stickers: planned_stickers,
        subtitles: planned_subtitles,
        audio_tracks: planned_audio_tracks,
        total_duration,
        warnings,
    })
}

fn normalize_gap_policy(value: &str) -> String {
    match value.trim().to_lowercase().as_str() {
        "reject" => "reject".to_string(),
        _ => "omit".to_string(),
    }
}

fn plan_gaps(
    clips: &[ExportClipPlan],
    gap_policy: &str,
    warnings: &mut Vec<String>,
) -> Result<Vec<ExportGapPlan>, String> {
    let mut gaps = Vec::new();
    let mut cursor = 0.0;

    for clip in clips {
        if clip.start > cursor + 1e-6 {
            let duration = clip.start - cursor;
            if gap_policy == "reject" {
                return Err(format!(
                    "Timeline gap rejected: start {cursor:.6}, duration {duration:.6}."
                ));
            }
            gaps.push(ExportGapPlan {
                start: cursor,
                duration,
                policy: gap_policy.to_string(),
            });
            let display_policy = if gap_policy == "omit" {
                "omitted"
            } else {
                gap_policy
            };
            warnings.push(format!(
                "Timeline gap {display_policy}: start {cursor:.6}, duration {duration:.6}."
            ));
        }
        cursor = cursor.max(clip.start + clip.duration);
    }

    Ok(gaps)
}

fn plan_filter_steps(
    wants_speed_filter: bool,
    sticker_count: usize,
    subtitle_count: usize,
    audio_track_count: usize,
    speed: f64,
) -> Vec<ExportFilterStep> {
    let mut steps = Vec::new();

    if subtitle_count > 0 {
        steps.push(ExportFilterStep {
            target: "video".to_string(),
            kind: "subtitles".to_string(),
            value: json!({"count": subtitle_count}),
        });
    }

    if wants_speed_filter {
        steps.push(ExportFilterStep {
            target: "video".to_string(),
            kind: "setpts".to_string(),
            value: json!({"speed": speed}),
        });
    }

    if sticker_count > 0 {
        steps.push(ExportFilterStep {
            target: "video".to_string(),
            kind: "overlay".to_string(),
            value: json!({"count": sticker_count}),
        });
    }

    if audio_track_count > 0 {
        steps.push(ExportFilterStep {
            target: "audio".to_string(),
            kind: "mix".to_string(),
            value: json!({"count": audio_track_count}),
        });
    }

    if wants_speed_filter {
        steps.push(ExportFilterStep {
            target: "audio".to_string(),
            kind: "atempo".to_string(),
            value: json!({"speed": speed}),
        });
    }

    steps
}

fn plan_clip(index: usize, clip: &Value, warnings: &mut Vec<String>) -> Option<ExportClipPlan> {
    let path = clip
        .get("path")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();

    if path.is_empty() {
        warnings.push(format!("Skipping clip {index}: missing path."));
        return None;
    }

    if !Path::new(&path).exists() {
        warnings.push(format!("Skipping missing clip path: {path}"));
        return None;
    }

    let start = read_float(clip.get("start"), 0.0).unwrap_or(0.0);
    let in_point = read_float(clip.get("in_point"), 0.0)
        .unwrap_or(0.0)
        .max(0.0);
    let duration = read_float(clip.get("duration"), 0.0)
        .unwrap_or(0.0)
        .max(0.0);
    let out_point = read_out_point(clip, in_point, duration);
    let effective_duration = out_point
        .map(|value| (value - in_point).max(0.0))
        .unwrap_or(duration);

    if effective_duration <= 0.0 {
        warnings.push(format!("Skipping clip {index}: non-positive duration."));
        return None;
    }

    Some(ExportClipPlan {
        path,
        start,
        in_point,
        out_point,
        duration: effective_duration,
    })
}

fn read_out_point(clip: &Value, in_point: f64, duration: f64) -> Option<f64> {
    let Some(raw_value) = clip.get("out_point") else {
        return if duration > 0.0 {
            Some(in_point + duration)
        } else {
            None
        };
    };
    let out_point = read_float(Some(raw_value), 0.0)?;

    if raw_value.is_null() || raw_value.as_str().is_some_and(str::is_empty) || out_point == 0.0 {
        if duration > 0.0 {
            return Some(in_point + duration);
        }
        return None;
    }

    if out_point > in_point {
        Some(out_point)
    } else {
        None
    }
}

fn read_float(value: Option<&Value>, default: f64) -> Option<f64> {
    match value {
        Some(Value::Number(number)) => number.as_f64(),
        Some(Value::String(text)) => text.parse::<f64>().ok(),
        Some(Value::Null) | None => Some(default),
        _ => Some(default),
    }
}

fn plan_sticker(
    index: usize,
    sticker: &Value,
    warnings: &mut Vec<String>,
) -> Option<ExportStickerPlan> {
    let content = sticker
        .get("content")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .trim()
        .to_string();
    if content.is_empty() {
        warnings.push(format!("Skipping sticker {index}: missing content."));
        return None;
    }

    let scale = read_float(sticker.get("scale"), 1.0)
        .unwrap_or(1.0)
        .max(0.01);

    Some(ExportStickerPlan {
        content,
        x: read_float(sticker.get("x"), 0.0).unwrap_or(0.0),
        y: read_float(sticker.get("y"), 0.0).unwrap_or(0.0),
        scale,
    })
}

fn plan_subtitle(
    index: usize,
    subtitle: &Value,
    warnings: &mut Vec<String>,
) -> Option<ExportSubtitlePlan> {
    let text_content = subtitle
        .get("text_content")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .trim()
        .to_string();
    if text_content.is_empty() {
        warnings.push(format!("Skipping subtitle {index}: empty text."));
        return None;
    }

    let duration = read_float(subtitle.get("duration"), 2.0)
        .unwrap_or(2.0)
        .max(0.0);
    if duration <= 0.0 {
        warnings.push(format!("Skipping subtitle {index}: non-positive duration."));
        return None;
    }

    Some(ExportSubtitlePlan {
        start_time: read_float(subtitle.get("start_time"), 0.0)
            .unwrap_or(0.0)
            .max(0.0),
        duration,
        text_content,
    })
}

fn plan_audio(index: usize, audio: &Value, warnings: &mut Vec<String>) -> Option<ExportAudioPlan> {
    let path = audio
        .get("path")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    if path.is_empty() {
        warnings.push(format!("Skipping audio track {index}: missing path."));
        return None;
    }
    if !Path::new(&path).exists() {
        warnings.push(format!("Skipping missing audio track path: {path}"));
        return None;
    }

    Some(ExportAudioPlan {
        path,
        start_time: read_float(audio.get("start_time"), 0.0)
            .unwrap_or(0.0)
            .max(0.0),
        duration: read_float(audio.get("duration"), 0.0)
            .unwrap_or(0.0)
            .max(0.0),
    })
}
