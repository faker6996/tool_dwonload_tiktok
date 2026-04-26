use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::CoreClip;

const EPSILON: f64 = 1e-9;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CoreTrack {
    pub name: String,
    pub is_audio: bool,
    pub clips: Vec<CoreClip>,
    pub is_muted: bool,
    pub is_locked: bool,
    pub is_hidden: bool,
}

impl CoreTrack {
    pub fn new(name: String, is_audio: bool) -> Self {
        Self {
            name,
            is_audio,
            clips: Vec::new(),
            is_muted: false,
            is_locked: false,
            is_hidden: false,
        }
    }

    pub fn add_clip(&mut self, mut clip: CoreClip, position: Option<f64>) -> bool {
        if self.is_locked {
            return false;
        }

        clip.start_time = match position {
            Some(value) => value,
            None => self.clips.last().map_or(0.0, CoreClip::end_time),
        };

        self.clips.push(clip);
        self.sort_clips();
        true
    }

    pub fn remove_clip(&mut self, clip_id: &str) -> Option<CoreClip> {
        if self.is_locked {
            return None;
        }

        let index = self.get_clip_index(clip_id)?;
        Some(self.clips.remove(index))
    }

    pub fn get_clip_index(&self, clip_id: &str) -> Option<usize> {
        self.clips.iter().position(|clip| clip.id == clip_id)
    }

    pub fn validate_no_overlaps(&self) -> bool {
        self.clips.windows(2).all(|pair| {
            let previous = &pair[0];
            let next = &pair[1];
            previous.end_time() <= next.start_time + EPSILON
        })
    }

    fn sort_clips(&mut self) {
        self.clips
            .sort_by(|left, right| left.start_time.total_cmp(&right.start_time));
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CoreMagneticTrack {
    pub track: CoreTrack,
}

impl CoreMagneticTrack {
    pub fn new(name: String) -> Self {
        Self {
            track: CoreTrack::new(name, false),
        }
    }

    pub fn add_clip(&mut self, clip: CoreClip, position: Option<f64>) -> bool {
        if self.track.is_locked {
            return false;
        }

        if position.is_none() || self.track.clips.is_empty() {
            return self.track.add_clip(clip, None);
        }

        let position = position.unwrap_or(0.0);
        let mut insert_index = 0;
        for (index, existing) in self.track.clips.iter().enumerate() {
            if existing.start_time > position {
                insert_index = index;
                break;
            }
            insert_index = index + 1;
        }

        let shift_amount = clip.length();
        for existing in self.track.clips.iter_mut().skip(insert_index) {
            existing.start_time += shift_amount;
        }

        let mut inserted_clip = clip;
        inserted_clip.start_time = position;
        if insert_index > 0 {
            let previous = &self.track.clips[insert_index - 1];
            inserted_clip.start_time = previous.end_time();
        }

        self.track.clips.insert(insert_index, inserted_clip);
        true
    }

    pub fn remove_clip(&mut self, clip_id: &str) -> Option<CoreClip> {
        if self.track.is_locked {
            return None;
        }

        let remove_index = self.track.get_clip_index(clip_id)?;
        let removed_clip = self.track.clips.remove(remove_index);
        let shift_amount = removed_clip.length();

        for clip in self.track.clips.iter_mut().skip(remove_index) {
            clip.start_time -= shift_amount;
        }

        Some(removed_clip)
    }

    pub fn split_clip(&mut self, clip_id: &str, timeline_time: f64) -> Option<CoreClip> {
        if self.track.is_locked {
            return None;
        }

        let clip_index = self.track.get_clip_index(clip_id)?;
        let clip = &self.track.clips[clip_index];
        let clip_start = clip.start_time;
        let clip_end = clip.end_time();

        if timeline_time <= clip_start || timeline_time >= clip_end {
            return None;
        }

        let media_split_point = clip.in_point + (timeline_time - clip_start);
        if media_split_point <= clip.in_point || media_split_point >= clip.out_point {
            return None;
        }

        let mut right_clip = self.track.clips[clip_index].clone();
        right_clip.id = Uuid::new_v4().to_string();
        right_clip.start_time = timeline_time;
        right_clip.in_point = media_split_point;

        self.track.clips[clip_index].out_point = media_split_point;
        self.track.clips.insert(clip_index + 1, right_clip.clone());
        Some(right_clip)
    }

    pub fn trim_clip(
        &mut self,
        clip_id: &str,
        new_in_point: Option<f64>,
        new_out_point: Option<f64>,
    ) -> bool {
        if self.track.is_locked {
            return false;
        }

        let Some(clip_index) = self.track.get_clip_index(clip_id) else {
            return false;
        };

        let current_in = self.track.clips[clip_index].in_point;
        let current_out = self.track.clips[clip_index].out_point;
        let duration = self.track.clips[clip_index].duration;

        let target_in = new_in_point.unwrap_or(current_in).max(0.0).min(duration);
        let target_out = new_out_point.unwrap_or(current_out).max(0.0).min(duration);

        if target_out <= target_in {
            return false;
        }

        let old_length = self.track.clips[clip_index].length();
        self.track.clips[clip_index].in_point = target_in;
        self.track.clips[clip_index].out_point = target_out;
        let length_delta = self.track.clips[clip_index].length() - old_length;

        if length_delta.abs() > EPSILON {
            for clip in self.track.clips.iter_mut().skip(clip_index + 1) {
                clip.start_time += length_delta;
            }
        }

        true
    }

    pub fn validate_no_overlaps(&self) -> bool {
        self.track.validate_no_overlaps()
    }
}
