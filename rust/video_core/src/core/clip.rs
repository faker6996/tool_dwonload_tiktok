use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CoreClip {
    pub id: String,
    pub asset_id: String,
    pub name: String,
    pub duration: f64,
    pub start_time: f64,
    pub in_point: f64,
    pub out_point: f64,
    pub track_index: i32,
}

impl CoreClip {
    pub fn new(asset_id: String, name: String, duration: f64) -> Self {
        let normalized_duration = duration.max(0.0);

        Self {
            id: Uuid::new_v4().to_string(),
            asset_id,
            name,
            duration: normalized_duration,
            start_time: 0.0,
            in_point: 0.0,
            out_point: normalized_duration,
            track_index: 0,
        }
    }

    pub fn length(&self) -> f64 {
        Self::length_from_points(self.in_point, self.out_point)
    }

    pub fn length_from_points(in_point: f64, out_point: f64) -> f64 {
        (out_point - in_point).max(0.0)
    }

    pub fn end_time(&self) -> f64 {
        self.start_time + self.length()
    }

    pub fn set_in_point(&mut self, value: f64) {
        self.in_point = value.max(0.0).min(self.out_point).min(self.duration);
    }

    pub fn set_out_point(&mut self, value: f64) {
        self.out_point = value.max(self.in_point).min(self.duration);
    }
}
