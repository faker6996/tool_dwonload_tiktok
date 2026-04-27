use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum QueueStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Cancelled,
}

impl QueueStatus {
    fn as_str(self) -> &'static str {
        match self {
            Self::Pending => "pending",
            Self::Running => "running",
            Self::Completed => "completed",
            Self::Failed => "failed",
            Self::Cancelled => "cancelled",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct QueueTransitionResult {
    pub ok: bool,
    pub status: String,
    pub progress: i64,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct QueueCancellationResult {
    pub ok: bool,
    pub status: String,
    pub progress: i64,
    pub error: Option<String>,
    pub cancel_requested: bool,
    pub cancel_reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct QueueStatusCounts {
    pub total: usize,
    pub pending: usize,
    pub running: usize,
    pub completed: usize,
    pub failed: usize,
    pub cancelled: usize,
}

pub fn clamp_queue_progress(progress: i64) -> i64 {
    progress.clamp(0, 100)
}

pub fn can_transition_queue_status(current: &str, target: &str) -> bool {
    let Some(current) = parse_status(current) else {
        return false;
    };
    let Some(target) = parse_status(target) else {
        return false;
    };
    can_transition(current, target)
}

pub fn transition_queue_status(
    current_status: &str,
    current_progress: i64,
    current_error: Option<String>,
    target_status: &str,
    progress: Option<i64>,
    error: Option<String>,
) -> QueueTransitionResult {
    let Some(current) = parse_status(current_status) else {
        return QueueTransitionResult {
            ok: false,
            status: current_status.to_string(),
            progress: clamp_queue_progress(current_progress),
            error: current_error,
        };
    };
    let Some(target) = parse_status(target_status) else {
        return QueueTransitionResult {
            ok: false,
            status: current.as_str().to_string(),
            progress: clamp_queue_progress(current_progress),
            error: current_error,
        };
    };

    if current == target {
        return QueueTransitionResult {
            ok: true,
            status: target.as_str().to_string(),
            progress: progress
                .map(clamp_queue_progress)
                .unwrap_or_else(|| clamp_queue_progress(current_progress)),
            error: error.or(current_error),
        };
    }

    if !can_transition(current, target) {
        return QueueTransitionResult {
            ok: false,
            status: current.as_str().to_string(),
            progress: clamp_queue_progress(current_progress),
            error: current_error,
        };
    }

    let normalized_progress = clamp_queue_progress(current_progress);
    match target {
        QueueStatus::Pending => QueueTransitionResult {
            ok: true,
            status: target.as_str().to_string(),
            progress: 0,
            error: None,
        },
        QueueStatus::Running => QueueTransitionResult {
            ok: true,
            status: target.as_str().to_string(),
            progress: progress
                .map(clamp_queue_progress)
                .unwrap_or(normalized_progress),
            error: None,
        },
        QueueStatus::Completed => QueueTransitionResult {
            ok: true,
            status: target.as_str().to_string(),
            progress: 100,
            error: None,
        },
        QueueStatus::Failed | QueueStatus::Cancelled => QueueTransitionResult {
            ok: true,
            status: target.as_str().to_string(),
            progress: normalized_progress,
            error: error.or(current_error),
        },
    }
}

pub fn request_queue_cancellation(
    current_status: &str,
    current_progress: i64,
    current_error: Option<String>,
    reason: &str,
) -> QueueCancellationResult {
    let Some(current) = parse_status(current_status) else {
        return QueueCancellationResult {
            ok: false,
            status: current_status.to_string(),
            progress: clamp_queue_progress(current_progress),
            error: current_error,
            cancel_requested: false,
            cancel_reason: String::new(),
        };
    };

    if !matches!(current, QueueStatus::Pending | QueueStatus::Running) {
        return QueueCancellationResult {
            ok: false,
            status: current.as_str().to_string(),
            progress: clamp_queue_progress(current_progress),
            error: current_error,
            cancel_requested: false,
            cancel_reason: String::new(),
        };
    }

    let reason = if reason.trim().is_empty() {
        "cancelled"
    } else {
        reason
    };
    let transition = transition_queue_status(
        current.as_str(),
        current_progress,
        current_error,
        QueueStatus::Cancelled.as_str(),
        None,
        Some(reason.to_string()),
    );

    QueueCancellationResult {
        ok: transition.ok,
        status: transition.status,
        progress: transition.progress,
        error: transition.error,
        cancel_requested: transition.ok,
        cancel_reason: if transition.ok {
            reason.to_string()
        } else {
            String::new()
        },
    }
}

pub fn count_queue_statuses(statuses: &[String]) -> QueueStatusCounts {
    let mut counts = QueueStatusCounts {
        total: statuses.len(),
        pending: 0,
        running: 0,
        completed: 0,
        failed: 0,
        cancelled: 0,
    };

    for status in statuses {
        match parse_status(status) {
            Some(QueueStatus::Pending) => counts.pending += 1,
            Some(QueueStatus::Running) => counts.running += 1,
            Some(QueueStatus::Completed) => counts.completed += 1,
            Some(QueueStatus::Failed) => counts.failed += 1,
            Some(QueueStatus::Cancelled) => counts.cancelled += 1,
            None => {}
        }
    }

    counts
}

fn parse_status(status: &str) -> Option<QueueStatus> {
    match status.trim().to_lowercase().as_str() {
        "pending" => Some(QueueStatus::Pending),
        "running" => Some(QueueStatus::Running),
        "completed" => Some(QueueStatus::Completed),
        "failed" => Some(QueueStatus::Failed),
        "cancelled" => Some(QueueStatus::Cancelled),
        _ => None,
    }
}

fn can_transition(current: QueueStatus, target: QueueStatus) -> bool {
    match current {
        QueueStatus::Pending => matches!(target, QueueStatus::Running | QueueStatus::Cancelled),
        QueueStatus::Running => matches!(
            target,
            QueueStatus::Pending
                | QueueStatus::Completed
                | QueueStatus::Failed
                | QueueStatus::Cancelled
        ),
        QueueStatus::Completed | QueueStatus::Failed | QueueStatus::Cancelled => false,
    }
}
