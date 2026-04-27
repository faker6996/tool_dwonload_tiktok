use pyo3::prelude::*;

mod bindings;
pub mod core;

pub use bindings::{PyClip, PyMagneticTrack};
pub use core::{
    build_export_plan, build_export_plan_with_overlays, can_transition_queue_status,
    clamp_queue_progress, count_queue_statuses, request_queue_cancellation,
    transition_queue_status, CoreClip, CoreMagneticTrack, CoreTrack, ExportAudioPlan,
    ExportClipPlan, ExportFilterPlan, ExportFilterStep, ExportGapPlan, ExportPlan,
    ExportPlanSettings, ExportStickerPlan, ExportSubtitlePlan,
};

#[pyfunction]
fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

#[pyfunction]
fn clip_length(in_point: f64, out_point: f64) -> f64 {
    CoreClip::length_from_points(in_point, out_point)
}

#[pyfunction]
fn build_export_plan_json(clips_json: &str, settings_json: &str) -> PyResult<String> {
    let clips: Vec<serde_json::Value> = serde_json::from_str(clips_json)
        .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))?;
    let settings: serde_json::Value = serde_json::from_str(settings_json)
        .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))?;
    let plan =
        build_export_plan(&clips, &settings).map_err(pyo3::exceptions::PyValueError::new_err)?;

    serde_json::to_string(&plan)
        .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))
}

#[pyfunction]
fn build_export_plan_full_json(
    clips_json: &str,
    settings_json: &str,
    stickers_json: &str,
    subtitles_json: &str,
    audio_tracks_json: &str,
) -> PyResult<String> {
    let clips: Vec<serde_json::Value> = serde_json::from_str(clips_json)
        .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))?;
    let settings: serde_json::Value = serde_json::from_str(settings_json)
        .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))?;
    let stickers: Vec<serde_json::Value> = serde_json::from_str(stickers_json)
        .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))?;
    let subtitles: Vec<serde_json::Value> = serde_json::from_str(subtitles_json)
        .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))?;
    let audio_tracks: Vec<serde_json::Value> = serde_json::from_str(audio_tracks_json)
        .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))?;
    let plan =
        build_export_plan_with_overlays(&clips, &settings, &stickers, &subtitles, &audio_tracks)
            .map_err(pyo3::exceptions::PyValueError::new_err)?;

    serde_json::to_string(&plan)
        .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))
}

#[pyfunction]
fn queue_clamp_progress(progress: i64) -> i64 {
    clamp_queue_progress(progress)
}

#[pyfunction]
fn queue_can_transition(current_status: &str, target_status: &str) -> bool {
    can_transition_queue_status(current_status, target_status)
}

#[pyfunction]
#[pyo3(signature = (current_status, current_progress, current_error, target_status, progress = None, error = None))]
fn queue_transition_json(
    current_status: &str,
    current_progress: i64,
    current_error: Option<String>,
    target_status: &str,
    progress: Option<i64>,
    error: Option<String>,
) -> PyResult<String> {
    let result = transition_queue_status(
        current_status,
        current_progress,
        current_error,
        target_status,
        progress,
        error,
    );
    serde_json::to_string(&result)
        .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))
}

#[pyfunction]
#[pyo3(signature = (current_status, current_progress, current_error, reason = "cancelled"))]
fn queue_request_cancellation_json(
    current_status: &str,
    current_progress: i64,
    current_error: Option<String>,
    reason: &str,
) -> PyResult<String> {
    let result =
        request_queue_cancellation(current_status, current_progress, current_error, reason);
    serde_json::to_string(&result)
        .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))
}

#[pyfunction]
fn queue_status_counts_json(statuses_json: &str) -> PyResult<String> {
    let statuses: Vec<String> = serde_json::from_str(statuses_json)
        .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))?;
    let counts = count_queue_statuses(&statuses);
    serde_json::to_string(&counts)
        .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))
}

#[pymodule]
fn video_core(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PyClip>()?;
    module.add_class::<PyMagneticTrack>()?;
    module.add_function(wrap_pyfunction!(version, module)?)?;
    module.add_function(wrap_pyfunction!(clip_length, module)?)?;
    module.add_function(wrap_pyfunction!(build_export_plan_json, module)?)?;
    module.add_function(wrap_pyfunction!(build_export_plan_full_json, module)?)?;
    module.add_function(wrap_pyfunction!(queue_clamp_progress, module)?)?;
    module.add_function(wrap_pyfunction!(queue_can_transition, module)?)?;
    module.add_function(wrap_pyfunction!(queue_transition_json, module)?)?;
    module.add_function(wrap_pyfunction!(queue_request_cancellation_json, module)?)?;
    module.add_function(wrap_pyfunction!(queue_status_counts_json, module)?)?;
    Ok(())
}
