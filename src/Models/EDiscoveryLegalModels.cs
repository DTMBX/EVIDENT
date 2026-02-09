// ============================================================================
// Evident E-Discovery Legal System - Data Models
// ============================================================================
// This file defines all data models for the legal e-discovery platform
// including Cases, Evidence, Documents, Parties, Legal Holds, and Audit Logs
// ============================================================================

using System.Text.Json.Serialization;

namespace Evident.MatterDocket.MAUI.Models;

#region ============ LEGAL CASE MANAGEMENT ============

/// <summary>
/// Legal Case/Matter - The central container for all evidence and discovery
/// </summary>
public class LegalCase
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString();
    
    [JsonPropertyName("case_number")]
    public string CaseNumber { get; set; } = string.Empty;
    
    [JsonPropertyName("case_name")]
    public string CaseName { get; set; } = string.Empty;
    
    [JsonPropertyName("description")]
    public string? Description { get; set; }
    
    [JsonPropertyName("jurisdiction")]
    public string? Jurisdiction { get; set; }
    
    [JsonPropertyName("status")] // Active, OnHold, Closed, Archived
    public string Status { get; set; } = "Active";
    
    [JsonPropertyName("case_type")] // Criminal, Civil, Insurance, Administrative, Other
    public string CaseType { get; set; } = "Civil";
    
    [JsonPropertyName("created_by")]
    public int CreatedByUserId { get; set; }
    
    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    
    [JsonPropertyName("updated_at")]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    
    [JsonPropertyName("matter_id")] // For law firm integration
    public string? MatterId { get; set; }
    
    [JsonPropertyName("is_legal_hold_active")]
    public bool IsLegalHoldActive { get; set; }
    
    [JsonPropertyName("confidentiality_level")] // Public, Confidential, Attorney-ClientPrivilege
    public string ConfidentialityLevel { get; set; } = "Confidential";
}

/// <summary>
/// Party to the litigation/matter (attorney, paralegal, party, witness, etc.)
/// </summary>
public class Party
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString();
    
    [JsonPropertyName("case_id")]
    public string CaseId { get; set; } = string.Empty;
    
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;
    
    [JsonPropertyName("party_type")] // Plaintiff, Defendant, Attorney, Witness, Investigator, Judge, Other
    public string PartyType { get; set; } = "Other";
    
    [JsonPropertyName("role")] // Attorney, Paralegal, Client, Witness, Expert, Officer, Investigator, Adjuster
    public string Role { get; set; } = "Client";
    
    [JsonPropertyName("email")]
    public string? Email { get; set; }
    
    [JsonPropertyName("phone")]
    public string? Phone { get; set; }
    
    [JsonPropertyName("organization")]
    public string? Organization { get; set; }
    
    [JsonPropertyName("permissions")] // JSON array of permission strings
    public List<string> Permissions { get; set; } = new() { "CanView" };
    
    [JsonPropertyName("active")]
    public bool IsActive { get; set; } = true;
}

#endregion

#region ============ EVIDENCE & DOCUMENT MANAGEMENT ============

/// <summary>
/// Digital Evidence - Raw media files (PDFs, videos, audio, images)
/// </summary>
public class EvidenceItem
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString();
    
    [JsonPropertyName("case_id")]
    public string CaseId { get; set; } = string.Empty;
    
    [JsonPropertyName("filename")]
    public string Filename { get; set; } = string.Empty;
    
    [JsonPropertyName("file_type")] // PDF, Video, Audio, Image, Email, Other
    public string FileType { get; set; } = string.Empty;
    
    [JsonPropertyName("file_size")]
    public long FileSize { get; set; }
    
    [JsonPropertyName("mime_type")]
    public string? MimeType { get; set; }
    
    [JsonPropertyName("uploaded_by")]
    public int UploadedByUserId { get; set; }
    
    [JsonPropertyName("uploaded_at")]
    public DateTime UploadedAt { get; set; }
    
    [JsonPropertyName("source_location")]
    public string? SourceLocation { get; set; } // Where evidence came from
    
    [JsonPropertyName("custodian")]
    public string? Custodian { get; set; } // Who had custody
    
    [JsonPropertyName("processing_status")] // Pending, Processing, Complete, Failed, Queued
    public string ProcessingStatus { get; set; } = "Pending";
    
    [JsonPropertyName("integrity_hash")] // SHA-256 forensic hash
    public string? IntegrityHash { get; set; }
    
    [JsonPropertyName("is_redacted")]
    public bool IsRedacted { get; set; }
    
    [JsonPropertyName("confidentiality_level")] // Public, Internal, Confidential, Privileged
    public string ConfidentialityLevel { get; set; } = "Confidential";
    
    [JsonPropertyName("discovery_status")] // NotResponsive, Responsive, Privileged, Withheld, Unknown
    public string DiscoveryStatus { get; set; } = "Unknown";
    
    [JsonPropertyName("document_count")] // How many documents extracted
    public int DocumentCount { get; set; }
    
    [JsonPropertyName("storage_url")]
    public string? StorageUrl { get; set; } // S3 or on-prem path
}

/// <summary>
/// Processed Document - Extracted pages, transcripts, or analysis results
/// </summary>
public class Document
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString();
    
    [JsonPropertyName("evidence_id")]
    public string EvidenceId { get; set; } = string.Empty;
    
    [JsonPropertyName("case_id")]
    public string CaseId { get; set; } = string.Empty;
    
    [JsonPropertyName("document_type")] // Page, Transcript, Redacted, Summary, Extract
    public string DocumentType { get; set; } = "Page";
    
    [JsonPropertyName("page_number")]
    public int? PageNumber { get; set; }
    
    [JsonPropertyName("extracted_text")]
    public string? ExtractedText { get; set; }
    
    [JsonPropertyName("ocr_confidence")]
    public double? OcrConfidence { get; set; } // 0.0-1.0
    
    [JsonPropertyName("review_status")] // NotReviewed, Reviewed, Flagged, Approved
    public string ReviewStatus { get; set; } = "NotReviewed";
    
    [JsonPropertyName("reviewer_id")]
    public int? ReviewerUserId { get; set; }
    
    [JsonPropertyName("review_notes")]
    public string? ReviewNotes { get; set; }
    
    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

/// <summary>
/// Privilege Assertion - Legal privilege protections
/// </summary>
public class PrivilegeAssertion
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString();
    
    [JsonPropertyName("evidence_id")]
    public string? EvidenceId { get; set; }
    
    [JsonPropertyName("document_id")]
    public string? DocumentId { get; set; }
    
    [JsonPropertyName("case_id")]
    public string CaseId { get; set; } = string.Empty;
    
    [JsonPropertyName("privilege_type")] // AttorneyClient, WorkProduct, PrivilegedDoc, Other
    public string PrivilegeType { get; set; } = "AttorneyClient";
    
    [JsonPropertyName("privilege_grounds")]
    public string? PrivilegeGrounds { get; set; }
    
    [JsonPropertyName("asserted_by")]
    public int AssertedByUserId { get; set; }
    
    [JsonPropertyName("asserted_at")]
    public DateTime AssertedAt { get; set; } = DateTime.UtcNow;
}

/// <summary>
/// Redaction - Areas of documents to hide/mask
/// </summary>
public class Redaction
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString();
    
    [JsonPropertyName("document_id")]
    public string DocumentId { get; set; } = string.Empty;
    
    [JsonPropertyName("redaction_type")] // Text, NameEntity, SensitiveInfo, Privilege, Other
    public string RedactionType { get; set; } = "Other";
    
    [JsonPropertyName("reason")]
    public string? Reason { get; set; }
    
    [JsonPropertyName("redacted_by")]
    public int RedactedByUserId { get; set; }
    
    [JsonPropertyName("redacted_at")]
    public DateTime RedactedAt { get; set; } = DateTime.UtcNow;
}

#endregion

#region ============ LEGAL HOLDS & COMPLIANCE ============

/// <summary>
/// Legal Hold - Litigation hold directive to preserve evidence
/// </summary>
public class LegalHold
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString();
    
    [JsonPropertyName("case_id")]
    public string CaseId { get; set; } = string.Empty;
    
    [JsonPropertyName("hold_name")]
    public string HoldName { get; set; } = string.Empty;
    
    [JsonPropertyName("issued_by")]
    public int IssuedByUserId { get; set; }
    
    [JsonPropertyName("issued_date")]
    public DateTime IssuedDate { get; set; } = DateTime.UtcNow;
    
    [JsonPropertyName("retention_until")]
    public DateTime? RetentionUntil { get; set; }
    
    [JsonPropertyName("status")] // Active, Modified, Lifted, Expired
    public string Status { get; set; } = "Active";
    
    [JsonPropertyName("scope")]
    public string? Scope { get; set; } // "All emails, documents, videos related to..."
    
    [JsonPropertyName("applicable_parties")] // Array of party IDs
    public List<string> ApplicablePartyIds { get; set; } = new();
    
    [JsonPropertyName("description")]
    public string? Description { get; set; }
}

/// <summary>
/// Audit Log - Chain of custody and compliance tracking
/// </summary>
public class AuditLogEntry
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString();
    
    [JsonPropertyName("case_id")]
    public string? CaseId { get; set; }
    
    [JsonPropertyName("evidence_id")]
    public string? EvidenceId { get; set; }
    
    [JsonPropertyName("document_id")]
    public string? DocumentId { get; set; }
    
    [JsonPropertyName("action")] // Upload, Access, Download, Export, Redact, Review, Produce, etc.
    public string Action { get; set; } = string.Empty;
    
    [JsonPropertyName("actor_user_id")]
    public int ActorUserId { get; set; }
    
    [JsonPropertyName("timestamp")]
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    
    [JsonPropertyName("details")]
    public string? Details { get; set; }
    
    [JsonPropertyName("ip_address")]
    public string? IpAddress { get; set; }
    
    [JsonPropertyName("legal_significance")] // Standard, ChainOfCustody, Potential, Critical
    public string LegalSignificance { get; set; } = "Standard";
}

#endregion

#region ============ PROCESSING & ANALYSIS ============

/// <summary>
/// Media Metadata extracted from evidence
/// </summary>
public class MediaMetadata
{
    [JsonPropertyName("duration")]
    public double? DurationSeconds { get; set; }
    
    [JsonPropertyName("resolution")]
    public string? Resolution { get; set; } // "1920x1080" for video
    
    [JsonPropertyName("fps")]
    public double? FramesPerSecond { get; set; }
    
    [JsonPropertyName("codec")]
    public string? VideoCodec { get; set; }
    
    [JsonPropertyName("audio_codec")]
    public string? AudioCodec { get; set; }
    
    [JsonPropertyName("creation_date")]
    public DateTime? CreationDate { get; set; }
    
    [JsonPropertyName("modified_date")]
    public DateTime? ModifiedDate { get; set; }
    
    [JsonPropertyName("people_detected")]
    public List<string>? PeopleDetected { get; set; }
    
    [JsonPropertyName("locations")]
    public List<string>? LocationsDetected { get; set; }
}

/// <summary>
/// Analysis Results from AI processing
/// </summary>
public class AnalysisResult
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString();
    
    [JsonPropertyName("evidence_id")]
    public string EvidenceId { get; set; } = string.Empty;
    
    [JsonPropertyName("status")] // Pending, Processing, Complete, Failed
    public string Status { get; set; } = "Pending";
    
    [JsonPropertyName("analysis_type")] // Transcription, OCR, PrivilegeDetection, etc.
    public string AnalysisType { get; set; } = string.Empty;
    
    [JsonPropertyName("progress")]
    public int Progress { get; set; }
    
    [JsonPropertyName("transcription")]
    public string? Transcription { get; set; }
    
    [JsonPropertyName("entities")]
    public List<EntityExtraction>? Entities { get; set; }
    
    [JsonPropertyName("timeline")]
    public List<TimelineEvent>? Timeline { get; set; }
    
    [JsonPropertyName("privilege_score")]
    public double? PrivilegeScore { get; set; } // 0.0-1.0 confidence
    
    [JsonPropertyName("responsiveness_score")]
    public double? ResponsiveScore { get; set; }
    
    [JsonPropertyName("completed_at")]
    public DateTime? CompletedAt { get; set; }
}

/// <summary>
/// Entity Extraction from documents/transcripts
/// </summary>
public class EntityExtraction
{
    [JsonPropertyName("type")] // Person, Organization, Location, Date, Amount, etc.
    public string Type { get; set; } = string.Empty;
    
    [JsonPropertyName("value")]
    public string Value { get; set; } = string.Empty;
    
    [JsonPropertyName("confidence")]
    public double Confidence { get; set; }
    
    [JsonPropertyName("context")]
    public string? Context { get; set; } // Surrounding text
}

/// <summary>
/// Timeline Event from analyzing video/audio
/// </summary>
public class TimelineEvent
{
    [JsonPropertyName("timestamp")]
    public string Timestamp { get; set; } = string.Empty;
    
    [JsonPropertyName("event")]
    public string Event { get; set; } = string.Empty;
    
    [JsonPropertyName("confidence")]
    public double Confidence { get; set; }
    
    [JsonPropertyName("type")] // Speech, Action, Location, Transition
    public string Type { get; set; } = "Action";
}

#endregion

#region ============ API REQUEST/RESPONSE MODELS ============

public class CreateCaseRequest
{
    [JsonPropertyName("case_number")]
    public string CaseNumber { get; set; } = string.Empty;
    
    [JsonPropertyName("case_name")]
    public string CaseName { get; set; } = string.Empty;
    
    [JsonPropertyName("description")]
    public string? Description { get; set; }
    
    [JsonPropertyName("jurisdiction")]
    public string? Jurisdiction { get; set; }
    
    [JsonPropertyName("case_type")]
    public string CaseType { get; set; } = "Civil";
}

public class UpdateCaseRequest
{
    [JsonPropertyName("case_name")]
    public string? CaseName { get; set; }
    
    [JsonPropertyName("description")]
    public string? Description { get; set; }
    
    [JsonPropertyName("status")]
    public string? Status { get; set; }
}

public class AddPartyRequest
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;
    
    [JsonPropertyName("party_type")]
    public string PartyType { get; set; } = string.Empty;
    
    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty;
    
    [JsonPropertyName("email")]
    public string? Email { get; set; }
    
    [JsonPropertyName("organization")]
    public string? Organization { get; set; }
}

public class IssueLegalHoldRequest
{
    [JsonPropertyName("hold_name")]
    public string HoldName { get; set; } = string.Empty;
    
    [JsonPropertyName("scope")]
    public string Scope { get; set; } = string.Empty;
    
    [JsonPropertyName("retention_until")]
    public DateTime? RetentionUntil { get; set; }
    
    [JsonPropertyName("applicable_party_ids")]
    public List<string>? ApplicablePartyIds { get; set; }
}

public class UploadEvidenceRequest
{
    [JsonPropertyName("case_id")]
    public string CaseId { get; set; } = string.Empty;
    
    [JsonPropertyName("source_location")]
    public string? SourceLocation { get; set; }
    
    [JsonPropertyName("custodian")]
    public string? Custodian { get; set; }
    
    [JsonPropertyName("confidentiality_level")]
    public string ConfidentialityLevel { get; set; } = "Confidential";
}

public class PrivilegeAssertionRequest
{
    [JsonPropertyName("privilege_type")]
    public string PrivilegeType { get; set; } = string.Empty;
    
    [JsonPropertyName("privilege_grounds")]
    public string? PrivilegeGrounds { get; set; }
}

public class CaseListResponse
{
    [JsonPropertyName("cases")]
    public List<LegalCase> Cases { get; set; } = new();
    
    [JsonPropertyName("total")]
    public int Total { get; set; }
}

public class EvidenceListResponse
{
    [JsonPropertyName("evidence")]
    public List<EvidenceItem> Evidence { get; set; } = new();
    
    [JsonPropertyName("total")]
    public int Total { get; set; }
}

public class CaseSummaryResponse
{
    [JsonPropertyName("case")]
    public LegalCase Case { get; set; } = new();
    
    [JsonPropertyName("evidence_count")]
    public int EvidenceCount { get; set; }
    
    [JsonPropertyName("document_count")]
    public int DocumentCount { get; set; }
    
    [JsonPropertyName("party_count")]
    public int PartyCount { get; set; }
    
    [JsonPropertyName("active_legal_holds")]
    public int ActiveLegalHolds { get; set; }
    
    [JsonPropertyName("storage_used_mb")]
    public long StorageUsedMB { get; set; }
}

#endregion

#region ============ BACKWARD COMPATIBILITY (Legacy Models) ============

// Keep for backward compatibility with existing code
public class Project
{
    [JsonPropertyName("id")]
    public int Id { get; set; }
    
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;
    
    [JsonPropertyName("description")]
    public string? Description { get; set; }
    
    [JsonPropertyName("custom_instructions")]
    public string? CustomInstructions { get; set; }
    
    [JsonPropertyName("model_preference")]
    public string ModelPreference { get; set; } = "gpt-4";
    
    [JsonPropertyName("max_tokens")]
    public int MaxTokens { get; set; } = 4000;
    
    [JsonPropertyName("temperature")]
    public double Temperature { get; set; } = 0.7;
    
    [JsonPropertyName("conversation_count")]
    public int ConversationCount { get; set; }
    
    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }
    
    [JsonPropertyName("updated_at")]
    public DateTime UpdatedAt { get; set; }
}

public class Evidence
{
    [JsonPropertyName("id")]
    public int Id { get; set; }
    
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;
    
    [JsonPropertyName("filename")]
    public string Filename { get; set; } = string.Empty;
    
    [JsonPropertyName("size")]
    public long Size { get; set; }
    
    [JsonPropertyName("status")]
    public string Status { get; set; } = "pending";
    
    [JsonPropertyName("uploaded_at")]
    public DateTime UploadedAt { get; set; }
}

#endregion
