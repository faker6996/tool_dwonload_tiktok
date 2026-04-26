use pyo3::prelude::*;

use crate::core::CoreClip;

#[pyclass(name = "Clip")]
#[derive(Debug, Clone)]
pub struct PyClip {
    pub(crate) inner: CoreClip,
}

impl From<CoreClip> for PyClip {
    fn from(inner: CoreClip) -> Self {
        Self { inner }
    }
}

#[pymethods]
impl PyClip {
    #[new]
    #[pyo3(signature = (asset_id, name, duration))]
    fn py_new(asset_id: String, name: String, duration: f64) -> Self {
        Self {
            inner: CoreClip::new(asset_id, name, duration),
        }
    }

    #[getter]
    fn id(&self) -> String {
        self.inner.id.clone()
    }

    #[setter]
    fn set_id(&mut self, value: String) {
        self.inner.id = value;
    }

    #[getter]
    fn asset_id(&self) -> String {
        self.inner.asset_id.clone()
    }

    #[getter]
    fn name(&self) -> String {
        self.inner.name.clone()
    }

    #[getter]
    fn duration(&self) -> f64 {
        self.inner.duration
    }

    #[getter]
    fn start_time(&self) -> f64 {
        self.inner.start_time
    }

    #[setter]
    fn set_start_time(&mut self, value: f64) {
        self.inner.start_time = value;
    }

    #[getter]
    fn in_point(&self) -> f64 {
        self.inner.in_point
    }

    #[setter]
    fn set_in_point(&mut self, value: f64) {
        self.inner.set_in_point(value);
    }

    #[getter]
    fn out_point(&self) -> f64 {
        self.inner.out_point
    }

    #[setter]
    fn set_out_point(&mut self, value: f64) {
        self.inner.set_out_point(value);
    }

    #[getter]
    fn track_index(&self) -> i32 {
        self.inner.track_index
    }

    #[setter]
    fn set_track_index(&mut self, value: i32) {
        self.inner.track_index = value;
    }

    fn length(&self) -> f64 {
        self.inner.length()
    }

    fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(&self.inner)
            .map_err(|err| pyo3::exceptions::PyValueError::new_err(err.to_string()))
    }
}
