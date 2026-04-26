use pyo3::prelude::*;
use pyo3::PyRef;

use crate::bindings::PyClip;
use crate::core::CoreMagneticTrack;

#[pyclass(name = "MagneticTrack")]
#[derive(Debug, Clone)]
pub struct PyMagneticTrack {
    inner: CoreMagneticTrack,
}

#[pymethods]
impl PyMagneticTrack {
    #[new]
    #[pyo3(signature = (name = "Main Track".to_string()))]
    fn py_new(name: String) -> Self {
        Self {
            inner: CoreMagneticTrack::new(name),
        }
    }

    #[getter]
    fn name(&self) -> String {
        self.inner.track.name.clone()
    }

    #[getter]
    fn is_locked(&self) -> bool {
        self.inner.track.is_locked
    }

    #[setter]
    fn set_is_locked(&mut self, value: bool) {
        self.inner.track.is_locked = value;
    }

    #[getter]
    fn clips(&self) -> Vec<PyClip> {
        self.inner
            .track
            .clips
            .iter()
            .cloned()
            .map(PyClip::from)
            .collect()
    }

    #[pyo3(signature = (clip, position = None))]
    fn add_clip(&mut self, clip: &PyClip, position: Option<f64>) -> bool {
        self.inner.add_clip(clip.inner.clone(), position)
    }

    fn load_clips(&mut self, clips: Vec<PyRef<'_, PyClip>>) {
        self.inner.track.clips = clips.into_iter().map(|clip| clip.inner.clone()).collect();
    }

    fn remove_clip(&mut self, clip_id: String) -> Option<PyClip> {
        self.inner.remove_clip(&clip_id).map(PyClip::from)
    }

    fn split_clip(&mut self, clip_id: String, timeline_time: f64) -> Option<PyClip> {
        self.inner
            .split_clip(&clip_id, timeline_time)
            .map(PyClip::from)
    }

    #[pyo3(signature = (clip_id, new_in_point = None, new_out_point = None))]
    fn trim_clip(
        &mut self,
        clip_id: String,
        new_in_point: Option<f64>,
        new_out_point: Option<f64>,
    ) -> bool {
        self.inner.trim_clip(&clip_id, new_in_point, new_out_point)
    }

    fn validate_no_overlaps(&self) -> bool {
        self.inner.validate_no_overlaps()
    }

    fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(&self.inner)
            .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))
    }
}
