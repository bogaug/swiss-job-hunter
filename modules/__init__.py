"""Swiss Job Hunter – moduli principali."""
from .scraper import search_jobs, get_job_detail, REGIONS, Job
from .ai_generator import generate_cover_letter, generate_email_subject
from .email_sender import send_email, test_email_config, preview_email
from .tracker import (
    init_db, add_application, get_applications, get_application,
    update_application_status, delete_application,
    get_stats, get_status_history, export_to_csv,
    STATUS_OPTIONS,
)

__all__ = [
    "search_jobs", "get_job_detail", "REGIONS", "Job",
    "generate_cover_letter", "generate_email_subject",
    "send_email", "test_email_config", "preview_email",
    "init_db", "add_application", "get_applications", "get_application",
    "update_application_status", "delete_application",
    "get_stats", "get_status_history", "export_to_csv",
    "STATUS_OPTIONS",
]
