use video_core::{
    can_transition_queue_status, clamp_queue_progress, count_queue_statuses,
    request_queue_cancellation, transition_queue_status,
};

#[test]
fn queue_progress_is_clamped() {
    assert_eq!(clamp_queue_progress(-10), 0);
    assert_eq!(clamp_queue_progress(55), 55);
    assert_eq!(clamp_queue_progress(150), 100);
}

#[test]
fn queue_transition_rules_reject_terminal_restarts() {
    assert!(can_transition_queue_status("pending", "running"));
    assert!(!can_transition_queue_status("completed", "running"));

    let result = transition_queue_status("completed", 100, None, "running", None, None);

    assert!(!result.ok);
    assert_eq!(result.status, "completed");
    assert_eq!(result.progress, 100);
}

#[test]
fn queue_transitions_apply_progress_and_errors() {
    let running = transition_queue_status("pending", 0, None, "running", Some(150), None);
    assert!(running.ok);
    assert_eq!(running.status, "running");
    assert_eq!(running.progress, 100);

    let failed = transition_queue_status(
        "running",
        70,
        None,
        "failed",
        None,
        Some("boom".to_string()),
    );
    assert!(failed.ok);
    assert_eq!(failed.status, "failed");
    assert_eq!(failed.progress, 70);
    assert_eq!(failed.error.as_deref(), Some("boom"));
}

#[test]
fn queue_cancellation_marks_pending_or_running_only() {
    let running = request_queue_cancellation("running", 30, None, "user");
    assert!(running.ok);
    assert_eq!(running.status, "cancelled");
    assert!(running.cancel_requested);
    assert_eq!(running.cancel_reason, "user");

    let completed = request_queue_cancellation("completed", 100, None, "user");
    assert!(!completed.ok);
    assert!(!completed.cancel_requested);
}

#[test]
fn queue_status_counts_include_cancelled() {
    let statuses = vec![
        "pending".to_string(),
        "running".to_string(),
        "completed".to_string(),
        "failed".to_string(),
        "cancelled".to_string(),
        "unknown".to_string(),
    ];

    let counts = count_queue_statuses(&statuses);

    assert_eq!(counts.total, 6);
    assert_eq!(counts.pending, 1);
    assert_eq!(counts.running, 1);
    assert_eq!(counts.completed, 1);
    assert_eq!(counts.failed, 1);
    assert_eq!(counts.cancelled, 1);
}
